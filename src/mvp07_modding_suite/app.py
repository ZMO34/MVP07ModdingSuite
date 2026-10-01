from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from .model import RosterDatabase


POSITION_NAMES = {
    0: "Starting Pitcher", 1: "Catcher", 2: "First Base", 3: "Second Base",
    4: "Third Base", 5: "Shortstop", 6: "Left Field", 7: "Center Field",
    8: "Right Field", 9: "Designated Hitter", 10: "Pitcher / Bullpen",
}

BASIC_FIELDS = [
    "first_name", "last_name", "playerattrib_jerseynum", "playerattrib_bats",
    "playerattrib_throws", "playerattrib_primaryposition",
    "playerattrib_secondaryposition", "playerattrib_height", "playerattrib_weight",
    "playerattrib_year", "playerattrib_speed", "playerattrib_fielding",
    "playerattrib_range", "playerattrib_throwstrength", "playerattrib_throwaccuracy",
    "playerattrib_bunting", "playerattrib_baserunning", "playerattrib_durability",
]
BAT_FIELDS = ["lrattrib_contact", "lrattrib_power"]
PITCH_FIELDS = [
    "pitchattrib_stamina", "pitchattrib_pickoff", "pitchattrib_fastball_control",
    "pitchattrib_fastball_velocity", "pitchattrib_pitch2_type",
    "pitchattrib_pitch2_control", "pitchattrib_pitch2_velocity",
    "pitchattrib_pitch3_type", "pitchattrib_pitch3_control",
    "pitchattrib_pitch3_velocity", "pitchattrib_pitcher_delivery",
]


class Editor(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=8)
        self.master = master
        self.db = None
        self.path = None
        self.selected_team = 0
        self.selected_slot = 0
        self.field_vars = {}
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="Open DATABASE.BIG", command=self.open_file).pack(side="left")
        ttk.Button(toolbar, text="Save As…", command=self.save_as).pack(side="left", padx=6)
        self.status = ttk.Label(toolbar, text="No database loaded")
        self.status.pack(side="left", padx=12)

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body, padding=4)
        body.add(left, weight=1)
        ttk.Label(left, text="Teams").pack(anchor="w")
        self.team_list = tk.Listbox(left, exportselection=False, width=28)
        self.team_list.pack(fill="both", expand=True)
        self.team_list.bind("<<ListboxSelect>>", self.on_team)

        mid = ttk.Frame(body, padding=4)
        body.add(mid, weight=2)
        self.team_title = ttk.Label(mid, text="Roster", font=("", 12, "bold"))
        self.team_title.pack(anchor="w")
        columns = ("slot", "jersey", "player", "pos", "bat", "role")
        self.roster = ttk.Treeview(mid, columns=columns, show="headings", height=24)
        for col, label, width in [
            ("slot","#",36),("jersey","Jersey",54),("player","Player",180),
            ("pos","Pos",110),("bat","Bat",42),("role","Role flags",90)]:
            self.roster.heading(col, text=label)
            self.roster.column(col, width=width, anchor="w")
        self.roster.pack(fill="both", expand=True)
        self.roster.bind("<<TreeviewSelect>>", self.on_player)

        right = ttk.Frame(body, padding=4)
        body.add(right, weight=3)
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill="both", expand=True)
        self.basic_tab = ttk.Frame(self.tabs, padding=8)
        self.r_tab = ttk.Frame(self.tabs, padding=8)
        self.l_tab = ttk.Frame(self.tabs, padding=8)
        self.pitch_tab = ttk.Frame(self.tabs, padding=8)
        self.team_tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(self.basic_tab, text="Player")
        self.tabs.add(self.r_tab, text="vs RHP")
        self.tabs.add(self.l_tab, text="vs LHP")
        self.tabs.add(self.pitch_tab, text="Pitching")
        self.tabs.add(self.team_tab, text="Team")
        self._make_form(self.basic_tab, "attrib.dat", BASIC_FIELDS)
        self._make_form(self.r_tab, "rhattrib.dat", BAT_FIELDS)
        self._make_form(self.l_tab, "lhattrib.dat", BAT_FIELDS)
        self._make_form(self.pitch_tab, "pitcher.dat", PITCH_FIELDS)
        self._make_team_form()
        ttk.Button(right, text="Apply Current Player Changes", command=self.apply_player).pack(anchor="e", pady=(8,0))

    def _make_form(self, parent, table, fields):
        for row, name in enumerate(fields):
            ttk.Label(parent, text=name).grid(row=row, column=0, sticky="w", padx=(0,8), pady=2)
            var = tk.StringVar()
            self.field_vars[(table, name)] = var
            ttk.Entry(parent, textvariable=var, width=28).grid(row=row, column=1, sticky="ew", pady=2)
        parent.columnconfigure(1, weight=1)

    def _make_team_form(self):
        self.team_vars = {k: tk.StringVar() for k in ("key","name","abbreviation","city","nickname")}
        row = 0
        for k, var in self.team_vars.items():
            ttk.Label(self.team_tab, text=k).grid(row=row,column=0,sticky="w",padx=(0,8),pady=2)
            ttk.Entry(self.team_tab,textvariable=var,width=32).grid(row=row,column=1,sticky="ew",pady=2)
            row += 1
        self.team_meta = ttk.Label(self.team_tab, text="")
        self.team_meta.grid(row=row,column=0,columnspan=2,sticky="w",pady=8); row += 1
        ttk.Button(self.team_tab,text="Apply Team Changes",command=self.apply_team).grid(row=row,column=1,sticky="e")
        self.team_tab.columnconfigure(1,weight=1)

    def open_file(self):
        name = filedialog.askopenfilename(title="Open DATABASE.BIG", filetypes=[("BIG archives","*.BIG"),("All files","*.*")])
        if not name: return
        try:
            self.db = RosterDatabase.load(Path(name)); self.path = Path(name)
        except Exception as exc:
            messagebox.showerror("Open failed", str(exc)); return
        self.team_list.delete(0,"end")
        for t in self.db.teams:
            self.team_list.insert("end", f"{t.index+1:03d}  {t.name}")
        self.team_list.selection_set(0); self.team_list.activate(0)
        self.status.config(text=f"Loaded {self.path.name} — 152 teams")
        self.load_team(0)

    def on_team(self, _=None):
        if not self.db or not self.team_list.curselection(): return
        self.apply_player(silent=True)
        self.load_team(self.team_list.curselection()[0])

    def load_team(self, idx):
        self.selected_team = idx
        team = self.db.teams[idx]
        self.team_title.config(text=f"{team.name} — 25-player roster")
        for k in self.team_vars: self.team_vars[k].set(str(getattr(team,k)))
        self.team_meta.config(text=f"Location ID: {team.location_id}   Conference ID: {team.conference_id}   Division: {team.division_index}   Asset ID: {team.asset_id}   Unknown 3-bit value: {team.metadata_top3}   Special bit: {team.metadata_bit0}   Starters: {team.starter_indexes}")
        for item in self.roster.get_children(): self.roster.delete(item)
        amap = self.db.tables["attrib.dat"].by_numeric_key()
        inv = {v:k for k,v in self.db.tables["attrib.dat"].fields.items()}
        for i, slot in enumerate(team.roster):
            vals = amap.get(slot.player_id,{})
            first = vals.get(inv.get("first_name",-1),"")
            last = vals.get(inv.get("last_name",-1),"")
            jersey = vals.get(inv.get("playerattrib_jerseynum",-1),"")
            posraw = vals.get(inv.get("playerattrib_primaryposition",-1),"")
            try: pos = POSITION_NAMES.get(int(posraw),posraw)
            except Exception: pos = posraw
            bat = str(slot.inferred_batting_order or "")
            self.roster.insert("", "end", iid=str(i), values=(i+1, jersey, f"{first} {last}".strip(), pos, bat, f"0x{slot.role_flags:08X}"))
        self.roster.selection_set("0"); self.roster.focus("0"); self.load_player(0)

    def on_player(self, _=None):
        if not self.db or not self.roster.selection(): return
        self.apply_player(silent=True)
        self.load_player(int(self.roster.selection()[0]))

    def load_player(self, slot_index):
        self.selected_slot = slot_index
        pid = self.db.teams[self.selected_team].roster[slot_index].player_id
        for (table, field), var in self.field_vars.items():
            tab = self.db.tables[table]
            inv = {v:k for k,v in tab.fields.items()}
            vals = tab.by_numeric_key().get(pid)
            var.set("" if vals is None or field not in inv else vals.get(inv[field],""))

    def apply_player(self, silent=False):
        if not self.db: return
        pid = self.db.teams[self.selected_team].roster[self.selected_slot].player_id
        for (table, field), var in self.field_vars.items():
            tab = self.db.tables[table]
            inv = {v:k for k,v in tab.fields.items()}
            vals = tab.by_numeric_key().get(pid)
            if vals is not None and field in inv:
                vals[inv[field]] = var.get()
        if not silent:
            self.status.config(text=f"Applied edits to player ID 0x{pid:08X}")

    def apply_team(self):
        if not self.db: return
        t = self.db.teams[self.selected_team]
        try:
            for k,var in self.team_vars.items():
                setattr(t,k,var.get())
            self.team_list.delete(self.selected_team)
            self.team_list.insert(self.selected_team, f"{t.index+1:03d}  {t.name}")
            self.team_list.selection_set(self.selected_team)
            self.status.config(text=f"Applied edits to {t.name}")
        except Exception as exc:
            messagebox.showerror("Team edit failed", str(exc))

    def save_as(self):
        if not self.db: return
        self.apply_player(silent=True); self.apply_team()
        name = filedialog.asksaveasfilename(title="Save modified DATABASE.BIG", defaultextension=".BIG", filetypes=[("BIG archives","*.BIG")])
        if not name: return
        try:
            self.db.save(Path(name))
            RosterDatabase.load(Path(name))
            self.status.config(text=f"Saved and verified {Path(name).name}")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))


def main():
    root = tk.Tk()
    root.title("MVP 07 Modding Suite — Roster Editor")
    root.geometry("1280x760")
    Editor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
