"""
FROZEN LAKE – Streamlit + clipspy 
Instalare:  python -m pip install streamlit clipspy pandas
Rulare:     python -m streamlit run frozen_lake_app.py

"""

import streamlit as st
import clips
import os
import random


#  Cale fisier .clp


CLP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frozen_lake.clp")


#  Generare Harta Dinamica


def genereaza_harta_aleatoare(size, prob_gropi, is_slippery=False):
    cells = {(0, 0): "start", (size-1, size-1): "obiectiv"}
    facts = [
        "(mediu alunecos)" if is_slippery else "(mediu determinist)",
        f"(dimensiune-harta {size} {size})",
        "(pozitie-agent 0 0)",
        "(tip-celula 0 0 start)",
        f"(tip-celula {size-1} {size-1} obiectiv)"
    ]
    
    all_pos = [(r, c) for r in range(size) for c in range(size)]
    all_pos.remove((0, 0))
    all_pos.remove((size-1, size-1))
    
    # Generare aleatoare gropi
    for r, c in all_pos:
        if random.randint(1, 100) <= prob_gropi:
            cells[(r, c)] = "groapa"
            facts.append(f"(tip-celula {r} {c} groapa)")
            
    facts.extend([
        "(scop calculeaza-distante)",
        "(scop deplasare)"
    ])
    
    return cells, facts


#  Citire stare din mediul CLIPS


def read_state(env):
    pos = None
    distante = {}
    oprire = False

    for fact in env.facts():
        try:
            tname = fact.template.name
        except Exception:
            continue

        if tname == "pozitie-agent":
            try:
                pos = (int(fact[0]), int(fact[1]))
            except Exception:
                pass
        elif tname == "distanta":
            try:
                distante[(int(fact[0]), int(fact[1]))] = int(fact[2])
            except Exception:
                pass
        elif tname == "scop":
            try:
                if str(fact[0]) == "oprire":
                    oprire = True
            except Exception:
                pass

    return pos, distante, oprire



#  Motor CLIPS – episod complet, snapshot la fiecare mutare


def apply_slip(pos, direction, size, cell_types):
    r, c = pos
    if direction == "right" or direction == "left":
        candidates = [(r - 1, c), (r + 1, c)]
    else:
        candidates = [(r, c - 1), (r, c + 1)]
    valid = [(nr, nc) for nr, nc in candidates if 0 <= nr < size and 0 <= nc < size]
    if not valid:
        return pos
    return random.choice(valid)


def run_clips_episode(initial_facts, size, cell_types):
    env = clips.Environment()
    env.load(CLP_FILE)

    for f in initial_facts:
        env.assert_string(f)

    is_slippery = any("alunecos" in f for f in initial_facts)

    snapshots = []

    pos, distante, oprire = read_state(env)
    snapshots.append({
        "pozitie":  pos or (0, 0),
        "distante": distante.copy(),
        "mesaj":    "Start: agent la (0,0)",
        "rezultat": None,
        "directie": "right",
    })

    prev_pos = pos or (0, 0)

    for _ in range(1000):
        fired = env.run(1)
        if fired == 0:
            break

        pos, distante, oprire = read_state(env)

        if pos and pos != prev_pos:
            r1, c1 = prev_pos
            r2, c2 = pos
            if c2 > c1: dir_ = "right"; msg = "→ Dreapta"
            elif c2 < c1: dir_ = "left"; msg = "← Stanga"
            elif r2 > r1: dir_ = "down"; msg = "↓ Jos"
            else: dir_ = "up"; msg = "↑ Sus"

            snapshots.append({
                "pozitie":  pos,
                "distante": distante.copy() if distante else snapshots[-1]["distante"],
                "mesaj":    msg,
                "rezultat": None,
                "directie": "right" if dir_ in ("right", "down") else "left",
            })
            prev_pos = pos

            if is_slippery and random.random() < 0.6:
                slipped_pos = apply_slip(pos, dir_, size, cell_types)
                if slipped_pos != pos:
                    for fact in env.facts():
                        try:
                            if fact.template.name == "pozitie-agent":
                                fact.retract()
                                break
                        except Exception:
                            pass
                    env.assert_string(f"(pozitie-agent {slipped_pos[0]} {slipped_pos[1]})")
                    sr, sc = slipped_pos
                    pr, pc = pos
                    if sc > pc: slip_msg = "↠ Alunecare Dreapta"; slip_dir = "right"
                    elif sc < pc: slip_msg = "↞ Alunecare Stanga"; slip_dir = "left"
                    elif sr > pr: slip_msg = "↡ Alunecare Jos"; slip_dir = "right"
                    else: slip_msg = "↟ Alunecare Sus"; slip_dir = "right"

                    slip_rez = None
                    slip_final_msg = slip_msg
                    if cell_types.get(slipped_pos) == "groapa":
                        slip_rez = "esec"
                        slip_final_msg = slip_msg + " — 💀 Groapa! Esec."
                        for fact in env.facts():
                            try:
                                if fact.template.name == "scop":
                                    fact.retract()
                            except Exception:
                                pass
                        env.assert_string("(scop oprire)")
                    elif slipped_pos == (size-1, size-1):
                        slip_rez = "succes"
                        slip_final_msg = slip_msg + " — 🏆 Obiectiv atins!"

                    snapshots.append({
                        "pozitie":  slipped_pos,
                        "distante": distante.copy() if distante else snapshots[-1]["distante"],
                        "mesaj":    slip_final_msg,
                        "rezultat": slip_rez,
                        "directie": slip_dir,
                    })
                    prev_pos = slipped_pos
                    pos = slipped_pos
                    if slip_rez in ("esec", "succes"):
                        break

        pos, distante, oprire = read_state(env)

        if oprire:
            rez = "fara-drum"
            if pos == (size-1, size-1): rez = "succes"
            elif cell_types.get(pos) == "groapa": rez = "esec"

            msg = {"succes": "🏆 Obiectiv atins! Succes.",
                   "esec": "💀 Groapa! Esec.",
                   "fara-drum": "🚫 Nu exista drum."}[rez]

            snapshots.append({
                "pozitie":  pos or prev_pos,
                "distante": distante.copy() if distante else snapshots[-1]["distante"],
                "mesaj":    msg,
                "rezultat": rez,
                "directie": snapshots[-1].get("directie", "right"),
            })
            break

    last_dist = {}
    for s in snapshots:
        if s["distante"]:
            last_dist = s["distante"]
        elif last_dist:
            s["distante"] = last_dist

    env.clear() 
    return snapshots



#  SVG renderer


def render_svg(ar, ac, distante, trail, status, facing, steps, size, cell_types):
    CELL_SZ = 100
    PAD, GAP = 16, 6
    SVG_W = SVG_H = PAD*2 + size*CELL_SZ + (size-1)*GAP

    is_walking = status == "running" and steps > 0
    is_dead    = status == "failure" and cell_types.get((ar, ac), "ice") == "groapa"
    is_success = status == "success"

    def cell_xy(r, c):
        return PAD + c*(CELL_SZ+GAP), PAD + r*(CELL_SZ+GAP)

    def center_xy(r, c):
        x, y = cell_xy(r, c)
        return x + CELL_SZ//2, y + CELL_SZ//2

    p = []
    # Folosim width="100%" și max-width pentru ca hărțile mari (8x8) să nu iasă din ecran
    p.append(f"""<svg xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 {SVG_W} {SVG_H}" width="100%" style="max-width: {SVG_W}px; display:block; margin:auto; border-radius:18px;
         background:linear-gradient(160deg,#060e1f,#091524);
         box-shadow:0 0 60px #38bdf815,0 4px 24px #00000080;">
<defs>
  <filter id="gb"><feGaussianBlur stdDeviation="3" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="gg"><feGaussianBlur stdDeviation="5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <radialGradient id="g-ice"      cx="35%" cy="30%">
    <stop offset="0%"   stop-color="#1e3a5f" stop-opacity="0.85"/>
    <stop offset="100%" stop-color="#071120" stop-opacity="0.9"/></radialGradient>
  <radialGradient id="g-start"    cx="35%" cy="30%">
    <stop offset="0%"   stop-color="#166534" stop-opacity="0.9"/>
    <stop offset="100%" stop-color="#052e16" stop-opacity="0.95"/></radialGradient>
  <radialGradient id="g-groapa"   cx="50%" cy="40%">
    <stop offset="0%"   stop-color="#3b0000"/>
    <stop offset="100%" stop-color="#150000"/></radialGradient>
  <radialGradient id="g-obiectiv" cx="40%" cy="25%">
    <stop offset="0%"   stop-color="#92400e"/>
    <stop offset="100%" stop-color="#3b1a00"/></radialGradient>
  <style>
    @keyframes bob  {{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-4px)}}}}
    @keyframes fall {{0%{{transform:rotate(0deg)scale(1);opacity:1}}100%{{transform:rotate(80deg)scale(.5);opacity:.1}}}}
    @keyframes wlL  {{0%,100%{{transform:rotate(-14deg)}}50%{{transform:rotate(14deg)}}}}
    @keyframes wlR  {{0%,100%{{transform:rotate(14deg)}} 50%{{transform:rotate(-14deg)}}}}
    @keyframes waL  {{0%,100%{{transform:rotate(-10deg)}}50%{{transform:rotate(10deg)}}}}
    @keyframes waR  {{0%,100%{{transform:rotate(10deg)}} 50%{{transform:rotate(-10deg)}}}}
    @keyframes pg   {{0%,100%{{opacity:.6}}50%{{opacity:1}}}}
    @keyframes sp   {{0%,100%{{opacity:0;transform:scale(.5)}}50%{{opacity:1;transform:scale(1.2)}}}}
    @keyframes snow {{0%{{transform:translateY(-5px);opacity:0}}80%{{opacity:.5}}100%{{transform:translateY(8px);opacity:0}}}}
  </style>
</defs>""")

    for r in range(size):
        for c in range(size):
            cx, cy = cell_xy(r, c)
            ctype  = cell_types.get((r, c), "ice")
            is_ag  = (r, c) == (ar, ac)
            grad   = {"ice":"g-ice","start":"g-start","groapa":"g-groapa","obiectiv":"g-obiectiv"}[ctype]
            stroke = "#38bdf8cc" if is_ag else {"ice":"#7dd3fc18","start":"#4ade8044","groapa":"#dc262644","obiectiv":"#fbbf2466"}[ctype]
            sw     = "2.5" if is_ag else "1.5"
            flt    = 'filter="url(#gb)"' if is_ag else ""
            p.append(f'<rect x="{cx}" y="{cy}" width="{CELL_SZ}" height="{CELL_SZ}" rx="13" fill="url(#{grad})" stroke="{stroke}" stroke-width="{sw}" {flt}/>')

            if ctype == "ice":
                p.append(f'<line x1="{cx+14}" y1="{cy+12}" x2="{cx+32}" y2="{cy+12}" stroke="#ffffff12" stroke-width="1"/>'
                         f'<line x1="{cx+60}" y1="{cy+18}" x2="{cx+80}" y2="{cy+18}" stroke="#ffffff0a" stroke-width="1"/>')

            icx, icy = center_xy(r, c)
            if (r, c) in trail and not is_ag:
                p.append(f'<circle cx="{icx-8}" cy="{icy+22}" r="3" fill="#38bdf830"/>'
                         f'<circle cx="{icx+8}" cy="{icy+26}" r="3" fill="#38bdf830"/>')

            if ctype == "groapa" and not is_ag:
                p.append(f'<ellipse cx="{icx}" cy="{icy+10}" rx="26" ry="16" fill="#0d0000" stroke="#7f1d1d44" stroke-width="1"/>'
                         f'<line x1="{icx-10}" y1="{icy-8}" x2="{icx-2}" y2="{icy+6}" stroke="#dc2626" stroke-width="2" stroke-linecap="round"/>'
                         f'<line x1="{icx+8}" y1="{icy-10}" x2="{icx+2}" y2="{icy+4}" stroke="#dc2626" stroke-width="1.5" stroke-linecap="round"/>'
                         f'<text x="{icx}" y="{icy-16}" text-anchor="middle" font-size="20" fill="#ef4444" opacity="0.9">⚠</text>')
            elif ctype == "start" and not is_ag:
                p.append(f'<text x="{icx}" y="{icy-16}" text-anchor="middle" font-size="11" fill="#4ade8088" font-family="Share Tech Mono,monospace">START</text>'
                         f'<circle cx="{icx}" cy="{icy+8}" r="12" fill="none" stroke="#4ade8044" stroke-width="2" stroke-dasharray="4,3"/>')
            elif ctype == "obiectiv":
                p.append(f'<circle cx="{icx}" cy="{icy+6}" r="12" fill="#fbbf2440" filter="url(#gg)">'
                         f'<animate attributeName="r" values="12;20;12" dur="2s" repeatCount="indefinite"/>'
                         f'<animate attributeName="opacity" values=".7;.2;.7" dur="2s" repeatCount="indefinite"/></circle>'
                         f'<text x="{icx}" y="{icy+14}" text-anchor="middle" font-size="36" filter="url(#gg)">🏆</text>')

            p.append(f'<text x="{cx+CELL_SZ-5}" y="{cy+CELL_SZ-5}" text-anchor="end" font-family="Share Tech Mono,monospace" font-size="9" fill="#33415540">({r},{c})</text>')
            dv = distante.get((r, c))
            if dv is not None and ctype != "groapa":
                p.append(f'<text x="{cx+7}" y="{cy+15}" font-family="Share Tech Mono,monospace" font-size="11" fill="#7dd3fc66">{dv}</text>')

    # traseu
    full = trail + [(ar, ac)]
    for i in range(len(full) - 1):
        r1, c1 = full[i]
        r2, c2 = full[i+1]
        if abs(r2-r1) + abs(c2-c1) == 1:
            x1, y1 = center_xy(r1, c1)
            x2, y2 = center_xy(r2, c2)
            p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#38bdf840" stroke-width="3" stroke-dasharray="6,4"/>')

    # personaj
    ax, ay = center_xy(ar, ac)
    flip   = -1 if facing == "left" else 1
    body_a = ""
    
    if is_dead:
        body_a = 'style="transform-origin:0px 0px;animation:fall .9s ease-in forwards;"'
    elif is_success:
        body_a = 'style="transform-origin:0px -12px;animation:bob .55s ease-in-out infinite;"'
        
    ll = 'style="transform-origin:-5px 16px;animation:wlL .45s ease-in-out infinite;"' if is_walking else ""
    rl = 'style="transform-origin:5px 16px;animation:wlR .45s ease-in-out infinite;"' if is_walking else ""
    la = 'style="transform-origin:-13px 2px;animation:waL .45s ease-in-out infinite;"' if is_walking else ""
    ra = 'style="transform-origin:13px 2px;animation:waR .45s ease-in-out infinite;"' if is_walking else ""

    p.append(f'<g transform="translate({ax},{ay}) scale({flip},1)">')
    p.append(f'<g {body_a}>')
    
    p.append('<ellipse cx="0" cy="30" rx="20" ry="5" fill="#000" opacity="0.25"/>')
    p.append('<path d="M -9,-6 Q -22,-2 -20,7 Q -16,14 -8,12" fill="none" stroke="#f87171" stroke-width="3.5" stroke-linecap="round"/>')
    p.append('<circle cx="-20" cy="7" r="4" fill="#f87171" opacity=".8"/>')
    p.append('<rect x="-13" y="-4" width="26" height="24" rx="9" fill="#1d4ed8" stroke="#3b82f6" stroke-width="1.2"/>')
    p.append('<rect x="-2" y="-4" width="4" height="24" rx="2" fill="#1e40af" opacity=".8"/>')
    p.append('<rect x="-12" y="10" width="7" height="5" rx="2" fill="#1e40af" stroke="#3b82f666" stroke-width="1"/>')
    p.append('<rect x="5"   y="10" width="7" height="5" rx="2" fill="#1e40af" stroke="#3b82f666" stroke-width="1"/>')
    p.append('<path d="M -14,-5 Q -16,-22 0,-24 Q 16,-22 14,-5 Z" fill="#1e40af" stroke="#3b82f6" stroke-width="1"/>')
    p.append('<ellipse cx="0" cy="-12" rx="10" ry="9" fill="#fde68a"/>')
    p.append('<ellipse cx="-6" cy="-9" rx="3" ry="2" fill="#fca5a5" opacity=".5"/>')
    p.append('<ellipse cx="6"  cy="-9" rx="3" ry="2" fill="#fca5a5" opacity=".5"/>')
    
    if is_dead:
        p.append('<text x="-4.5" y="-8" font-size="7" text-anchor="middle" fill="#1c1917" font-weight="bold">x</text>'
                 '<text x="4.5"  y="-8" font-size="7" text-anchor="middle" fill="#1c1917" font-weight="bold">x</text>')
    elif is_success:
        p.append('<path d="M -6,-14 Q -4,-11 -2,-14" fill="none" stroke="#1c1917" stroke-width="1.5" stroke-linecap="round"/>'
                 '<path d="M 2,-14 Q 4,-11 6,-14" fill="none" stroke="#1c1917" stroke-width="1.5" stroke-linecap="round"/>'
                 '<path d="M -5,-7 Q 0,-4 5,-7" fill="none" stroke="#92400e" stroke-width="1.5" stroke-linecap="round"/>')
    else:
        p.append('<ellipse cx="-4" cy="-13" rx="2" ry="2.5" fill="#1c1917"/>'
                 '<ellipse cx="4"  cy="-13" rx="2" ry="2.5" fill="#1c1917"/>'
                 '<ellipse cx="-3.2" cy="-14" rx=".7" ry=".7" fill="#ffffffaa"/>'
                 '<ellipse cx="4.8"  cy="-14" rx=".7" ry=".7" fill="#ffffffaa"/>')
        if is_walking:
            p.append('<path d="M -3,-8 Q 0,-7 3,-8" fill="none" stroke="#92400e" stroke-width="1" stroke-linecap="round"/>')
            
    p.append('<path d="M -12,-20 Q -9,-36 0,-38 Q 9,-36 12,-20 Z" fill="#ef4444" stroke="#dc2626" stroke-width="1"/>'
             '<ellipse cx="0" cy="-20" rx="13" ry="4.5" fill="#fca5a5"/>'
             '<line x1="-9" y1="-26" x2="9" y2="-26" stroke="#dc2626" stroke-width="1.5"/>'
             '<circle cx="0" cy="-38" r="4.5" fill="#fca5a5"/>')
             
    p.append(f'<g {la}><line x1="-13" y1="3" x2="-26" y2="14" stroke="#1d4ed8" stroke-width="5.5" stroke-linecap="round"/>'
             '<ellipse cx="-26" cy="14" rx="5" ry="4" fill="#ef4444" opacity=".9"/></g>')
    p.append(f'<g {ra}><line x1="13" y1="3" x2="26" y2="14" stroke="#1d4ed8" stroke-width="5.5" stroke-linecap="round"/>'
             '<ellipse cx="26" cy="14" rx="5" ry="4" fill="#ef4444" opacity=".9"/></g>')
             
    p.append('<rect x="-11" y="18" width="10" height="14" rx="4" fill="#1e3a5f"/>'
             '<rect x="1"   y="18" width="10" height="14" rx="4" fill="#1e3a5f"/>')
             
    p.append(f'<g {ll}><rect x="-11" y="30" width="10" height="7" rx="3.5" fill="#374151"/></g>')
    p.append(f'<g {rl}><rect x="1" y="30" width="10" height="7" rx="3.5" fill="#374151"/></g>')
    
    if is_success:
        for sx, sy, sd in [(-30,-22,"0s"),(-38,-6,".3s"),(-22,-38,".6s"),(30,-24,".15s"),(40,-4,".45s")]:
            p.append(f'<text x="{sx}" y="{sy}" font-size="14" fill="#fbbf24" style="animation:sp 1s {sd} ease-in-out infinite;">✦</text>')
    if is_dead:
        for ix, iy, ia in [(-18,-8,0),(-24,2,.1),(18,-6,.05),(26,4,.15)]:
            p.append(f'<circle cx="{ix}" cy="{iy}" r="5" fill="#ef444466" style="animation:sp .6s {ia}s ease-out forwards;"/>')
            
    p.append('</g></g>')

    for i, (fx, fy) in enumerate([(45,25),(130,10),(250,40),(340,15),(380,55),(80,70),(190,5),(310,30),(430,8)]):
        p.append(f'<text x="{fx}" y="{fy}" font-size="10" fill="#7dd3fc25" style="animation:snow 3s {i*0.4:.1f}s ease-in-out infinite;">❄</text>')

    p.append('</svg>')
    return "\n".join(p)



#  STREAMLIT UI


st.set_page_config(page_title="Frozen Lake – CLIPS", page_icon="🧊", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;600;800&display=swap');
html,body,[data-testid="stAppViewContainer"]{background:#060d1a;color:#e8f4fd;font-family:'Exo 2',sans-serif;}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 20% 10%,#0d2137 0%,#060d1a 65%);}
h1{font-family:'Exo 2',sans-serif;font-weight:800;letter-spacing:3px;color:#7dd3fc;text-shadow:0 0 30px #38bdf870;margin-bottom:0;}
h3{font-family:'Share Tech Mono',monospace;color:#475569;font-size:.8rem;letter-spacing:2px;margin-top:4px;}
.stButton>button{background:linear-gradient(135deg,#1e3a5f,#0f2440);color:#7dd3fc;border:1px solid #2563eb44;
  border-radius:8px;font-family:'Share Tech Mono',monospace;font-size:.9rem;letter-spacing:1px;padding:.45rem 1.2rem;transition:all .2s;}
.stButton>button:hover{background:linear-gradient(135deg,#1d4ed8,#1e3a8a);box-shadow:0 0 18px #3b82f650;transform:translateY(-1px);}
.badge{display:inline-block;padding:4px 14px;border-radius:20px;font-family:'Share Tech Mono',monospace;font-size:.78rem;letter-spacing:1px;margin-bottom:8px;}
.badge-running{background:#1e3a5f;color:#7dd3fc;border:1px solid #38bdf855;}
.badge-success{background:#14532d;color:#4ade80;border:1px solid #4ade8055;}
.badge-failure{background:#1c0a0a;color:#f87171;border:1px solid #ef444455;}
.badge-ready  {background:#1c1c2e;color:#94a3b8;border:1px solid #334155;}
.stat-chip{display:inline-block;background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:5px 12px;
  font-family:'Share Tech Mono',monospace;font-size:.78rem;color:#94a3b8;margin-right:6px;margin-bottom:6px;}
.stat-chip span{color:#7dd3fc;font-weight:bold;}
.log-box{background:#03080f;border:1px solid #1e3a5f;border-radius:10px;padding:12px 16px;
  font-family:'Share Tech Mono',monospace;font-size:.8rem;color:#7dd3fc;max-height:200px;overflow-y:auto;line-height:1.8;}
.log-success{color:#4ade80;} .log-error{color:#f87171;} .log-move{color:#93c5fd;}
.clips-badge{display:inline-block;background:#0d1f0d;border:1px solid #4ade8033;border-radius:6px;
  padding:2px 10px;font-family:'Share Tech Mono',monospace;font-size:.7rem;color:#4ade8099;margin-left:8px;vertical-align:middle;}
</style>
""", unsafe_allow_html=True)


#  MENIU LATERAL (Setari Harta)

st.sidebar.header("⚙️ Setări Hartă")
selected_size = st.sidebar.selectbox("Dimensiune Hartă", [3, 4, 5, 6, 8], index=1)
prob_gropi = st.sidebar.slider("Probabilitate Gropi (%)", 0, 50, 20)

gen_btn = st.sidebar.button("🎲 Generează Hartă Nouă", use_container_width=True)
is_slippery = st.sidebar.toggle("🧊 Mediu alunecos ", value=False)

# Initializare Session State pentru Harta
if "map_size" not in st.session_state or gen_btn:
    cells, facts = genereaza_harta_aleatoare(selected_size, prob_gropi, is_slippery)
    st.session_state.map_size = selected_size
    st.session_state.cell_types = cells
    st.session_state.initial_facts = facts
    
    # Resetează simularea curenta daca generam harta noua
    st.session_state.snapshots = []
    st.session_state.snap_idx = 0
    st.session_state.status = "ready"
    st.session_state.trail = []
    st.session_state.facing = "right"
    st.session_state.clips_ran = False
    st.session_state.log = ["🧊 Hartă nouă generată. Apasă <strong>▶ Rulează CLIPS</strong>."]

# Restul variabilelor de stare
for k, v in [("snapshots",[]),("snap_idx",0),("status","ready"),
              ("trail",[]),("facing","right"),("clips_ran",False),
              ("log",["🧊 Apasa <strong>▶ Ruleaza CLIPS</strong> pentru a porni motorul."])]:
    if k not in st.session_state:
        st.session_state[k] = v

def reset_all():
    for k, v in [("snapshots",[]),("snap_idx",0),("status","ready"),
                  ("trail",[]),("facing","right"),("clips_ran",False),
                  ("log",["🔄 Reset efectuat. Harta actuală a fost păstrată."])]:
        st.session_state[k] = v

def advance():
    idx   = st.session_state.snap_idx
    snaps = st.session_state.snapshots
    if idx >= len(snaps) - 1:
        return
    idx += 1
    st.session_state.snap_idx = idx
    snap = snaps[idx]
    pos  = snap["pozitie"]
    prev = snaps[idx-1]["pozitie"]
    if pos != prev:
        if snap.get("directie"):
            st.session_state.facing = snap["directie"]
        if prev and prev not in st.session_state.trail:
            st.session_state.trail.append(prev)
    rez = snap["rezultat"]
    msg = snap["mesaj"]
    if rez == "succes":
        st.session_state.status = "success"
        st.session_state.log.append(f'<span class="log-success">{msg}</span>')
    elif rez in ("esec", "fara-drum"):
        st.session_state.status = "failure"
        st.session_state.log.append(f'<span class="log-error">{msg}</span>')
    else:
        st.session_state.status = "running"
        st.session_state.log.append(f'<span class="log-move">Pas {idx}: {msg} → {pos}</span>')
        if idx < len(snaps) - 1 and "Alunecare" in snaps[idx+1].get("mesaj", ""):
            idx += 1
            st.session_state.snap_idx = idx
            snap2 = snaps[idx]
            pos2  = snap2["pozitie"]
            prev2 = snaps[idx-1]["pozitie"]
            if pos2 != prev2:
                if snap2.get("directie"):
                    st.session_state.facing = snap2["directie"]
                if prev2 and prev2 not in st.session_state.trail:
                    st.session_state.trail.append(prev2)
            rez2 = snap2["rezultat"]
            msg2 = snap2["mesaj"]
            if rez2 == "succes":
                st.session_state.status = "success"
                st.session_state.log.append(f'<span class="log-success">{msg2}</span>')
            elif rez2 in ("esec", "fara-drum"):
                st.session_state.status = "failure"
                st.session_state.log.append(f'<span class="log-error">{msg2}</span>')
            else:
                st.session_state.log.append(f'<span class="log-move">Pas {idx}: {msg2} → {pos2}</span>')

st.markdown('<h1>🧊 FROZEN LAKE</h1>', unsafe_allow_html=True)
st.markdown('<h3>CLIPS ENGINE  <span class="clips-badge">frozen_lake.clp</span></h3>', unsafe_allow_html=True)
st.markdown("---")

if not os.path.exists(CLP_FILE):
    st.error(f"Fisierul **frozen_lake.clp** nu a fost gasit!\nPune-l in: `{os.path.dirname(CLP_FILE)}`")
    st.stop()

c1, c2, c3, c4 = st.columns([1.4, 1, 1, 1])
with c1: run_btn  = st.button("▶ Ruleaza CLIPS", use_container_width=True)
with c2: step_btn = st.button("⏭ Pas",          use_container_width=True)
with c3: auto_btn = st.button("⏩ Auto",         use_container_width=True)
with c4: rst_btn  = st.button("🔄 Reset Simulare", use_container_width=True)

if rst_btn:
    reset_all()

if run_btn:
    with st.spinner("Motor CLIPS in executie..."):
        try:
            snaps = run_clips_episode(
                st.session_state.initial_facts, 
                st.session_state.map_size,
                st.session_state.cell_types
            )
            st.session_state.snapshots = snaps
            st.session_state.snap_idx  = 0
            st.session_state.status    = "ready"
            st.session_state.trail     = []
            st.session_state.facing    = "right"
            st.session_state.clips_ran = True
            st.session_state.log       = [f"✅ CLIPS a generat <strong>{len(snaps)-1}</strong> pasi. Apasa Pas sau Auto."]
        except Exception as e:
            st.error(f"Eroare clipspy: {e}")

if step_btn and st.session_state.clips_ran and st.session_state.status in ("ready","running"):
    advance()

if auto_btn and st.session_state.clips_ran:
    while st.session_state.status in ("ready","running") and \
          st.session_state.snap_idx < len(st.session_state.snapshots) - 1:
        advance()

STATUS_MAP = {"ready":("badge-ready","⏸ PREGATIT"),"running":("badge-running","🔵 IN CURS"),
              "success":("badge-success","✅ SUCCES"),"failure":("badge-failure","❌ ESEC")}
cls, lbl = STATUS_MAP.get(st.session_state.status, STATUS_MAP["ready"])
idx      = st.session_state.snap_idx
snaps    = st.session_state.snapshots
cur_pos  = snaps[idx]["pozitie"] if snaps else (0, 0)
cur_dist = snaps[idx]["distante"] if snaps else {}
ar, ac   = cur_pos if cur_pos else (0, 0)
dist_cur = cur_dist.get((ar, ac), "--")

st.markdown(
    f'<div class="badge {cls}">{lbl}</div> '
    f'<span class="stat-chip">Pasi: <span>{max(0,idx)}</span></span>'
    f'<span class="stat-chip">Pozitie: <span>({ar},{ac})</span></span>'
    f'<span class="stat-chip">Dist obiectiv: <span>{dist_cur}</span></span>'
    f'<span class="stat-chip">Snap: <span>{idx}/{max(0,len(snaps)-1)}</span></span>',
    unsafe_allow_html=True
)

# Desenam harta cu datele din state
svg = render_svg(ar, ac, cur_dist, st.session_state.trail,
                 st.session_state.status, st.session_state.facing, max(0, idx),
                 st.session_state.map_size, st.session_state.cell_types)
svg_curatat = svg.replace("\n", "")
st.markdown(svg_curatat, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("**📋 Jurnal executie CLIPS**")
st.markdown(f'<div class="log-box">{"<br>".join(reversed(st.session_state.log[-25:]))}</div>',
            unsafe_allow_html=True)

with st.expander("📜 Fapte Asertate la Start"):
    st.code("\n".join(st.session_state.initial_facts), language="lisp")