# Frozen Lake – Expert System (CLIPS + Streamlit)

This is our project for the Knowledge-Based Systems course: an expert system that solves the classic *Frozen Lake* problem — get an agent from a start cell to a goal cell on a grid, without falling into any holes, and do it in the fewest steps possible.

Instead of writing a normal BFS in Python, we did it "the expert systems way": all the pathfinding logic lives in CLIPS rules, and Python only handles the visual side (Streamlit) and talks to CLIPS through `clipspy`. Watching the rules fire one by one and actually seeing the distances get calculated on the grid is honestly the fun part of this project.

Built by **Florea Marian, Constantin Rareș Daniel and Ghergheluc Raul**, Faculty of Automatic Control and Computer Engineering, TUIASI.

## What it does

- Generates a random map (from 3×3 up to 8×8) with a hole probability you control from a slider
- Two modes: **deterministic**, where every move does exactly what you'd expect, and **slippery**, where there's a 60% chance the agent slides sideways instead of going where it was told
- Shows the distance-to-goal CLIPS computed for every single cell, right on the map — so you can actually see the algorithm "thinking"
- Lets you run the whole thing at once, go step by step, or hit Auto and watch the agent walk itself to the goal
- Keeps a log of every move, in order, so you can trace exactly what the engine decided and why
- Correctly tells apart the three ways an episode can end: reached the goal, fell in a hole, or no path exists at all

## How the CLIPS side actually works

The rules in `frozen_lake.clp` are split into a few groups, and `salience` is what decides which rule wins when several could fire at once:

- **Init (salience 100):** puts distance 0 on the goal cell — this is where the whole propagation starts
- **Propagation (salience 90) + shortcut updates (salience 95):** these rules spread the distance outward to every reachable neighbor, and fix it if a shorter path to that cell shows up later
- **Terminal states (salience 200):** as soon as the agent lands on a hole or on the goal, everything stops, no more moves get processed
- **No path found (salience 80):** if the current cell never got a distance assigned, the engine gives up gracefully instead of looping forever
- **Movement (salience 50 → 47, right/down/left/up):** move to whichever neighbor has a distance exactly 1 lower than the current cell
- **Slipping rules (salience 45/44):** only active in slippery mode, these handle the perpendicular deviation instead of the intended move

The nice part about doing this with salience instead of, say, just picking the first matching rule: no matter which direction rule ends up firing when there's a tie, the agent is still guaranteed to move to a cell that's one step closer — so the path length stays optimal, only the exact route taken can differ.

## Running it yourself

```bash
git clone https://github.com/<user>/frozen-lake-clips.git
cd frozen-lake-clips

python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run frozen_lake_app.py
```

It'll open in your browser at `http://localhost:8501`. Just make sure `frozen_lake.clp` stays in the same folder as `frozen_lake_app.py` — the app looks for it right next to itself.

## What's in here

```
frozen_lake_app.py   → Streamlit UI + all the clipspy glue code
frozen_lake.clp       → the actual CLIPS rule base, i.e. the "brain"
requirements.txt      → the two packages you need
```

## Built with

CLIPS for the rule engine, [clipspy](https://clipspy.readthedocs.io/) to talk to it from Python, and Streamlit for the interface.

## Things we'd add if we kept working on it

- Editing the map by clicking directly on cells instead of only random generation
- Multiple checkpoints/sub-goals instead of a single goal
- Saving/loading a specific map so you can re-test the same scenario
- Smarter (dynamic) rule priorities for bigger maps, so the engine re-evaluates less

## License

School project, free to use for learning purposes.
