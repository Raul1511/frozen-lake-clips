; FROZEN LAKE CLIPS 

; ═══════════════════════════════════════════════════════════════
; 1. INIȚIALIZARE
; ═══════════════════════════════════════════════════════════════
(defrule initializare-distanta-obiectiv
   (declare (salience 100))
   (scop calculeaza-distante)
   (tip-celula ?r ?c obiectiv)
   (not (distanta ?r ?c 0))
=>
   (assert (distanta ?r ?c 0))
)

; ═══════════════════════════════════════════════════════════════
; 2. PROPAGARE STANDARD (Dacă celula nu are nicio distanță)
; ═══════════════════════════════════════════════════════════════
(defrule propaga-sus
   (declare (salience 90))
   (scop calculeaza-distante)
   (distanta ?r ?c ?d)
   (test (> ?r 0))
   (not (tip-celula =(- ?r 1) ?c groapa))
   (not (distanta =(- ?r 1) ?c ?x))
=>
   (assert (distanta (- ?r 1) ?c (+ ?d 1)))
)

(defrule propaga-jos
   (declare (salience 90))
   (scop calculeaza-distante)
   (distanta ?r ?c ?d)
   (dimensiune-harta ?nr ?nc)
   (test (< ?r (- ?nr 1)))
   (not (tip-celula =(+ ?r 1) ?c groapa))
   (not (distanta =(+ ?r 1) ?c ?x))
=>
   (assert (distanta (+ ?r 1) ?c (+ ?d 1)))
)

(defrule propaga-stanga
   (declare (salience 90))
   (scop calculeaza-distante)
   (distanta ?r ?c ?d)
   (test (> ?c 0))
   (not (tip-celula ?r =(- ?c 1) groapa))
   (not (distanta ?r =(- ?c 1) ?x))
=>
   (assert (distanta ?r (- ?c 1) (+ ?d 1)))
)

(defrule propaga-dreapta
   (declare (salience 90))
   (scop calculeaza-distante)
   (distanta ?r ?c ?d)
   (dimensiune-harta ?nr ?nc)
   (test (< ?c (- ?nc 1)))
   (not (tip-celula ?r =(+ ?c 1) groapa))
   (not (distanta ?r =(+ ?c 1) ?x))
=>
   (assert (distanta ?r (+ ?c 1) (+ ?d 1)))
)

; ═══════════════════════════════════════════════════════════════
; 3. UPDATE SCURTĂTURĂ (Corectează drumurile ineficiente)
; ═══════════════════════════════════════════════════════════════
(defrule update-sus
   (declare (salience 95))
   (scop calculeaza-distante)
   (distanta ?r ?c ?d)
   (test (> ?r 0))
   (not (tip-celula =(- ?r 1) ?c groapa))
   ?vechi <- (distanta =(- ?r 1) ?c ?d-vechi)
   (test (> ?d-vechi (+ ?d 1)))
=>
   (retract ?vechi)
   (assert (distanta (- ?r 1) ?c (+ ?d 1)))
)

(defrule update-jos
   (declare (salience 95))
   (scop calculeaza-distante)
   (distanta ?r ?c ?d)
   (dimensiune-harta ?nr ?nc)
   (test (< ?r (- ?nr 1)))
   (not (tip-celula =(+ ?r 1) ?c groapa))
   ?vechi <- (distanta =(+ ?r 1) ?c ?d-vechi)
   (test (> ?d-vechi (+ ?d 1)))
=>
   (retract ?vechi)
   (assert (distanta (+ ?r 1) ?c (+ ?d 1)))
)

(defrule update-stanga
   (declare (salience 95))
   (scop calculeaza-distante)
   (distanta ?r ?c ?d)
   (test (> ?c 0))
   (not (tip-celula ?r =(- ?c 1) groapa))
   ?vechi <- (distanta ?r =(- ?c 1) ?d-vechi)
   (test (> ?d-vechi (+ ?d 1)))
=>
   (retract ?vechi)
   (assert (distanta ?r (- ?c 1) (+ ?d 1)))
)

(defrule update-dreapta
   (declare (salience 95))
   (scop calculeaza-distante)
   (distanta ?r ?c ?d)
   (dimensiune-harta ?nr ?nc)
   (test (< ?c (- ?nc 1)))
   (not (tip-celula ?r =(+ ?c 1) groapa))
   ?vechi <- (distanta ?r =(+ ?c 1) ?d-vechi)
   (test (> ?d-vechi (+ ?d 1)))
=>
   (retract ?vechi)
   (assert (distanta ?r (+ ?c 1) (+ ?d 1)))
)

; ═══════════════════════════════════════════════════════════════
; 4. STĂRI TERMINALE
; ═══════════════════════════════════════════════════════════════
(defrule agent-in-groapa
   (declare (salience 200))
   ?g <- (scop deplasare)
   (pozitie-agent ?r ?c)
   (tip-celula ?r ?c groapa)
=>
   (retract ?g)
   (assert (scop oprire))
)

(defrule agent-la-obiectiv
   (declare (salience 200))
   ?g <- (scop deplasare)
   (pozitie-agent ?r ?c)
   (tip-celula ?r ?c obiectiv)
=>
   (retract ?g)
   (assert (scop oprire))
)

(defrule nu-exista-drum
   (declare (salience 80))
   ?g <- (scop deplasare)
   (pozitie-agent ?r ?c)
   (not (distanta ?r ?c ?d))
=>
   (retract ?g)
   (assert (scop oprire))
)

; ═══════════════════════════════════════════════════════════════
; 5. DEPLASAREA AGENTULUI
; ═══════════════════════════════════════════════════════════════
(defrule alege-dreapta
   (declare (salience 50))
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   (distanta ?r ?c ?dcurent)
   (distanta ?r =(+ ?c 1) ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
=>
   (retract ?p ?g)
   (assert (pozitie-agent ?r (+ ?c 1)))
   (assert (scop deplasare))
)

(defrule alege-jos
   (declare (salience 49))
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   (distanta ?r ?c ?dcurent)
   (distanta =(+ ?r 1) ?c ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
=>
   (retract ?p ?g)
   (assert (pozitie-agent (+ ?r 1) ?c))
   (assert (scop deplasare))
)

(defrule alege-stanga
   (declare (salience 48))
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   (distanta ?r ?c ?dcurent)
   (distanta ?r =(- ?c 1) ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
=>
   (retract ?p ?g)
   (assert (pozitie-agent ?r (- ?c 1)))
   (assert (scop deplasare))
)

(defrule alege-sus
   (declare (salience 47))
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   (distanta ?r ?c ?dcurent)
   (distanta =(- ?r 1) ?c ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
=>
   (retract ?p ?g)
   (assert (pozitie-agent (- ?r 1) ?c))
   (assert (scop deplasare))
)

(defrule oprire
   ?g <- (scop oprire)
=>
   (retract ?g)
)

; ═══════════════════════════════════════════════════════════════
; 6. DEPLASARE ALUNECOASĂ (is_slippery)
; ═══════════════════════════════════════════════════════════════
(defrule alunecare-dreapta-sus
   (declare (salience 45))
   (mediu alunecos)
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   ?ar <- (alunecare-rand ?val)
   (test (= ?val 1))
   (distanta ?r ?c ?dcurent)
   (distanta ?r =(+ ?c 1) ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
   (test (> ?r 0))
   (not (tip-celula =(- ?r 1) ?c groapa))
=>
   (retract ?p ?g ?ar)
   (assert (pozitie-agent (- ?r 1) ?c))
   (assert (scop deplasare))
)

(defrule alunecare-dreapta-jos
   (declare (salience 44))
   (mediu alunecos)
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   ?ar <- (alunecare-rand ?val)
   (test (= ?val 2))
   (distanta ?r ?c ?dcurent)
   (distanta ?r =(+ ?c 1) ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
   (dimensiune-harta ?nr ?nc)
   (test (< ?r (- ?nr 1)))
   (not (tip-celula =(+ ?r 1) ?c groapa))
=>
   (retract ?p ?g ?ar)
   (assert (pozitie-agent (+ ?r 1) ?c))
   (assert (scop deplasare))
)

(defrule alunecare-jos-stanga
   (declare (salience 45))
   (mediu alunecos)
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   ?ar <- (alunecare-rand ?val)
   (test (= ?val 1))
   (distanta ?r ?c ?dcurent)
   (distanta =(+ ?r 1) ?c ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
   (test (> ?c 0))
   (not (tip-celula ?r =(- ?c 1) groapa))
=>
   (retract ?p ?g ?ar)
   (assert (pozitie-agent ?r (- ?c 1)))
   (assert (scop deplasare))
)

(defrule alunecare-jos-dreapta
   (declare (salience 44))
   (mediu alunecos)
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   ?ar <- (alunecare-rand ?val)
   (test (= ?val 2))
   (distanta ?r ?c ?dcurent)
   (distanta =(+ ?r 1) ?c ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
   (dimensiune-harta ?nr ?nc)
   (test (< ?c (- ?nc 1)))
   (not (tip-celula ?r =(+ ?c 1) groapa))
=>
   (retract ?p ?g ?ar)
   (assert (pozitie-agent ?r (+ ?c 1)))
   (assert (scop deplasare))
)

(defrule alunecare-stanga-sus
   (declare (salience 45))
   (mediu alunecos)
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   ?ar <- (alunecare-rand ?val)
   (test (= ?val 1))
   (distanta ?r ?c ?dcurent)
   (distanta ?r =(- ?c 1) ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
   (test (> ?r 0))
   (not (tip-celula =(- ?r 1) ?c groapa))
=>
   (retract ?p ?g ?ar)
   (assert (pozitie-agent (- ?r 1) ?c))
   (assert (scop deplasare))
)

(defrule alunecare-stanga-jos
   (declare (salience 44))
   (mediu alunecos)
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   ?ar <- (alunecare-rand ?val)
   (test (= ?val 2))
   (distanta ?r ?c ?dcurent)
   (distanta ?r =(- ?c 1) ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
   (dimensiune-harta ?nr ?nc)
   (test (< ?r (- ?nr 1)))
   (not (tip-celula =(+ ?r 1) ?c groapa))
=>
   (retract ?p ?g ?ar)
   (assert (pozitie-agent (+ ?r 1) ?c))
   (assert (scop deplasare))
)

(defrule alunecare-sus-stanga
   (declare (salience 45))
   (mediu alunecos)
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   ?ar <- (alunecare-rand ?val)
   (test (= ?val 1))
   (distanta ?r ?c ?dcurent)
   (distanta =(- ?r 1) ?c ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
   (test (> ?c 0))
   (not (tip-celula ?r =(- ?c 1) groapa))
=>
   (retract ?p ?g ?ar)
   (assert (pozitie-agent ?r (- ?c 1)))
   (assert (scop deplasare))
)

(defrule alunecare-sus-dreapta
   (declare (salience 44))
   (mediu alunecos)
   ?g <- (scop deplasare)
   ?p <- (pozitie-agent ?r ?c)
   ?ar <- (alunecare-rand ?val)
   (test (= ?val 2))
   (distanta ?r ?c ?dcurent)
   (distanta =(- ?r 1) ?c ?dvecin)
   (test (= ?dvecin (- ?dcurent 1)))
   (dimensiune-harta ?nr ?nc)
   (test (< ?c (- ?nc 1)))
   (not (tip-celula ?r =(+ ?c 1) groapa))
=>
   (retract ?p ?g ?ar)
   (assert (pozitie-agent ?r (+ ?c 1)))
   (assert (scop deplasare))
)

(defrule curata-alunecare-rand
   (declare (salience 10))
   (scop deplasare)
   ?ar <- (alunecare-rand ?val)
=>
   (retract ?ar)
)