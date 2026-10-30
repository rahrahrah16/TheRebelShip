# The Rebel Ship

The Rebel Ship is a small top-down space game made with Pygame. The player mines asteroids, builds helper ships, upgrades the ship and fights a rival fleet.

## Run the game

From this folder, activate the supplied environment and start the game:

```bash
source .venv/bin/activate
python -m client.main
```

If pygame-ce is not installed in that environment yet, install the one listed in `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

## Controls

| Key or mouse | Action |
| --- | --- |
| W, A, S, D or arrow keys | Move |
| J or left mouse click | Shoot toward the pointer |
| Space | Open or close the Control Center |
| P | Pause or continue |
| F11 | Toggle fullscreen |
| Enter | Start from the title screen |
| R | Restart after a win or loss |
| Esc | Quit |

In the **Fleet** tab, select a helper ship and choose **Mining Asteroids**, **Attack Enemies**, or **Follow Ship**. **Recall All** sends every helper back to the player. A new helper costs 34 Iron, 24 Copper, 15 Crystal and 18 Power. The **Tech Lab** contains four upgrades.

## How the code is organized

- `game/model.py` stores the game state and rules. It does not import pygame.
- `client/main.py` reads keys and mouse input, draws the game and runs the frame loop.
- `api/templates/` contains the practice leaderboard and rules pages.
- `api/static/style.css` styles both pages.

The model uses plain classes and short methods so the rules are easier to follow and explain.
