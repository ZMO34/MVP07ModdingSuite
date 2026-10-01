from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from .documents import open_roster_document


POSITION_NAMES = {
    0: "Starting Pitcher",
    1: "Catcher",
    2: "First Base",
    3: "Second Base",
    4: "Third Base",
    5: "Shortstop",
    6: "Left Field",
    7: "Center Field",
    8: "Right Field",
    9: "Designated Hitter",
    10: "Pitcher / Bullpen",
}

BASIC_FIELDS = [
    "first_name",
    "last_name",
    "playerattrib_jerseynum",
    "playerattrib_bats",
    "playerattrib_throws",
    "playerattrib_primaryposition",
    "playerattrib_secondaryposition",
    "playerattrib_height",
    "playerattrib_weight",
    "playerattrib_year",
    "playerattrib_homelocation",
    "playerattrib_speed",
    "playerattrib_fielding",
    "playerattrib_range",
    "playerattrib_throwstrength",
    "playerattrib_throwaccuracy",
    "playerattrib_platediscipline",
    "playerattrib_baserunning",
    "playerattrib_durability",
    "playerattrib_battingstance",
    "playerattrib_swingtype",
    "playerattrib_ditty",
    "playerattrib_starpower",
    "playerattrib_scholarshiptenths",
    "playerattrib_attitude",
    "playerattrib_academic",
]

APPEARANCE_FIELDS = [
    "playerattrib_facemorphindex",
    "playerattrib_boneprofile",
    "playerattrib_skintone",
    "playerattrib_eyecolour",
    "playerattrib_haircolour",
    "playerattrib_sideburns",
    "playerattrib_facialhair",
    "playerattrib_captype",
    "playerattrib_capposition",
    "playerattrib_eyeprotection",
    "derived_eyeblack",
    "derived_sunglasses_style",
    "playerattrib_battinghelmet",
    "playerattrib_elbowguard",
    "playerattrib_wristbandleftarm",
    "playerattrib_wristbandrightarm",
    "playerattrib_shinguard",
    "playerattrib_socks",
    "playerattrib_catchermask",
]
BAT_FIELDS = [
    "lrattrib_contact", "lrattrib_power",
    "lrattrib_hit_ul", "lrattrib_hit_um", "lrattrib_hit_ur",
    "lrattrib_hit_cl", "lrattrib_hit_cm", "lrattrib_hit_cr",
    "lrattrib_hit_ll", "lrattrib_hit_lm", "lrattrib_hit_lr",
    "lrattrib_lf_pct", "lrattrib_cf_pct", "lrattrib_rf_pct", "lrattrib_hr_pct",
    "lrattrib_chasefb", "lrattrib_chaseslowbreak", "lrattrib_chasehardbreak",
    "lrattrib_takefb", "lrattrib_takeslowbreak", "lrattrib_takehardbreak",
    "lrattrib_missfb", "lrattrib_missslowbreak", "lrattrib_misshardbreak",
]
PITCH_FIELDS = [
    "pitchattrib_pitcher_delivery",
    "pitchattrib_stamina",
    "pitchattrib_pickoff",
    "pitchattrib_fastball_control",
    "pitchattrib_fastball_velocity",
    "pitchattrib_pitch2_type",
    "pitchattrib_pitch2_movement",
    "pitchattrib_pitch2_description",
    "pitchattrib_pitch2_control",
    "pitchattrib_pitch2_velocity",
    "pitchattrib_pitch3_type",
    "pitchattrib_pitch3_movement",
    "pitchattrib_pitch3_description",
    "pitchattrib_pitch3_control",
    "pitchattrib_pitch3_velocity",
    "pitchattrib_pitch4_type",
    "pitchattrib_pitch4_movement",
    "pitchattrib_pitch4_description",
    "pitchattrib_pitch4_control",
    "pitchattrib_pitch4_velocity",
    "pitchattrib_pitch5_type",
    "pitchattrib_pitch5_movement",
    "pitchattrib_pitch5_description",
    "pitchattrib_pitch5_control",
    "pitchattrib_pitch5_velocity",
]


class Editor(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=8)
        self.master = master
        self.doc = None
        self.path = None
        self.selected_team = 0
        self.selected_slot = 0
        self.field_vars: dict[tuple[str, str], tk.StringVar] = {}
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="Open Roster…", command=self.open_file).pack(side="left")
        ttk.Button(toolbar, text="Save As…", command=self.save_as).pack(side="left", padx=6)
        self.status = ttk.Label(toolbar, text="No roster loaded")
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
        columns = ("slot", "player", "pos", "bat_a", "bat_b", "def_a", "def_b", "pitch", "role")
        self.roster = ttk.Treeview(mid, columns=columns, show="headings", height=24)
        for col, label, width in [
            ("slot", "#", 38),
            ("player", "Player", 190),
            ("pos", "Pos", 95),
            ("bat_a", "Bat vR", 52),
            ("bat_b", "Bat vL", 52),
            ("def_a", "Def vR", 52),
            ("def_b", "Def vL", 52),
            ("pitch", "Pitch role", 70),
            ("role", "Role flags", 95),
        ]:
            self.roster.heading(col, text=label)
            self.roster.column(col, width=width, anchor="w")
        self.roster.pack(fill="both", expand=True)
        self.roster.bind("<<TreeviewSelect>>", self.on_player)

        right = ttk.Frame(body, padding=4)
        body.add(right, weight=3)

        common = ttk.LabelFrame(right, text="Roster slot", padding=8)
        common.pack(fill="x", pady=(0, 8))
        self.player_id_var = tk.StringVar()
        self.role_flags_var = tk.StringVar()
        ttk.Label(common, text="Player ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(common, textvariable=self.player_id_var, state="readonly", width=22).grid(
            row=0, column=1, sticky="ew", padx=(8, 16)
        )
        ttk.Label(common, text="Role flags").grid(row=0, column=2, sticky="w")
        ttk.Entry(common, textvariable=self.role_flags_var, width=18).grid(
            row=0, column=3, sticky="ew", padx=(8, 0)
        )
        ttk.Button(common, text="Apply Slot", command=self.apply_slot).grid(
            row=0, column=4, padx=(10, 0)
        )
        common.columnconfigure(1, weight=1)
        common.columnconfigure(3, weight=1)

        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill="both", expand=True)

        self.basic_tab = ttk.Frame(self.tabs, padding=8)
        self.r_tab = ttk.Frame(self.tabs, padding=8)
        self.l_tab = ttk.Frame(self.tabs, padding=8)
        self.pitch_tab = ttk.Frame(self.tabs, padding=8)
        self.appearance_tab = ttk.Frame(self.tabs, padding=8)
        self.save_tab = ttk.Frame(self.tabs, padding=8)
        self.team_tab = ttk.Frame(self.tabs, padding=8)

        self.tabs.add(self.basic_tab, text="Player")
        self.tabs.add(self.r_tab, text="vs RHP")
        self.tabs.add(self.l_tab, text="vs LHP")
        self.tabs.add(self.pitch_tab, text="Pitching")
        self.tabs.add(self.appearance_tab, text="Appearance")
        self.tabs.add(self.save_tab, text="Save Packed")
        self.tabs.add(self.team_tab, text="Team")

        self._make_form(self.basic_tab, "attrib.dat", BASIC_FIELDS)
        self._make_form(self.r_tab, "rhattrib.dat", BAT_FIELDS)
        self._make_form(self.l_tab, "lhattrib.dat", BAT_FIELDS)
        self._make_form(self.pitch_tab, "pitcher.dat", PITCH_FIELDS)
        self._make_form(self.appearance_tab, "attrib.dat", APPEARANCE_FIELDS)

        self.save_first = tk.StringVar()
        self.save_last = tk.StringVar()
        self.save_index = tk.StringVar()
        self.save_payload = tk.StringVar()
        for row, (label, var, state) in enumerate([
            ("first_name", self.save_first, "normal"),
            ("last_name", self.save_last, "normal"),
            ("player_index", self.save_index, "readonly"),
            ("packed_attributes_hex", self.save_payload, "readonly"),
        ]):
            ttk.Label(self.save_tab, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
            ttk.Entry(self.save_tab, textvariable=var, state=state, width=64).grid(
                row=row, column=1, sticky="ew", pady=2
            )
        self.save_tab.columnconfigure(1, weight=1)

        self._make_team_form()
        ttk.Button(right, text="Apply Current Player Changes", command=self.apply_player).pack(
            anchor="e", pady=(8, 0)
        )

    def _make_form(self, parent, table, fields):
        for row, name in enumerate(fields):
            ttk.Label(parent, text=name).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
            var = tk.StringVar()
            self.field_vars[(table, name)] = var
            ttk.Entry(parent, textvariable=var, width=28).grid(
                row=row, column=1, sticky="ew", pady=2
            )
        parent.columnconfigure(1, weight=1)

    def _make_team_form(self):
        self.team_vars = {
            k: tk.StringVar()
            for k in ("key", "name", "abbreviation", "city", "nickname")
        }
        row = 0
        for key, var in self.team_vars.items():
            ttk.Label(self.team_tab, text=key).grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=2
            )
            ttk.Entry(self.team_tab, textvariable=var, width=32).grid(
                row=row, column=1, sticky="ew", pady=2
            )
            row += 1

        self.rotation_var = tk.StringVar()
        ttk.Label(self.team_tab, text="starting rotation indexes").grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=2
        )
        ttk.Entry(self.team_tab, textvariable=self.rotation_var, width=32).grid(
            row=row, column=1, sticky="ew", pady=2
        )
        row += 1

        self.team_meta = ttk.Label(self.team_tab, text="", wraplength=520)
        self.team_meta.grid(row=row, column=0, columnspan=2, sticky="w", pady=8)
        row += 1
        ttk.Button(self.team_tab, text="Apply Team Changes", command=self.apply_team).grid(
            row=row, column=1, sticky="e"
        )
        self.team_tab.columnconfigure(1, weight=1)

    def open_file(self):
        name = filedialog.askopenfilename(
            title="Open MVP 07 roster source",
            filetypes=[
                ("Supported roster sources", "*.BIG *.bin *.sav *.zip"),
                ("DATABASE.BIG", "*.BIG"),
                ("roster.bin", "*.bin"),
                ("PS2 roster save", "*.sav"),
                ("PCSX2 save ZIP", "*.zip"),
                ("All files", "*.*"),
            ],
        )
        if not name:
            return

        try:
            self.doc = open_roster_document(Path(name))
            self.path = Path(name)
        except Exception as exc:
            messagebox.showerror("Open failed", str(exc))
            return

        self.team_list.delete(0, "end")
        for team in self.doc.teams:
            self.team_list.insert("end", f"{team.index + 1:03d}  {team.name}")

        self.team_list.selection_set(0)
        self.team_list.activate(0)
        self.status.config(
            text=f"Loaded {self.path.name} as {self.doc.source_kind} — "
                 f"{self.doc.max_roster_slots} roster slots/team"
        )
        self.load_team(0)

    def on_team(self, _=None):
        if not self.doc or not self.team_list.curselection():
            return
        self.apply_player(silent=True)
        self.load_team(self.team_list.curselection()[0])

    def load_team(self, index):
        self.selected_team = index
        team = self.doc.teams[index]
        self.team_title.config(
            text=f"{team.name} — {self.doc.max_roster_slots}-slot roster"
        )

        for key in self.team_vars:
            self.team_vars[key].set(str(getattr(team, key)))

        self.rotation_var.set(",".join(str(x) for x in team.starter_indexes))
        self.team_meta.config(
            text=(
                f"Location ID: {team.location_id}   "
                f"Conference ID: {team.conference_id}   "
                f"Division: {team.division_index}   "
                f"Asset ID: {team.asset_id}   "
                f"Unknown 3-bit value: {team.metadata_top3}   "
                f"Special bit: {team.metadata_bit0}"
            )
        )

        for item in self.roster.get_children():
            self.roster.delete(item)

        for i, slot in enumerate(team.roster):
            if slot.player_id == 0:
                player_name = "(empty)"
                pos = ""
            else:
                player_name = self.doc.player_display_name(slot.player_id)
                fields = self.doc.player_fields(slot.player_id)
                posraw = fields.get("attrib.dat", {}).get("playerattrib_primaryposition", "")
                try:
                    pos = POSITION_NAMES.get(int(posraw), posraw)
                except Exception:
                    pos = posraw

            bat_a = str(slot.batting_order_a or "")
            bat_b = str(slot.batting_order_b or "")
            def_a = str(slot.defense_a or "")
            def_b = str(slot.defense_b or "")
            pitch = slot.pitching_role or ""
            self.roster.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    i + 1,
                    player_name,
                    pos,
                    bat_a,
                    bat_b,
                    def_a,
                    def_b,
                    pitch,
                    f"0x{slot.role_flags:08X}",
                ),
            )

        self.roster.selection_set("0")
        self.roster.focus("0")
        self.load_player(0)

    def on_player(self, _=None):
        if not self.doc or not self.roster.selection():
            return
        self.apply_player(silent=True)
        self.load_player(int(self.roster.selection()[0]))

    def load_player(self, slot_index):
        self.selected_slot = slot_index
        slot = self.doc.teams[self.selected_team].roster[slot_index]
        self.player_id_var.set(f"0x{slot.player_id:08X}")
        self.role_flags_var.set(f"0x{slot.role_flags:08X}")

        for var in self.field_vars.values():
            var.set("")
        self.save_first.set("")
        self.save_last.set("")
        self.save_index.set("")
        self.save_payload.set("")

        if slot.player_id == 0:
            return

        fields = self.doc.player_fields(slot.player_id)

        for (table, field), var in self.field_vars.items():
            var.set(fields.get(table, {}).get(field, ""))

        save_fields = fields.get("save", {})
        self.save_first.set(save_fields.get("first_name", ""))
        self.save_last.set(save_fields.get("last_name", ""))
        self.save_index.set(save_fields.get("player_index", ""))
        self.save_payload.set(save_fields.get("packed_attributes_hex", ""))

    def apply_slot(self):
        if not self.doc:
            return
        team = self.doc.teams[self.selected_team]
        old = team.roster[self.selected_slot]
        try:
            role_text = self.role_flags_var.get().strip()
            role_flags = int(role_text, 0)
            team.set_roster_slot(self.selected_slot, old.player_id, role_flags)
            self.load_team(self.selected_team)
            self.roster.selection_set(str(self.selected_slot))
            self.roster.focus(str(self.selected_slot))
            self.load_player(self.selected_slot)
            self.status.config(text=f"Updated roster slot {self.selected_slot + 1}")
        except Exception as exc:
            messagebox.showerror("Slot edit failed", str(exc))

    def apply_player(self, silent=False):
        if not self.doc:
            return

        slot = self.doc.teams[self.selected_team].roster[self.selected_slot]
        if slot.player_id == 0:
            return

        changes: dict[str, dict[str, str]] = {}
        if self.doc.supports_dat_attributes:
            for (table, field), var in self.field_vars.items():
                changes.setdefault(table, {})[field] = var.get()
        elif self.doc.source_kind == ".sav":
            for (table, field), var in self.field_vars.items():
                if table in {"attrib.dat", "lhattrib.dat", "rhattrib.dat", "pitcher.dat"}:
                    changes.setdefault(table, {})[field] = var.get()

        if self.doc.source_kind == ".sav":
            changes["save"] = {
                "first_name": self.save_first.get(),
                "last_name": self.save_last.get(),
            }

        if changes:
            try:
                self.doc.set_player_fields(slot.player_id, changes)
            except Exception as exc:
                if not silent:
                    messagebox.showerror("Player edit failed", str(exc))
                return

        if not silent:
            self.status.config(text=f"Applied edits to player ID 0x{slot.player_id:08X}")

    def apply_team(self):
        if not self.doc:
            return

        team = self.doc.teams[self.selected_team]
        try:
            for key, var in self.team_vars.items():
                setattr(team, key, var.get())

            rotation = [
                int(part.strip(), 0)
                for part in self.rotation_var.get().split(",")
                if part.strip()
            ]
            team.starter_indexes = rotation

            self.team_list.delete(self.selected_team)
            self.team_list.insert(
                self.selected_team, f"{team.index + 1:03d}  {team.name}"
            )
            self.team_list.selection_set(self.selected_team)
            self.status.config(text=f"Applied edits to {team.name}")
        except Exception as exc:
            messagebox.showerror("Team edit failed", str(exc))

    def save_as(self):
        if not self.doc:
            return

        self.apply_player(silent=True)
        self.apply_team()

        source_suffix = self.path.suffix if self.path else ""
        default_ext = source_suffix if source_suffix else ".sav"
        name = filedialog.asksaveasfilename(
            title="Save modified roster",
            defaultextension=default_ext,
            filetypes=[
                ("DATABASE.BIG", "*.BIG"),
                ("roster.bin", "*.bin"),
                ("PS2 roster save", "*.sav"),
                ("PCSX2 save ZIP", "*.zip"),
                ("All files", "*.*"),
            ],
        )
        if not name:
            return

        try:
            out = Path(name)
            self.doc.save(out)
            # Re-open saved output as a structural verification.
            open_roster_document(out)
            self.status.config(text=f"Saved and verified {out.name}")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))


def main():
    root = tk.Tk()
    root.title("MVP 07 Modding Suite — Unified Roster Editor")
    root.geometry("1320x800")
    Editor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
