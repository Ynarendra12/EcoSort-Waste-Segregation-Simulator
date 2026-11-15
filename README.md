# EcoSort: Interactive 2D Waste Segregation Simulator

A colourful 2D game that teaches children how to sort waste into **Wet**, **Dry** and **Recycle** bins, built with **Python** and **Pygame**. All the Computer Graphics (transformations, line and circle drawing, polygon filling, clipping and viewport mapping) is written by hand instead of using ready-made library functions.

> Mini project for the **Computer Graphics Lab**

![EcoSort title screen](screenshots/01-title-screen.png)

## Table of Contents
- [About the Project](#about-the-project)
- [Features](#features)
- [Screenshots](#screenshots)
- [Getting Started](#getting-started)
- [Controls](#controls)
- [How the Game Works](#how-the-game-works)
- [Computer Graphics Concepts Used](#computer-graphics-concepts-used)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Testing](#testing)
- [Limitations and Future Work](#limitations-and-future-work)
- [Author](#author)

## About the Project
Many children do not know which waste goes into which bin. EcoSort turns a normal day (going to school by bus, sitting in class, buying a snack, going on a picnic) into a small story. After eating a snack, the player must carry the wrapper, peel or bottle to the correct dustbin to earn points.

## Features
- Choose one of **four characters**: duck, boy, girl or cat.
- **Two levels**: School Day (home, bus ride, school, classroom, canteen) and Park Picnic.
- **Six snacks**, each leaving waste that belongs to the Wet, Dry or Recycle bin.
- Scoring: **+10** for a correct bin and **-5** for a wrong one, with a tip that explains the right answer.
- Star rating (1 to 3 stars) for each level and a final **Eco Score** with a title (Keep trying, Eco Beginner, Eco Star, ECO HERO).
- Smooth animation at 60 FPS, with sound effects generated in code (no image or audio files needed).
- Press **F1** in any scene to see which Computer Graphics concepts are used on that screen.

## Screenshots

### Figure 1: Title screen and character selection
![Title screen with four characters](screenshots/01-title-screen.png)

### Figure 2: Places menu
![Places menu with School Day and Park Picnic](screenshots/02-places-menu.png)

### Figure 3: School Day, at home
![Character at home with school bag, lunch box and water bottle](screenshots/03-school-home.png)

### Figure 4: School Day, bus ride
![School bus on the road with a route mini-map](screenshots/04-bus-ride.png)

### Figure 5: School Day, classroom
![Classroom with teacher and students](screenshots/05-classroom.png)

### Figure 6: Canteen menu
![Canteen snack menu with six items](screenshots/06-canteen-menu.png)

### Figure 7: Dustbins in the canteen
![Character carrying waste near the Wet, Dry and Recycle dustbins](screenshots/07-canteen-bins.png)

### Figure 8: Park Picnic level
![Park scene with pond, windmill and dustbins](screenshots/08-park-picnic.png)

### Figure 9: Level result
![Level complete screen with stars, score and accuracy](screenshots/09-level-result.png)

### Figure 10: Final Eco Score
![Final Eco Score screen with rating](screenshots/10-eco-score.png)

*The scores on the result screens are sample values used to take the screenshots.*

## Getting Started

### Requirements
- Python 3 (download from [python.org](https://www.python.org/downloads/); tick "Add python.exe to PATH" on Windows)
- Pygame

### Run the game
```bash
git clone https://github.com/Ynarendra12/EcoSort-Waste-Segregation-Simulator.git
cd EcoSort-Waste-Segregation-Simulator
pip install pygame
python main.py
```

## Controls

| Key or action | What it does |
| --- | --- |
| Left / Right arrow or A / D | Walk |
| Mouse | Choose a character, a level or a snack |
| E, Enter or Space | Open the snack menu and pour waste into the nearest bin |
| Space | Skip a part of the School Day story |
| Esc | Go back |
| F1 | Show the Computer Graphics concepts used on the current screen |

## How the Game Works
1. Pick a character on the title screen and press Start.
2. Choose **School Day** or **Park Picnic** on the places menu.
3. Walk to the canteen counter (or the picnic basket) and choose a snack.
4. The character eats it and the waste appears in hand.
5. Walk to a dustbin and pour the waste in. A correct bin gives +10 points; a wrong bin gives -5 and a hint.
6. Sort enough items (4 in School Day, 5 in Park Picnic) to finish the level and see the star rating.
7. Press **Finish** on the places menu to see your final Eco Score.

| Food | Waste | Correct bin |
| --- | --- | --- |
| Chips | Chips packet | Dry |
| Banana | Banana peel | Wet |
| Juice box | Juice carton | Recycle |
| Apple | Apple core | Wet |
| Sandwich | Paper wrapper | Dry |
| Water bottle | Plastic bottle | Recycle |

## Computer Graphics Concepts Used

| S.NO | Topic | Where it is used | File |
| --- | --- | --- | --- |
| 1 | DDA line algorithm | Picket fence rails in the park | `algorithms.py` |
| 2 | Bresenham's line algorithm | Road dashes and sun rays | `algorithms.py` |
| 3 | Midpoint circle algorithm | Ring around the sun | `algorithms.py` |
| 4 | Scan-line polygon fill | Body of the dustbins | `algorithms.py` |
| 5 | Translation and scaling | Walking, bus driving, gate sliding, bus door opening | `transforms.py` |
| 6 | Rotation and reflection | Wheels, windmill, sun rays, pond reflection | `transforms.py` |
| 7 | Shear (extra) | Swaying trees, grass and flag, shaking bin | `transforms.py` |
| 8 | Composite transformations | Rotation about a pivot: translate, rotate, translate back | `transforms.py` |
| 9 | Matrix representation (2D) | 3x3 homogeneous matrices | `transforms.py` |
| 10 | Window to viewport mapping | Route mini-map on the bus ride | `transforms.py`, `scene_school.py` |
| 11 | Line clipping (Cohen-Sutherland) | Road dashes clipped to the screen | `algorithms.py`, `scene_school.py` |
| Extra | Hierarchical modelling | Characters whose arms and legs rotate about joints | `characters.py` |

## Project Structure
```
EcoSort/
├── main.py            # Game loop, scene switching, F1 concepts overlay
├── settings.py        # Screen size, FPS, scoring, bin definitions
├── transforms.py      # 3x3 matrices, composite transforms, window-to-viewport
├── algorithms.py      # DDA, Bresenham, midpoint circle, Cohen-Sutherland, scan-line fill
├── gfx.py             # Drawing helpers that work through a matrix
├── characters.py      # The four characters and their walking animation
├── props.py           # Bus, school, traffic light, trees, windmill, dustbins
├── items.py           # The six foods and their waste
├── binlevel.py        # Shared bin game (eat, carry, pour, score)
├── scene_menus.py     # Title, places, result and end screens
├── scene_school.py    # School Day level
├── scene_park.py      # Park Picnic level
├── ui.py              # Buttons, panels, messages, particles
├── sound.py           # Sound effects generated in code
└── screenshots/       # Images used in this README
```

## Tech Stack
- **Language:** Python 3
- **Library:** Pygame (window, input, game loop and pixel/polygon drawing only)
- **Editor:** Visual Studio Code

## Testing
The graphics functions and game rules were checked with an automated script (23 checks, all passed): transformation results, line and circle algorithms, clipping, scan-line fill, scoring, star ratings, and a run of each scene without errors.

## Limitations and Future Work
- The game is **2D**, so 3D transformations, projections, curves and hidden surface removal are not covered.
- Only two levels are playable. Temple, Market, Restaurant and Game Zone are shown as locked places.
- Ideas for later: more levels, flood fill and boundary fill, Bezier curves for the waste flight path, Cyrus-Beck and Sutherland-Hodgman clipping, a 3D version, more waste types and a high score list.

## Author
**Yerragolla Narendra**
B.Tech CSE, Department of Computer Science and Engineering, MRIIRS
Computer Graphics Lab Mini Project, 2026-2027
