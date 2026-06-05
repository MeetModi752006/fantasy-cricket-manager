"""
database_setup.py
-----------------
Creates and seeds the Fantasy Cricket SQLite database.
Tables:  stats, match, teams
Run this once before launching the application.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "fantasy_cricket.db")


# ---------------------------------------------------------------------------
# Schema helpers
# ---------------------------------------------------------------------------

CREATE_STATS = """
CREATE TABLE IF NOT EXISTS stats (
    player   TEXT PRIMARY KEY,
    matches  INTEGER NOT NULL,
    runs     INTEGER NOT NULL,
    hundreds INTEGER NOT NULL,
    fifties  INTEGER NOT NULL,
    value    REAL    NOT NULL,
    ctg      TEXT    NOT NULL   -- Batsman / Bowler / All-Rounder / Wicket-Keeper
);
"""

CREATE_MATCH = """
CREATE TABLE IF NOT EXISTS match (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    match_name TEXT NOT NULL,
    player   TEXT    NOT NULL,
    scored   INTEGER NOT NULL DEFAULT 0,
    faced    INTEGER NOT NULL DEFAULT 0,
    fours    INTEGER NOT NULL DEFAULT 0,
    sixes    INTEGER NOT NULL DEFAULT 0,
    bowled   INTEGER NOT NULL DEFAULT 0,
    maiden   INTEGER NOT NULL DEFAULT 0,
    given    REAL    NOT NULL DEFAULT 0,
    wkts     INTEGER NOT NULL DEFAULT 0,
    catches  INTEGER NOT NULL DEFAULT 0,
    stumping INTEGER NOT NULL DEFAULT 0,
    runout   INTEGER NOT NULL DEFAULT 0
);
"""

CREATE_TEAMS = """
CREATE TABLE IF NOT EXISTS teams (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    players TEXT NOT NULL,   -- comma-separated player names
    value   REAL NOT NULL DEFAULT 0
);
"""

# ---------------------------------------------------------------------------
# Seed data — stats table
# ---------------------------------------------------------------------------

STATS_DATA = [
    # Batsmen
    ("Virat Kohli",   300, 12169, 43, 62, 9.5,  "Batsman"),
    ("Rohit Sharma",  243, 9877,  29, 45, 8.0,  "Batsman"),
    ("Shubman Gill",  120, 4200,  8,  22, 7.5,  "Batsman"),
    ("KL Rahul",      195, 7140,  17, 40, 8.5,  "Batsman"),
    ("Shreyas Iyer",  100, 3200,  6,  18, 7.0,  "Batsman"),
    ("Ishan Kishan",  82,  2500,  1,  14, 6.5,  "Batsman"),

    # Bowlers
    ("Jasprit Bumrah",  130, 350,  0, 0, 9.0,  "Bowler"),
    ("Mohammed Shami",  100, 280,  0, 0, 8.0,  "Bowler"),
    ("Kuldeep Yadav",   90,  200,  0, 0, 7.5,  "Bowler"),
    ("Yuzvendra Chahal", 80, 180, 0, 0, 7.0,  "Bowler"),
    ("Arshdeep Singh",  70,  150,  0, 0, 6.5,  "Bowler"),
    ("Mohammed Siraj",  85,  190,  0, 0, 7.0,  "Bowler"),

    # All-Rounders
    ("Hardik Pandya",  180, 3500, 0, 18, 9.0,  "All-Rounder"),
    ("Ravindra Jadeja", 220, 4500, 0, 21, 9.5,  "All-Rounder"),
    ("Axar Patel",     120, 2000, 0, 10, 7.5,  "All-Rounder"),
    ("Shardul Thakur", 80,  1100, 0,  5, 7.0,  "All-Rounder"),

    # Wicket-Keepers
    ("MS Dhoni",       350, 10773, 0, 73, 9.0,  "Wicket-Keeper"),
    ("Rishabh Pant",   100, 3284,  5, 17, 8.5,  "Wicket-Keeper"),
    ("Sanju Samson",   90,  2500,  3, 14, 7.5,  "Wicket-Keeper"),
    ("Dinesh Karthik", 95,  2200,  0,  9, 7.0,  "Wicket-Keeper"),
]

# ---------------------------------------------------------------------------
# Seed data — match table  (two sample matches)
# ---------------------------------------------------------------------------

MATCH_DATA = [
    # match_name, player, scored, faced, fours, sixes, bowled, maiden, given, wkts, catches, stumping, runout
    # --- Match: India vs Australia ---
    ("India vs Australia", "Virat Kohli",    82, 94, 8, 2, 0, 0, 0,   0, 1, 0, 0),
    ("India vs Australia", "Rohit Sharma",   55, 48, 6, 2, 0, 0, 0,   0, 0, 0, 0),
    ("India vs Australia", "Shubman Gill",   33, 40, 4, 0, 0, 0, 0,   0, 1, 0, 0),
    ("India vs Australia", "KL Rahul",       28, 35, 2, 1, 0, 0, 0,   0, 0, 0, 0),
    ("India vs Australia", "Shreyas Iyer",   42, 38, 3, 2, 0, 0, 0,   0, 0, 0, 0),
    ("India vs Australia", "Ishan Kishan",   18, 22, 1, 1, 0, 0, 0,   0, 0, 0, 0),
    ("India vs Australia", "Hardik Pandya",  35, 28, 2, 2, 4,  0, 32, 2, 1, 0, 0),
    ("India vs Australia", "Ravindra Jadeja",22, 30, 1, 0, 10, 2, 38, 3, 2, 0, 1),
    ("India vs Australia", "Axar Patel",     10, 15, 0, 0, 8,  1, 30, 2, 0, 0, 0),
    ("India vs Australia", "Jasprit Bumrah",  2,  5, 0, 0, 10, 1, 28, 4, 0, 0, 0),
    ("India vs Australia", "Mohammed Shami",  0,  0, 0, 0, 8,  0, 42, 2, 1, 0, 0),
    ("India vs Australia", "Kuldeep Yadav",   0,  0, 0, 0, 10, 0, 35, 3, 1, 0, 0),
    ("India vs Australia", "Yuzvendra Chahal",0,  0, 0, 0, 10, 0, 40, 2, 0, 0, 0),
    ("India vs Australia", "Arshdeep Singh",  0,  0, 0, 0, 6,  0, 38, 1, 0, 0, 0),
    ("India vs Australia", "Mohammed Siraj",  0,  0, 0, 0, 8,  0, 45, 2, 0, 0, 0),
    ("India vs Australia", "Shardul Thakur",  5,  8, 0, 0, 4,  0, 30, 1, 0, 0, 0),
    ("India vs Australia", "MS Dhoni",       14, 10, 1, 1, 0,  0,  0, 0, 2, 1, 0),
    ("India vs Australia", "Rishabh Pant",   30, 25, 2, 2, 0,  0,  0, 0, 1, 0, 0),
    ("India vs Australia", "Sanju Samson",   12, 15, 1, 0, 0,  0,  0, 0, 1, 0, 0),
    ("India vs Australia", "Dinesh Karthik",  8,  6, 1, 0, 0,  0,  0, 0, 0, 0, 0),

    # --- Match: India vs England ---
    ("India vs England", "Virat Kohli",    102, 96, 10, 3, 0, 0, 0,   0, 0, 0, 0),
    ("India vs England", "Rohit Sharma",    75, 60,  7, 3, 0, 0, 0,   0, 1, 0, 0),
    ("India vs England", "Shubman Gill",    56, 65,  5, 1, 0, 0, 0,   0, 0, 0, 0),
    ("India vs England", "KL Rahul",        45, 50,  3, 1, 0, 0, 0,   0, 0, 0, 0),
    ("India vs England", "Shreyas Iyer",    20, 30,  2, 0, 0, 0, 0,   0, 1, 0, 0),
    ("India vs England", "Ishan Kishan",    38, 30,  4, 1, 0, 0, 0,   0, 0, 0, 0),
    ("India vs England", "Hardik Pandya",   50, 35,  3, 3, 6, 1, 40,  3, 1, 0, 1),
    ("India vs England", "Ravindra Jadeja", 30, 40,  2, 0, 8, 2, 32,  2, 2, 0, 0),
    ("India vs England", "Axar Patel",      15, 20,  1, 0, 6, 0, 28,  1, 0, 0, 0),
    ("India vs England", "Jasprit Bumrah",   0,  0,  0, 0, 10,2, 22,  5, 0, 0, 0),
    ("India vs England", "Mohammed Shami",   0,  0,  0, 0, 8, 0, 36,  3, 0, 0, 0),
    ("India vs England", "Kuldeep Yadav",    0,  0,  0, 0, 8, 1, 30,  2, 1, 0, 0),
    ("India vs England", "Yuzvendra Chahal", 0,  0,  0, 0, 10,0, 48,  1, 2, 0, 0),
    ("India vs England", "Arshdeep Singh",   0,  0,  0, 0, 8, 0, 40,  2, 0, 0, 0),
    ("India vs England", "Mohammed Siraj",   0,  0,  0, 0, 6, 0, 35,  1, 0, 0, 0),
    ("India vs England", "Shardul Thakur",   8, 10,  0, 0, 6, 0, 44,  2, 1, 0, 0),
    ("India vs England", "MS Dhoni",        20, 15,  2, 1, 0, 0,  0,  0, 3, 0, 0),
    ("India vs England", "Rishabh Pant",    48, 40,  4, 2, 0, 0,  0,  0, 2, 0, 0),
    ("India vs England", "Sanju Samson",    22, 25,  2, 1, 0, 0,  0,  0, 1, 0, 0),
    ("India vs England", "Dinesh Karthik",  12,  8,  2, 0, 0, 0,   0, 0, 0, 0, 0),
]


def build_database():
    """Drop and recreate the database, then seed all tables."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript(f"""
        DROP TABLE IF EXISTS stats;
        DROP TABLE IF EXISTS match;
        DROP TABLE IF EXISTS teams;
        {CREATE_STATS}
        {CREATE_MATCH}
        {CREATE_TEAMS}
    """)

    cur.executemany(
        "INSERT INTO stats (player, matches, runs, hundreds, fifties, value, ctg) "
        "VALUES (?,?,?,?,?,?,?)",
        STATS_DATA,
    )

    cur.executemany(
        "INSERT INTO match (match_name, player, scored, faced, fours, sixes, "
        "bowled, maiden, given, wkts, catches, stumping, runout) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        MATCH_DATA,
    )

    conn.commit()
    conn.close()
    print(f"Database created at: {DB_PATH}")


if __name__ == "__main__":
    build_database()
