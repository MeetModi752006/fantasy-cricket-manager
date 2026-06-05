"""
score_calculator.py
--------------------
Pure functions that compute a player's fantasy points from a match row.
Keeping all scoring logic here makes it easy to modify rules in one place.

Scoring Rules
-------------
Batting
  - 1 point per 2 runs
  - +5 for a half-century (50+ runs)
  - +10 for a century (100+ runs)
  - +2 if strike-rate 80–100
  - +4 if strike-rate > 100
  - +1 per boundary (four), +2 per over-boundary (six)

Bowling
  - 10 points per wicket
  - +5 bonus for 3 wickets in an innings
  - +10 bonus for 5+ wickets in an innings
  - +4 if economy 3.5–4.5
  - +7 if economy 2.0–3.5
  - +10 if economy < 2.0

Fielding
  - 10 points each for catch / stumping / run-out
"""


def _batting_points(scored: int, faced: int, fours: int, sixes: int) -> float:
    """Return batting fantasy points for one innings."""
    points = scored / 2.0                    # 1 point per 2 runs
    points += fours * 1                      # boundary bonus
    points += sixes * 2                      # over-boundary bonus

    if scored >= 100:
        points += 10                         # century bonus
    elif scored >= 50:
        points += 5                          # half-century bonus

    if faced > 0:
        strike_rate = (scored / faced) * 100
        if strike_rate > 100:
            points += 4
        elif strike_rate >= 80:
            points += 2

    return points


def _bowling_points(bowled: int, maiden: int, given: float, wkts: int) -> float:
    """Return bowling fantasy points for one spell."""
    points = wkts * 10                       # 10 per wicket

    if wkts >= 5:
        points += 10                         # 5-fer bonus
    elif wkts >= 3:
        points += 5                          # 3-fer bonus

    if bowled > 0:
        economy = given / bowled             # runs per over
        if economy < 2.0:
            points += 10
        elif economy <= 3.5:
            points += 7
        elif economy <= 4.5:
            points += 4

    points += maiden * 3                     # small maiden bonus
    return points


def _fielding_points(catches: int, stumping: int, runout: int) -> float:
    """Return fielding fantasy points."""
    return (catches + stumping + runout) * 10


def calculate_player_points(row: tuple) -> float:
    """
    Compute total fantasy points for a single player from a match row.

    Parameters
    ----------
    row : tuple
        (player, scored, faced, fours, sixes, bowled, maiden, given,
         wkts, catches, stumping, runout)

    Returns
    -------
    float
        Total fantasy points.
    """
    (_, scored, faced, fours, sixes,
     bowled, maiden, given, wkts,
     catches, stumping, runout) = row

    batting  = _batting_points(scored, faced, fours, sixes)
    bowling  = _bowling_points(bowled, maiden, given, wkts)
    fielding = _fielding_points(catches, stumping, runout)

    return batting + bowling + fielding


def calculate_team_score(player_names: list, match_name: str, db_conn) -> dict:
    """
    Calculate the total fantasy score for a team in a given match.

    Parameters
    ----------
    player_names : list[str]
        Names of the selected players.
    match_name : str
        Name of the match (as stored in the match table).
    db_conn : sqlite3.Connection
        Open database connection.

    Returns
    -------
    dict
        {"total": float, "breakdown": {player: points}}
    """
    cur = db_conn.cursor()
    breakdown = {}

    for player in player_names:
        cur.execute(
            """
            SELECT player, scored, faced, fours, sixes, bowled, maiden,
                   given, wkts, catches, stumping, runout
            FROM   match
            WHERE  player = ? AND match_name = ?
            """,
            (player, match_name),
        )
        row = cur.fetchone()
        if row:
            breakdown[player] = calculate_player_points(row)
        else:
            breakdown[player] = 0.0          # player did not appear in this match

    return {
        "total": sum(breakdown.values()),
        "breakdown": breakdown,
    }
