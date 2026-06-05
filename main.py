"""
main.py
-------
Fantasy Cricket – main GUI application.

Requirements
  - Python 3.8+
  - tkinter  (standard library)
  - sqlite3  (standard library)

Run
  python main.py

Make sure database_setup.py has been executed at least once first.
"""

import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from database_setup import DB_PATH, build_database
from score_calculator import calculate_team_score

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CATEGORIES = ["Batsman", "Bowler", "All-Rounder", "Wicket-Keeper"]

SELECTION_RULES = {
    "Batsman":       (3, 5),   # min, max
    "Bowler":        (3, 5),
    "All-Rounder":   (1, 3),
    "Wicket-Keeper": (1, 2),
}

TOTAL_PLAYER_LIMIT = 11
TOTAL_POINTS_BUDGET = 100.0   # budget in "value" units

COLORS = {
    "bg":        "#1a2b3c",
    "panel":     "#243447",
    "accent":    "#e8c84a",
    "btn":       "#2d7a4f",
    "btn_text":  "#ffffff",
    "text":      "#e8edf2",
    "subtext":   "#8fa3b8",
    "listbg":    "#1e3148",
    "highlight": "#2d7a4f",
    "error":     "#c0392b",
}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db_connection() -> sqlite3.Connection:
    """Open and return a connection to the cricket database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_players_by_category(category: str) -> list:
    """Return list of player names in the given category."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT player, value FROM stats WHERE ctg = ? ORDER BY value DESC",
                    (category,))
        rows = cur.fetchall()
        conn.close()
        return [(r["player"], r["value"]) for r in rows]
    except sqlite3.Error as exc:
        messagebox.showerror("Database Error", str(exc))
        return []


def fetch_match_names() -> list:
    """Return distinct match names from the match table."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT match_name FROM match ORDER BY match_name")
        rows = cur.fetchall()
        conn.close()
        return [r["match_name"] for r in rows]
    except sqlite3.Error as exc:
        messagebox.showerror("Database Error", str(exc))
        return []


def fetch_saved_teams() -> list:
    """Return all saved team names."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM teams ORDER BY name")
        rows = cur.fetchall()
        conn.close()
        return [r["name"] for r in rows]
    except sqlite3.Error as exc:
        messagebox.showerror("Database Error", str(exc))
        return []


def save_team_to_db(team_name: str, player_names: list, total_value: float):
    """Persist a team to the teams table."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        players_str = ",".join(player_names)
        cur.execute(
            "INSERT INTO teams (name, players, value) VALUES (?,?,?)",
            (team_name, players_str, total_value),
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as exc:
        messagebox.showerror("Database Error", str(exc))


def load_team_from_db(team_name: str) -> list:
    """Load a saved team and return its player list."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT players FROM teams WHERE name = ?", (team_name,))
        row = cur.fetchone()
        conn.close()
        if row:
            return [p.strip() for p in row["players"].split(",") if p.strip()]
        return []
    except sqlite3.Error as exc:
        messagebox.showerror("Database Error", str(exc))
        return []


# ---------------------------------------------------------------------------
# Team validation
# ---------------------------------------------------------------------------

def validate_selection(selected_players: list, db_conn: sqlite3.Connection) -> tuple:
    """
    Verify the selected player list against all game rules.

    Returns (is_valid: bool, error_message: str)
    """
    if not selected_players:
        return False, "No players selected."

    if len(selected_players) > TOTAL_PLAYER_LIMIT:
        return False, f"Team cannot exceed {TOTAL_PLAYER_LIMIT} players."

    cur = db_conn.cursor()

    counts = {cat: 0 for cat in CATEGORIES}
    total_value = 0.0

    for name in selected_players:
        cur.execute("SELECT ctg, value FROM stats WHERE player = ?", (name,))
        row = cur.fetchone()
        if not row:
            return False, f"Player '{name}' not found in database."
        counts[row["ctg"]] += 1
        total_value += row["value"]

    for cat, (mn, mx) in SELECTION_RULES.items():
        n = counts[cat]
        if n < mn or n > mx:
            return False, (
                f"Invalid {cat} count: {n}. "
                f"Required between {mn} and {mx}."
            )

    if total_value > TOTAL_POINTS_BUDGET:
        return False, (
            f"Total player value {total_value:.1f} exceeds "
            f"budget of {TOTAL_POINTS_BUDGET}."
        )

    return True, ""


# ---------------------------------------------------------------------------
# GUI Application
# ---------------------------------------------------------------------------

class FantasyCricketApp(tk.Tk):
    """Main application window for Fantasy Cricket."""

    def __init__(self):
        super().__init__()

        # Ensure DB exists
        if not os.path.exists(DB_PATH):
            build_database()

        self.title("Fantasy Cricket")
        self.geometry("960x640")
        self.resizable(True, True)
        self.configure(bg=COLORS["bg"])

        # State
        self.team_name = tk.StringVar(value="")
        self.selected_category = tk.StringVar(value=CATEGORIES[0])
        self.selection_enabled = False

        # Player data in memory
        self._all_players: dict = {}   # name -> value
        self._selected_players: list = []

        self._build_menu()
        self._build_ui()
        self._refresh_points_display()

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self):
        menubar = tk.Menu(self, bg=COLORS["panel"], fg=COLORS["text"],
                          activebackground=COLORS["accent"],
                          activeforeground=COLORS["bg"])

        manage = tk.Menu(menubar, tearoff=0, bg=COLORS["panel"],
                         fg=COLORS["text"],
                         activebackground=COLORS["accent"],
                         activeforeground=COLORS["bg"])
        manage.add_command(label="New Team",  command=self._new_team)
        manage.add_command(label="Open Team", command=self._open_team)
        manage.add_separator()
        manage.add_command(label="Save Team", command=self._save_team)
        menubar.add_cascade(label="Manage Teams", menu=manage)

        score_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["panel"],
                             fg=COLORS["text"],
                             activebackground=COLORS["accent"],
                             activeforeground=COLORS["bg"])
        score_menu.add_command(label="Evaluate Score", command=self._evaluate_score)
        menubar.add_cascade(label="Score", menu=score_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["panel"],
                            fg=COLORS["text"],
                            activebackground=COLORS["accent"],
                            activeforeground=COLORS["bg"])
        help_menu.add_command(label="Rules", command=self._show_rules)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    # ------------------------------------------------------------------
    # Main UI layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ---- Header ----
        header = tk.Frame(self, bg=COLORS["bg"], pady=10)
        header.pack(fill=tk.X, padx=10)

        tk.Label(header, text="🏏  Fantasy Cricket",
                 font=("Helvetica", 22, "bold"),
                 bg=COLORS["bg"], fg=COLORS["accent"]).pack(side=tk.LEFT)

        self.team_label = tk.Label(header, textvariable=self.team_name,
                                   font=("Helvetica", 14),
                                   bg=COLORS["bg"], fg=COLORS["subtext"])
        self.team_label.pack(side=tk.RIGHT, padx=10)

        # ---- Category radio buttons ----
        cat_frame = tk.Frame(self, bg=COLORS["panel"], padx=10, pady=6)
        cat_frame.pack(fill=tk.X, padx=10, pady=(0, 4))

        tk.Label(cat_frame, text="Category:", font=("Helvetica", 11, "bold"),
                 bg=COLORS["panel"], fg=COLORS["text"]).pack(side=tk.LEFT, padx=(0, 10))

        for cat in CATEGORIES:
            rb = tk.Radiobutton(
                cat_frame, text=cat, value=cat,
                variable=self.selected_category,
                command=self._on_category_change,
                bg=COLORS["panel"], fg=COLORS["text"],
                selectcolor=COLORS["bg"],
                activebackground=COLORS["panel"],
                activeforeground=COLORS["accent"],
                font=("Helvetica", 10),
            )
            rb.pack(side=tk.LEFT, padx=8)

        # ---- Two list boxes ----
        lists_frame = tk.Frame(self, bg=COLORS["bg"])
        lists_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        # Available players
        left_frame = tk.LabelFrame(lists_frame, text="Available Players",
                                   bg=COLORS["panel"], fg=COLORS["accent"],
                                   font=("Helvetica", 11, "bold"),
                                   padx=6, pady=6)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.available_list = tk.Listbox(
            left_frame, bg=COLORS["listbg"], fg=COLORS["text"],
            selectbackground=COLORS["highlight"],
            font=("Helvetica", 11), activestyle="none",
            height=18,
        )
        self.available_list.pack(fill=tk.BOTH, expand=True)
        self.available_list.bind("<Double-Button-1>", self._add_player)

        av_scroll = ttk.Scrollbar(left_frame, command=self.available_list.yview)
        av_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.available_list.config(yscrollcommand=av_scroll.set)

        # Centre buttons
        btn_col = tk.Frame(lists_frame, bg=COLORS["bg"])
        btn_col.grid(row=0, column=1, padx=4)

        tk.Button(btn_col, text="Add ▶", command=self._add_player,
                  bg=COLORS["btn"], fg=COLORS["btn_text"],
                  font=("Helvetica", 10, "bold"), relief=tk.FLAT,
                  padx=8, pady=4).pack(pady=6)

        tk.Button(btn_col, text="◀ Remove", command=self._remove_player,
                  bg=COLORS["error"], fg=COLORS["btn_text"],
                  font=("Helvetica", 10, "bold"), relief=tk.FLAT,
                  padx=8, pady=4).pack(pady=6)

        # Selected players
        right_frame = tk.LabelFrame(lists_frame, text="Selected Players",
                                    bg=COLORS["panel"], fg=COLORS["accent"],
                                    font=("Helvetica", 11, "bold"),
                                    padx=6, pady=6)
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        self.selected_list = tk.Listbox(
            right_frame, bg=COLORS["listbg"], fg=COLORS["text"],
            selectbackground=COLORS["highlight"],
            font=("Helvetica", 11), activestyle="none",
            height=18,
        )
        self.selected_list.pack(fill=tk.BOTH, expand=True)
        self.selected_list.bind("<Double-Button-1>", self._remove_player)

        sel_scroll = ttk.Scrollbar(right_frame, command=self.selected_list.yview)
        sel_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_list.config(yscrollcommand=sel_scroll.set)

        lists_frame.columnconfigure(0, weight=1)
        lists_frame.columnconfigure(1, weight=0)
        lists_frame.columnconfigure(2, weight=1)
        lists_frame.rowconfigure(0, weight=1)

        # ---- Points footer ----
        footer = tk.Frame(self, bg=COLORS["panel"], pady=6)
        footer.pack(fill=tk.X, padx=10, pady=(4, 8))

        self.pts_available_lbl = tk.Label(
            footer, text="Points Available: 100.0",
            bg=COLORS["panel"], fg=COLORS["text"],
            font=("Helvetica", 11))
        self.pts_available_lbl.pack(side=tk.LEFT, padx=20)

        self.pts_used_lbl = tk.Label(
            footer, text="Points Used: 0.0",
            bg=COLORS["panel"], fg=COLORS["accent"],
            font=("Helvetica", 11, "bold"))
        self.pts_used_lbl.pack(side=tk.LEFT, padx=20)

        self.player_count_lbl = tk.Label(
            footer, text="Players: 0 / 11",
            bg=COLORS["panel"], fg=COLORS["subtext"],
            font=("Helvetica", 11))
        self.player_count_lbl.pack(side=tk.RIGHT, padx=20)

    # ------------------------------------------------------------------
    # Event handlers — Category
    # ------------------------------------------------------------------

    def _on_category_change(self):
        self._populate_available_list()

    def _populate_available_list(self):
        """Reload the left list with players of the selected category."""
        cat = self.selected_category.get()
        self.available_list.delete(0, tk.END)

        if not self.selection_enabled:
            self.available_list.insert(tk.END, "(Create a new team to begin)")
            return

        players = fetch_players_by_category(cat)
        self._all_players = {name: val for name, val in players}

        for name, val in players:
            if name not in self._selected_players:
                self.available_list.insert(tk.END, f"{name}  [val: {val}]")

    # ------------------------------------------------------------------
    # Event handlers — Player selection
    # ------------------------------------------------------------------

    def _add_player(self, event=None):
        if not self.selection_enabled:
            messagebox.showinfo("Info", "Please create a new team first.")
            return

        selection = self.available_list.curselection()
        if not selection:
            return

        item_text = self.available_list.get(selection[0])
        player_name = item_text.split("  [val:")[0].strip()

        if player_name in self._selected_players:
            return

        # Temp check — will full validate on save; give real-time feedback
        if len(self._selected_players) >= TOTAL_PLAYER_LIMIT:
            messagebox.showwarning(
                "Selection Error",
                f"A team can have at most {TOTAL_PLAYER_LIMIT} players.",
            )
            return

        player_value = self._all_players.get(player_name, 0)
        used = sum(self._all_players.get(p, 0) for p in self._selected_players)
        if used + player_value > TOTAL_POINTS_BUDGET:
            messagebox.showwarning(
                "Selection Error",
                f"Adding {player_name} would exceed the {TOTAL_POINTS_BUDGET} point budget.",
            )
            return

        self._selected_players.append(player_name)
        self.selected_list.insert(tk.END, f"{player_name}  [val: {player_value}]")
        self.available_list.delete(selection[0])
        self._refresh_points_display()

    def _remove_player(self, event=None):
        if not self.selection_enabled:
            return

        selection = self.selected_list.curselection()
        if not selection:
            return

        item_text = self.selected_list.get(selection[0])
        player_name = item_text.split("  [val:")[0].strip()

        self._selected_players.remove(player_name)
        self.selected_list.delete(selection[0])
        self._populate_available_list()    # refresh available with the removed player
        self._refresh_points_display()

    # ------------------------------------------------------------------
    # Points display
    # ------------------------------------------------------------------

    def _refresh_points_display(self):
        used = sum(self._all_players.get(p, 0) for p in self._selected_players)
        available = TOTAL_POINTS_BUDGET - used
        count = len(self._selected_players)

        self.pts_used_lbl.config(text=f"Points Used: {used:.1f}")
        self.pts_available_lbl.config(text=f"Points Available: {available:.1f}")
        self.player_count_lbl.config(text=f"Players: {count} / {TOTAL_PLAYER_LIMIT}")

    # ------------------------------------------------------------------
    # Menu actions
    # ------------------------------------------------------------------

    def _new_team(self):
        name = simpledialog.askstring(
            "New Team", "Enter your team name:",
            parent=self,
        )
        if not name or not name.strip():
            return

        self.team_name.set(f"Team: {name.strip()}")
        self._selected_players.clear()
        self.selected_list.delete(0, tk.END)
        self.selection_enabled = True
        self._populate_available_list()
        self._refresh_points_display()

    def _open_team(self):
        teams = fetch_saved_teams()
        if not teams:
            messagebox.showinfo("Open Team", "No saved teams found.")
            return

        dialog = _TeamChooser(self, "Open Team", teams)
        chosen = dialog.result
        if not chosen:
            return

        players = load_team_from_db(chosen)
        if not players:
            messagebox.showerror("Error", f"Could not load team '{chosen}'.")
            return

        self.team_name.set(f"Team: {chosen}")
        self._selected_players = players
        self.selection_enabled = True

        # Rebuild _all_players from DB for all categories
        self._all_players = {}
        for cat in CATEGORIES:
            self._all_players.update(
                {name: val for name, val in fetch_players_by_category(cat)}
            )

        # Refresh selected list widget
        self.selected_list.delete(0, tk.END)
        for p in self._selected_players:
            val = self._all_players.get(p, 0)
            self.selected_list.insert(tk.END, f"{p}  [val: {val}]")

        self._populate_available_list()
        self._refresh_points_display()

    def _save_team(self):
        if not self.selection_enabled or not self._selected_players:
            messagebox.showinfo("Save Team", "No players selected to save.")
            return

        conn = get_db_connection()
        is_valid, msg = validate_selection(self._selected_players, conn)
        conn.close()

        if not is_valid:
            messagebox.showwarning("Selection Error", msg)
            return

        name = self.team_name.get().replace("Team: ", "").strip()
        if not name:
            name = simpledialog.askstring("Save Team", "Enter team name:", parent=self)
            if not name:
                return

        used_value = sum(self._all_players.get(p, 0) for p in self._selected_players)
        save_team_to_db(name, self._selected_players, used_value)
        messagebox.showinfo("Saved", f"Team '{name}' saved successfully!")

    def _evaluate_score(self):
        teams = fetch_saved_teams()
        if not teams:
            messagebox.showinfo("Evaluate Score", "No saved teams. Save a team first.")
            return

        matches = fetch_match_names()
        if not matches:
            messagebox.showinfo("Evaluate Score", "No match data found in database.")
            return

        dialog = _EvaluateDialog(self, teams, matches)
        if not dialog.result:
            return

        team_name, match_name = dialog.result
        player_names = load_team_from_db(team_name)

        if not player_names:
            messagebox.showerror("Error", "Could not load team players.")
            return

        conn = get_db_connection()
        result = calculate_team_score(player_names, match_name, conn)
        conn.close()

        _show_score_report(self, team_name, match_name, result)

    def _show_rules(self):
        rules = (
            "Batting Rules\n"
            "─────────────\n"
            "• 1 point per 2 runs scored\n"
            "• +5 for a half-century (50+ runs)\n"
            "• +10 for a century (100+ runs)\n"
            "• +2 if strike-rate is 80–100\n"
            "• +4 if strike-rate > 100\n"
            "• +1 per four, +2 per six\n\n"
            "Bowling Rules\n"
            "─────────────\n"
            "• 10 points per wicket\n"
            "• +5 bonus for 3 wickets in an innings\n"
            "• +10 bonus for 5+ wickets\n"
            "• +4 if economy 3.5–4.5\n"
            "• +7 if economy 2.0–3.5\n"
            "• +10 if economy < 2.0\n\n"
            "Fielding Rules\n"
            "──────────────\n"
            "• 10 points each: catch / stumping / run-out\n\n"
            "Team Rules\n"
            "──────────\n"
            "• Exactly 11 players total\n"
            "• 3–5 Batsmen\n"
            "• 3–5 Bowlers\n"
            "• 1–3 All-Rounders\n"
            "• 1–2 Wicket-Keepers\n"
            "• Total player value ≤ 100 points"
        )
        messagebox.showinfo("Scoring Rules", rules)


# ---------------------------------------------------------------------------
# Helper dialogs
# ---------------------------------------------------------------------------

class _TeamChooser(tk.Toplevel):
    """Simple dialog to choose a saved team by name."""

    def __init__(self, parent, title, team_names):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        self.result = None

        tk.Label(self, text="Select a saved team:",
                 bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Helvetica", 12)).pack(padx=20, pady=(15, 5))

        self._var = tk.StringVar(value=team_names[0])
        for t in team_names:
            tk.Radiobutton(self, text=t, value=t, variable=self._var,
                           bg=COLORS["bg"], fg=COLORS["text"],
                           selectcolor=COLORS["panel"],
                           activebackground=COLORS["bg"],
                           font=("Helvetica", 11)).pack(anchor=tk.W, padx=30)

        btn_frame = tk.Frame(self, bg=COLORS["bg"])
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="Open", command=self._ok,
                  bg=COLORS["btn"], fg=COLORS["btn_text"],
                  font=("Helvetica", 10, "bold"), relief=tk.FLAT,
                  padx=12).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Cancel", command=self.destroy,
                  bg=COLORS["error"], fg=COLORS["btn_text"],
                  font=("Helvetica", 10, "bold"), relief=tk.FLAT,
                  padx=12).pack(side=tk.LEFT, padx=6)

        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def _ok(self):
        self.result = self._var.get()
        self.destroy()


class _EvaluateDialog(tk.Toplevel):
    """Dialog to select team + match for score evaluation."""

    def __init__(self, parent, team_names, match_names):
        super().__init__(parent)
        self.title("Evaluate Score")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])
        self.result = None

        tk.Label(self, text="Select Team:",
                 bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Helvetica", 11, "bold")).grid(row=0, column=0, sticky=tk.W,
                                                     padx=20, pady=(15, 4))

        self._team_var = tk.StringVar(value=team_names[0])
        team_combo = ttk.Combobox(self, textvariable=self._team_var,
                                  values=team_names, state="readonly", width=30)
        team_combo.grid(row=0, column=1, padx=10, pady=(15, 4))

        tk.Label(self, text="Select Match:",
                 bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Helvetica", 11, "bold")).grid(row=1, column=0, sticky=tk.W,
                                                     padx=20, pady=4)

        self._match_var = tk.StringVar(value=match_names[0])
        match_combo = ttk.Combobox(self, textvariable=self._match_var,
                                   values=match_names, state="readonly", width=30)
        match_combo.grid(row=1, column=1, padx=10, pady=4)

        btn_frame = tk.Frame(self, bg=COLORS["bg"])
        btn_frame.grid(row=2, column=0, columnspan=2, pady=14)

        tk.Button(btn_frame, text="Evaluate", command=self._ok,
                  bg=COLORS["btn"], fg=COLORS["btn_text"],
                  font=("Helvetica", 10, "bold"), relief=tk.FLAT,
                  padx=12).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Cancel", command=self.destroy,
                  bg=COLORS["error"], fg=COLORS["btn_text"],
                  font=("Helvetica", 10, "bold"), relief=tk.FLAT,
                  padx=12).pack(side=tk.LEFT, padx=6)

        self.configure(bg=COLORS["bg"])
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def _ok(self):
        self.result = (self._team_var.get(), self._match_var.get())
        self.destroy()


def _show_score_report(parent, team_name, match_name, result: dict):
    """Display the evaluation result in a popup window."""
    win = tk.Toplevel(parent)
    win.title("Score Report")
    win.configure(bg=COLORS["bg"])
    win.resizable(True, True)

    tk.Label(win, text=f"Team: {team_name}",
             bg=COLORS["bg"], fg=COLORS["accent"],
             font=("Helvetica", 14, "bold")).pack(pady=(14, 2))

    tk.Label(win, text=f"Match: {match_name}",
             bg=COLORS["bg"], fg=COLORS["subtext"],
             font=("Helvetica", 11)).pack(pady=(0, 10))

    # Treeview for breakdown
    cols = ("Player", "Points")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=14)
    tree.heading("Player", text="Player")
    tree.heading("Points", text="Fantasy Points")
    tree.column("Player", width=200, anchor=tk.W)
    tree.column("Points", width=140, anchor=tk.CENTER)

    breakdown = result["breakdown"]
    for player, pts in sorted(breakdown.items(), key=lambda x: -x[1]):
        tree.insert("", tk.END, values=(player, f"{pts:.1f}"))

    tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)

    tk.Label(win,
             text=f"Total Fantasy Score: {result['total']:.1f}",
             bg=COLORS["bg"], fg=COLORS["accent"],
             font=("Helvetica", 15, "bold")).pack(pady=10)

    tk.Button(win, text="Close", command=win.destroy,
              bg=COLORS["btn"], fg=COLORS["btn_text"],
              font=("Helvetica", 10, "bold"), relief=tk.FLAT,
              padx=16).pack(pady=(0, 14))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = FantasyCricketApp()
    app.mainloop()
