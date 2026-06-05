# Fantasy Cricket – Python Final Project

## Overview
A desktop Fantasy Cricket game built with Python, Tkinter, and SQLite.
Players form an 11-member virtual team from real Indian cricket players,
then evaluate their team score based on actual match performance data.

---

## Project Structure

```
fantasy_cricket/
├── main.py              # Main GUI application (entry point)
├── database_setup.py    # Creates and seeds the SQLite database
├── score_calculator.py  # Scoring logic (batting / bowling / fielding)
├── fantasy_cricket.db   # SQLite database (auto-created on first run)
└── README.md
```

---

## How to Run

### Step 1 – Set up the database (first time only)
```bash
python database_setup.py
```

### Step 2 – Launch the application
```bash
python main.py
```

> The app will auto-create the database if it doesn't exist yet.

---

## How to Play

1. **Create a New Team** – Go to *Manage Teams → New Team* and enter a team name.
2. **Select Players** – Use the category radio buttons (Batsman / Bowler /
   All-Rounder / Wicket-Keeper) to browse players.
   Double-click or click **Add ▶** to add a player to your team.
3. **Remove Players** – Double-click a player in the right list or click **◀ Remove**.
4. **Save Your Team** – *Manage Teams → Save Team* (validates rules first).
5. **Evaluate Score** – *Score → Evaluate Score*, then pick your team and a match.
   A score report window shows individual and total fantasy points.

---

## Team Rules
| Category       | Min | Max |
|----------------|-----|-----|
| Batsman        |  3  |  5  |
| Bowler         |  3  |  5  |
| All-Rounder    |  1  |  3  |
| Wicket-Keeper  |  1  |  2  |
| **Total**      | **11** | **11** |

Total player value budget: **100 points**

---

## Scoring Rules

### Batting
- 1 point per 2 runs
- +5 half-century bonus | +10 century bonus
- Strike rate 80–100 → +2 | >100 → +4
- +1 per four | +2 per six

### Bowling
- 10 points per wicket
- 3-wicket haul → +5 | 5-wicket haul → +10
- Economy 3.5–4.5 → +4 | 2.0–3.5 → +7 | <2.0 → +10

### Fielding
- 10 points each for catch / stumping / run-out

---

## Database Tables

### `stats`
| Column  | Type    | Description                        |
|---------|---------|------------------------------------|
| player  | TEXT PK | Player name                        |
| matches | INTEGER | Career matches                     |
| runs    | INTEGER | Career runs                        |
| hundreds| INTEGER | Career centuries                   |
| fifties | INTEGER | Career fifties                     |
| value   | REAL    | Fantasy value (budget cost)        |
| ctg     | TEXT    | Category (Batsman/Bowler/etc.)     |

### `match`
| Column    | Type    | Description              |
|-----------|---------|--------------------------|
| id        | INTEGER | Auto-increment PK        |
| match_name| TEXT    | Match identifier         |
| player    | TEXT    | Player name              |
| scored    | INTEGER | Runs scored              |
| faced     | INTEGER | Balls faced              |
| fours     | INTEGER | Boundaries hit           |
| sixes     | INTEGER | Over-boundaries hit      |
| bowled    | INTEGER | Overs bowled             |
| maiden    | INTEGER | Maiden overs             |
| given     | REAL    | Runs conceded            |
| wkts      | INTEGER | Wickets taken            |
| catches   | INTEGER | Catches taken            |
| stumping  | INTEGER | Stumpings                |
| runout    | INTEGER | Run-outs effected        |

### `teams`
| Column  | Type    | Description                        |
|---------|---------|------------------------------------|
| id      | INTEGER | Auto-increment PK                  |
| name    | TEXT    | Team name                          |
| players | TEXT    | Comma-separated player names       |
| value   | REAL    | Total value of team                |

---

## Requirements
- Python 3.8+
- `tkinter` (usually bundled with Python; on Linux: `sudo apt install python3-tk`)
- `sqlite3` (standard library)
