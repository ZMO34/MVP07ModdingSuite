from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import copy
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .csv_io import export_roster_csv, import_roster_csv
from .documents import open_roster_document
from .ui_schema import field_spec, validate_field_value


POSITION_NAMES = {
    0: "P", 1: "C", 2: "1B", 3: "2B", 4: "3B", 5: "SS",
    6: "LF", 7: "CF", 8: "RF", 9: "DH", 10: "P/Bullpen",
}

BASIC_FIELDS = [
    "first_name", "last_name", "playerattrib_jerseynum", "playerattrib_bats",
    "playerattrib_throws", "playerattrib_primaryposition", "playerattrib_secondaryposition",
    "playerattrib_height", "playerattrib_weight", "playerattrib_year",
    "playerattrib_homelocation", "playerattrib_speed", "playerattrib_fielding",
    "playerattrib_range", "playerattrib_throwstrength", "playerattrib_throwaccuracy",
    "playerattrib_bunting", "playerattrib_platediscipline", "playerattrib_baserunning",
    "playerattrib_durability", "playerattrib_battingstance", "playerattrib_swingtype",
    "playerattrib_ditty", "playerattrib_starpower", "playerattrib_scholarshiptenths",
    "playerattrib_attitude", "playerattrib_academic",
]

APPEARANCE_FIELDS = [
    "playerattrib_facemorphindex", "playerattrib_boneprofile", "playerattrib_skintone",
    "playerattrib_eyecolour", "playerattrib_haircolour", "playerattrib_sideburns",
    "playerattrib_facialhair", "playerattrib_captype", "playerattrib_capposition",
    "derived_eyeblack", "derived_sunglasses_style", "playerattrib_battinghelmet",
    "playerattrib_elbowguard", "playerattrib_wristbandleftarm",
    "playerattrib_wristbandrightarm", "playerattrib_shinguard", "playerattrib_socks",
    "playerattrib_catchermask",
]

BAT_FIELDS = [
    "lrattrib_contact", "lrattrib_power",
    "lrattrib_hit_ul", "lrattrib_hit_um", "lrattrib_hit_ur",
    "lrattrib_hit_cl", "lrattrib_hit_cm", "lrattrib_hit_cr",
    "lrattrib_hit_ll", "lrattrib_hit_lm", "lrattrib_hit_lr",
    "lrattrib_lf_pct", "lrattrib_cf_pct", "lrattrib_rf_pct", "lrattrib_hr_pct",
    "lrattrib_fb_pct", "lrattrib_ld_pct", "lrattrib_gb_pct",
    "lrattrib_chasefb", "lrattrib_chaseslowbreak", "lrattrib_chasehardbreak",
    "lrattrib_takefb", "lrattrib_takeslowbreak", "lrattrib_takehardbreak",
    "lrattrib_missfb", "lrattrib_missslowbreak", "lrattrib_misshardbreak",
]

PITCH_FIELDS = [
    "pitchattrib_pitcher_delivery", "pitchattrib_stamina", "pitchattrib_pickoff",
    "pitchattrib_fastball_control", "pitchattrib_fastball_velocity",
    "pitchattrib_pitch2_type", "pitchattrib_pitch2_movement",
    "pitchattrib_pitch2_description", "pitchattrib_pitch2_control",
    "pitchattrib_pitch2_velocity", "pitchattrib_pitch3_type",
    "pitchattrib_pitch3_movement", "pitchattrib_pitch3_description",
    "pitchattrib_pitch3_control", "pitchattrib_pitch3_velocity",
    "pitchattrib_pitch4_type", "pitchattrib_pitch4_movement",
    "pitchattrib_pitch4_description", "pitchattrib_pitch4_control",
    "pitchattrib_pitch4_velocity", "pitchattrib_pitch5_type",
    "pitchattrib_pitch5_movement", "pitchattrib_pitch5_description",
    "pitchattrib_pitch5_control", "pitchattrib_pitch5_velocity",
]


@dataclass
class FieldBinding:
    table: str
    field: str
    variable: tk.StringVar
    widget: tk.Widget
    original_table: str = ""
    original_raw: str = ""


class ScrollableFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(
            self, highlightthickness=0, borderwidth=0, background="#FFFFFF"
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas, padding=(14, 12))
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.inner.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.window, width=e.width),
        )
        self.canvas.bind(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )


class Editor(ttk.Frame):
    HISTORY_LIMIT = 30

    def __init__(self, master: tk.Tk):
        super().__init__(master, style="App.TFrame")
        self.master = master
        self.doc = None
        self.path: Path | None = None
        self.selected_team = 0
        self.selected_slot = 0
        self.visible_team_indexes: list[int] = []
        self.visible_slot_indexes: list[int] = []
        self.field_bindings: dict[tuple[str, str], FieldBinding] = {}
        self.team_vars: dict[str, tk.StringVar] = {}
        self.team_original: dict[str, str] = {}
        self.rotation_vars = [tk.StringVar() for _ in range(3)]
        self.rotation_choice_to_index: dict[str, int] = {}
        self.rotation_original: tuple[int, int, int] | None = None
        self.undo_stack: list[tuple[object, str]] = []
        self.redo_stack: list[tuple[object, str]] = []
        self.dirty = False
        self._loading = False

        self._configure_window()
        self._configure_styles()
        self.pack(fill="both", expand=True)
        self._build()
        self._bind_shortcuts()
        self._update_history_buttons()
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_window(self):
        self.master.title("MVP 07 Modding Suite — Roster Editor")
        self.master.geometry("1500x900")
        self.master.minsize(1180, 720)
        self.master.configure(background="#F4F6F8")

    def _configure_styles(self):
        style = ttk.Style(self.master)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("App.TFrame", background="#F4F6F8")
        style.configure("Surface.TFrame", background="#FFFFFF")
        style.configure("Toolbar.TFrame", background="#172033")
        style.configure(
            "Toolbar.TLabel", background="#172033", foreground="#FFFFFF"
        )
        style.configure(
            "Title.Toolbar.TLabel", font=("TkDefaultFont", 15, "bold")
        )
        style.configure("Muted.Toolbar.TLabel", foreground="#C7CFDB")
        style.configure(
            "PanelTitle.TLabel", font=("TkDefaultFont", 11, "bold")
        )
        style.configure(
            "PlayerTitle.TLabel", font=("TkDefaultFont", 14, "bold")
        )
        style.configure("Muted.TLabel", foreground="#667085")
        style.configure(
            "Status.TLabel",
            background="#EEF1F5",
            foreground="#475467",
            padding=(10, 6),
        )
        style.configure(
            "Accent.TButton", font=("TkDefaultFont", 9, "bold")
        )
        style.configure("Treeview", rowheight=28, font=("TkDefaultFont", 9))
        style.configure(
            "Treeview.Heading", font=("TkDefaultFont", 9, "bold")
        )
        style.map(
            "Treeview",
            background=[("selected", "#DDEAFE")],
            foreground=[("selected", "#172033")],
        )
        style.configure("TNotebook.Tab", padding=(12, 7))

    def _build(self):
        self._build_toolbar()
        content = ttk.Frame(
            self, style="App.TFrame", padding=(12, 12, 12, 6)
        )
        content.pack(fill="both", expand=True)
        body = ttk.Panedwindow(content, orient="horizontal")
        body.pack(fill="both", expand=True)
        self._build_team_panel(body)
        self._build_roster_panel(body)
        self._build_editor_panel(body)
        self.status = ttk.Label(
            self,
            text="Open a roster source to begin.",
            style="Status.TLabel",
            anchor="w",
        )
        self.status.pack(fill="x", side="bottom")

    def _build_toolbar(self):
        bar = ttk.Frame(self, style="Toolbar.TFrame", padding=(14, 10))
        bar.pack(fill="x")

        title = ttk.Frame(bar, style="Toolbar.TFrame")
        title.pack(side="left", padx=(0, 22))
        ttk.Label(
            title, text="MVP 07", style="Title.Toolbar.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            title, text="Roster Editor", style="Muted.Toolbar.TLabel"
        ).pack(anchor="w")

        ttk.Button(bar, text="Open…", command=self.open_file).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(bar, text="Save As…", command=self.save_as).pack(
            side="left", padx=(0, 14)
        )
        ttk.Separator(bar, orient="vertical").pack(
            side="left", fill="y", padx=(0, 14)
        )
        ttk.Button(bar, text="Import CSV…", command=self.import_csv).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(bar, text="Export CSV…", command=self.export_csv).pack(
            side="left", padx=(0, 14)
        )
        ttk.Separator(bar, orient="vertical").pack(
            side="left", fill="y", padx=(0, 14)
        )
        self.undo_button = ttk.Button(bar, text="Undo", command=self.undo)
        self.undo_button.pack(side="left", padx=(0, 6))
        self.redo_button = ttk.Button(bar, text="Redo", command=self.redo)
        self.redo_button.pack(side="left")

        self.dirty_label = ttk.Label(
            bar, text="", style="Muted.Toolbar.TLabel"
        )
        self.dirty_label.pack(side="right", padx=(12, 0))
        self.source_label = ttk.Label(
            bar, text="No file loaded", style="Muted.Toolbar.TLabel"
        )
        self.source_label.pack(side="right")

    def _build_team_panel(self, body):
        panel = ttk.Frame(body, style="Surface.TFrame", padding=12)
        body.add(panel, weight=1)
        ttk.Label(
            panel, text="Teams", style="PanelTitle.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            panel,
            text="Search school, city, nickname, or key",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 8))

        row = ttk.Frame(panel, style="Surface.TFrame")
        row.pack(fill="x", pady=(0, 8))
        self.team_search = tk.StringVar()
        self.team_search_entry = ttk.Entry(row, textvariable=self.team_search)
        self.team_search_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(
            row, text="×", width=3, command=lambda: self.team_search.set("")
        ).pack(side="left", padx=(4, 0))
        self.team_search.trace_add(
            "write", lambda *_: self.refresh_team_list()
        )

        wrap = ttk.Frame(panel, style="Surface.TFrame")
        wrap.pack(fill="both", expand=True)
        self.team_list = tk.Listbox(
            wrap,
            exportselection=False,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#D0D5DD",
            selectbackground="#DDEAFE",
            selectforeground="#172033",
            background="#FFFFFF",
            activestyle="none",
            font=("TkDefaultFont", 9),
        )
        scroll = ttk.Scrollbar(
            wrap, orient="vertical", command=self.team_list.yview
        )
        self.team_list.configure(yscrollcommand=scroll.set)
        self.team_list.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.team_list.bind("<<ListboxSelect>>", self.on_team)

    def _build_roster_panel(self, body):
        panel = ttk.Frame(body, style="Surface.TFrame", padding=12)
        body.add(panel, weight=3)
        self.team_title = ttk.Label(
            panel, text="Roster", style="PanelTitle.TLabel"
        )
        self.team_title.pack(anchor="w")
        self.team_subtitle = ttk.Label(
            panel, text="", style="Muted.TLabel"
        )
        self.team_subtitle.pack(anchor="w", pady=(2, 8))

        row = ttk.Frame(panel, style="Surface.TFrame")
        row.pack(fill="x", pady=(0, 8))
        self.player_search = tk.StringVar()
        self.player_search_entry = ttk.Entry(
            row, textvariable=self.player_search
        )
        self.player_search_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(
            row, text="×", width=3, command=lambda: self.player_search.set("")
        ).pack(side="left", padx=(4, 0))
        self.player_search.trace_add(
            "write", lambda *_: self.refresh_roster()
        )

        wrap = ttk.Frame(panel, style="Surface.TFrame")
        wrap.pack(fill="both", expand=True)
        columns = (
            "slot", "player", "pos", "bats", "throws",
            "bat_r", "bat_l", "def_r", "def_l", "pitch",
        )
        self.roster = ttk.Treeview(
            wrap, columns=columns, show="headings", selectmode="browse"
        )
        setup = [
            ("slot", "#", 34, "center"),
            ("player", "Player", 180, "w"),
            ("pos", "Pos", 58, "center"),
            ("bats", "B", 34, "center"),
            ("throws", "T", 34, "center"),
            ("bat_r", "vR", 38, "center"),
            ("bat_l", "vL", 38, "center"),
            ("def_r", "D-R", 42, "center"),
            ("def_l", "D-L", 42, "center"),
            ("pitch", "Pitch role", 72, "center"),
        ]
        for col, label, width, anchor in setup:
            self.roster.heading(col, text=label)
            self.roster.column(
                col,
                width=width,
                minwidth=width,
                anchor=anchor,
                stretch=col == "player",
            )
        scroll = ttk.Scrollbar(
            wrap, orient="vertical", command=self.roster.yview
        )
        self.roster.configure(yscrollcommand=scroll.set)
        self.roster.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.roster.bind("<<TreeviewSelect>>", self.on_player)

    def _build_editor_panel(self, body):
        panel = ttk.Frame(body, style="Surface.TFrame", padding=12)
        body.add(panel, weight=4)

        header = ttk.Frame(panel, style="Surface.TFrame")
        header.pack(fill="x", pady=(0, 8))
        title_box = ttk.Frame(header, style="Surface.TFrame")
        title_box.pack(side="left", fill="x", expand=True)
        self.player_title = ttk.Label(
            title_box, text="Player details", style="PlayerTitle.TLabel"
        )
        self.player_title.pack(anchor="w")
        self.player_meta = ttk.Label(
            title_box, text="Select a player", style="Muted.TLabel"
        )
        self.player_meta.pack(anchor="w", pady=(2, 0))
        ttk.Button(
            header,
            text="Apply Player",
            command=self.apply_player,
            style="Accent.TButton",
        ).pack(side="right")

        slot = ttk.LabelFrame(panel, text="Roster slot", padding=8)
        slot.pack(fill="x", pady=(0, 8))
        self.player_id_var = tk.StringVar()
        self.role_flags_var = tk.StringVar()
        ttk.Label(slot, text="Player ID").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Entry(
            slot,
            textvariable=self.player_id_var,
            state="readonly",
            width=18,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 16))
        ttk.Label(slot, text="Role flags").grid(
            row=0, column=2, sticky="w"
        )
        ttk.Entry(
            slot, textvariable=self.role_flags_var, width=18
        ).grid(row=0, column=3, sticky="ew", padx=(6, 8))
        ttk.Button(
            slot, text="Apply role", command=self.apply_slot
        ).grid(row=0, column=4)
        slot.columnconfigure(1, weight=1)
        slot.columnconfigure(3, weight=1)

        self.tabs = ttk.Notebook(panel)
        self.tabs.pack(fill="both", expand=True)

        self.basic_tab = ScrollableFrame(self.tabs)
        self.r_tab = ScrollableFrame(self.tabs)
        self.l_tab = ScrollableFrame(self.tabs)
        self.pitch_tab = ScrollableFrame(self.tabs)
        self.appearance_tab = ScrollableFrame(self.tabs)
        self.rotation_tab = ttk.Frame(self.tabs, padding=14)
        self.team_tab = ScrollableFrame(self.tabs)
        self.advanced_tab = ttk.Frame(self.tabs, padding=14)

        self.tabs.add(self.basic_tab, text="Player")
        self.tabs.add(self.r_tab, text="vs RHP")
        self.tabs.add(self.l_tab, text="vs LHP")
        self.tabs.add(self.pitch_tab, text="Pitching")
        self.tabs.add(self.appearance_tab, text="Appearance")
        self.tabs.add(self.rotation_tab, text="Rotation")
        self.tabs.add(self.team_tab, text="Team")
        self.tabs.add(self.advanced_tab, text="Advanced")

        self._make_form(self.basic_tab.inner, "attrib.dat", BASIC_FIELDS)
        self._make_form(self.r_tab.inner, "rhattrib.dat", BAT_FIELDS)
        self._make_form(self.l_tab.inner, "lhattrib.dat", BAT_FIELDS)
        self._make_form(self.pitch_tab.inner, "pitcher.dat", PITCH_FIELDS)
        self._make_form(
            self.appearance_tab.inner, "attrib.dat", APPEARANCE_FIELDS
        )
        self._make_rotation_form()
        self._make_team_form(self.team_tab.inner)
        self._make_advanced_form()

    def _make_form(self, parent, table, fields):
        parent.columnconfigure(1, weight=1)
        for row, name in enumerate(fields):
            spec = field_spec(name)
            ttk.Label(parent, text=spec.label).grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=4
            )
            var = tk.StringVar()
            if spec.choices:
                widget = ttk.Combobox(
                    parent,
                    textvariable=var,
                    values=spec.combo_values,
                    state="normal",
                )
                self._enable_autocomplete(widget)
            else:
                widget = ttk.Entry(parent, textvariable=var)
            widget.grid(row=row, column=1, sticky="ew", pady=4)
            if spec.minimum is not None or spec.maximum is not None:
                hint = (
                    " / ".join(spec.combo_values)
                    if spec.choices
                    else f"{spec.minimum if spec.minimum is not None else '…'}–"
                         f"{spec.maximum if spec.maximum is not None else '…'}"
                )
                ttk.Label(
                    parent, text=hint, style="Muted.TLabel"
                ).grid(row=row, column=2, sticky="w", padx=(8, 0))
            self.field_bindings[(table, name)] = FieldBinding(
                table, name, var, widget
            )

    def _make_rotation_form(self):
        ttk.Label(
            self.rotation_tab,
            text="Starting rotation",
            style="PanelTitle.TLabel",
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(
            self.rotation_tab,
            text="Choose the three roster slots stored by the game as starting pitchers.",
            style="Muted.TLabel",
        ).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(2, 14)
        )
        self.rotation_combos = []
        for i, var in enumerate(self.rotation_vars):
            ttk.Label(
                self.rotation_tab, text=f"Starter {i + 1}"
            ).grid(
                row=i + 2, column=0, sticky="w", padx=(0, 12), pady=6
            )
            combo = ttk.Combobox(
                self.rotation_tab, textvariable=var, state="normal"
            )
            combo.grid(row=i + 2, column=1, sticky="ew", pady=6)
            self._enable_autocomplete(combo)
            self.rotation_combos.append(combo)
        ttk.Button(
            self.rotation_tab,
            text="Apply Rotation",
            command=self.apply_rotation,
            style="Accent.TButton",
        ).grid(row=5, column=1, sticky="e", pady=(14, 0))
        self.rotation_tab.columnconfigure(1, weight=1)

    def _make_team_form(self, parent):
        parent.columnconfigure(1, weight=1)
        labels = {
            "key": "Internal key",
            "name": "School / team name",
            "abbreviation": "Abbreviation",
            "city": "City",
            "nickname": "Nickname",
        }
        for row, key in enumerate(
            ("key", "name", "abbreviation", "city", "nickname")
        ):
            var = tk.StringVar()
            self.team_vars[key] = var
            ttk.Label(parent, text=labels[key]).grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=5
            )
            ttk.Entry(parent, textvariable=var).grid(
                row=row, column=1, sticky="ew", pady=5
            )
        self.team_meta = ttk.Label(
            parent,
            text="",
            wraplength=520,
            justify="left",
            style="Muted.TLabel",
        )
        self.team_meta.grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(14, 10)
        )
        ttk.Button(
            parent,
            text="Apply Team",
            command=self.apply_team,
            style="Accent.TButton",
        ).grid(row=7, column=1, sticky="e")

    def _make_advanced_form(self):
        self.save_index = tk.StringVar()
        self.save_payload = tk.StringVar()
        ttk.Label(
            self.advanced_tab, text="Save player index"
        ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Entry(
            self.advanced_tab,
            textvariable=self.save_index,
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(
            self.advanced_tab, text="Packed attributes"
        ).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=4)
        ttk.Entry(
            self.advanced_tab,
            textvariable=self.save_payload,
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(
            self.advanced_tab,
            text="Raw diagnostics only. Unknown fields remain preserved by the backend.",
            style="Muted.TLabel",
        ).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )
        self.advanced_tab.columnconfigure(1, weight=1)

    def _bind_shortcuts(self):
        self.master.bind_all("<Control-o>", lambda _e: self.open_file())
        self.master.bind_all("<Control-s>", lambda _e: self.save_as())
        self.master.bind_all("<Control-z>", lambda _e: self.undo())
        self.master.bind_all("<Control-y>", lambda _e: self.redo())
        self.master.bind_all("<Control-Shift-Z>", lambda _e: self.redo())
        self.master.bind_all(
            "<Control-f>", lambda _e: self._focus_player_search()
        )

    def _focus_player_search(self):
        self.player_search_entry.focus_set()
        self.player_search_entry.selection_range(0, "end")
        return "break"

    def _enable_autocomplete(self, combo: ttk.Combobox):
        combo.bind(
            "<KeyRelease>",
            lambda event, c=combo: self._autocomplete(c, event),
            add="+",
        )

    @staticmethod
    def _autocomplete(combo: ttk.Combobox, event):
        if event.keysym in {
            "BackSpace", "Delete", "Left", "Right", "Home",
            "End", "Tab", "Return",
        }:
            return
        typed = combo.get()
        if not typed:
            return
        for option in combo.cget("values"):
            option = str(option)
            if option.lower().startswith(typed.lower()):
                combo.set(option)
                combo.icursor(len(typed))
                combo.selection_range(len(typed), "end")
                break

    def open_file(self):
        if self.dirty and not messagebox.askyesno(
            "Unsaved changes",
            "Discard current unsaved changes and open another file?",
        ):
            return False
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
            return False
        try:
            doc = open_roster_document(Path(name))
        except Exception as exc:
            messagebox.showerror("Open failed", str(exc))
            return False

        self.doc = doc
        self.path = Path(name)
        self.selected_team = 0
        self.selected_slot = 0
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.team_search.set("")
        self.player_search.set("")
        self._set_dirty(False)
        self.source_label.config(
            text=f"{self.path.name}  ·  {self.doc.source_kind}"
        )
        self.refresh_team_list(select_team=0)
        self.load_team(0, select_slot=0)
        self._set_status(
            f"Loaded {self.path.name} · "
            f"{self.doc.max_roster_slots} roster slots per team"
        )
        self._update_history_buttons()
        return True

    def refresh_team_list(self, select_team: int | None = None):
        if not self.doc:
            self.team_list.delete(0, "end")
            return
        query = self.team_search.get().strip().lower()
        if select_team is None:
            select_team = self.selected_team
        self._loading = True
        try:
            self.team_list.delete(0, "end")
            self.visible_team_indexes = []
            for index, team in enumerate(self.doc.teams):
                haystack = " ".join(
                    (
                        team.key,
                        team.name,
                        team.abbreviation,
                        team.city,
                        team.nickname,
                    )
                ).lower()
                if query and query not in haystack:
                    continue
                self.visible_team_indexes.append(index)
                self.team_list.insert(
                    "end", f"{index + 1:03d}   {team.name}"
                )
            if select_team in self.visible_team_indexes:
                visible = self.visible_team_indexes.index(select_team)
                self.team_list.selection_set(visible)
                self.team_list.activate(visible)
                self.team_list.see(visible)
        finally:
            self._loading = False

    def refresh_roster(self, select_slot: int | None = None):
        if not self.doc:
            return
        team = self.doc.teams[self.selected_team]
        query = self.player_search.get().strip().lower()
        if select_slot is None:
            select_slot = self.selected_slot
        self._loading = True
        try:
            for item in self.roster.get_children():
                self.roster.delete(item)
            self.visible_slot_indexes = []
            for i, slot in enumerate(team.roster):
                if slot.player_id:
                    name = self.doc.player_display_name(slot.player_id)
                    fields = self.doc.player_fields(slot.player_id)
                    attrib = fields.get("attrib.dat", {})
                    pos_raw = attrib.get(
                        "playerattrib_primaryposition", ""
                    )
                    try:
                        pos = POSITION_NAMES.get(
                            int(pos_raw), str(pos_raw)
                        )
                    except (TypeError, ValueError):
                        pos = str(pos_raw)
                    bats = field_spec(
                        "playerattrib_bats"
                    ).display_value(
                        attrib.get("playerattrib_bats", "")
                    )
                    throws = field_spec(
                        "playerattrib_throws"
                    ).display_value(
                        attrib.get("playerattrib_throws", "")
                    )
                else:
                    name, pos, bats, throws = "(empty)", "", "", ""

                haystack = (
                    f"{i + 1} {name} {pos} {bats} {throws} "
                    f"0x{slot.player_id:08x}"
                ).lower()
                if query and query not in haystack:
                    continue
                self.visible_slot_indexes.append(i)
                self.roster.insert(
                    "",
                    "end",
                    iid=str(i),
                    values=(
                        i + 1,
                        name,
                        pos,
                        bats,
                        throws,
                        slot.batting_order_a or "",
                        slot.batting_order_b or "",
                        slot.defense_a or "",
                        slot.defense_b or "",
                        slot.pitching_role or "",
                    ),
                )
            if select_slot in self.visible_slot_indexes:
                iid = str(select_slot)
                self.roster.selection_set(iid)
                self.roster.focus(iid)
                self.roster.see(iid)
            elif self.visible_slot_indexes:
                iid = str(self.visible_slot_indexes[0])
                self.roster.selection_set(iid)
                self.roster.focus(iid)
        finally:
            self._loading = False

    def on_team(self, _event=None):
        if (
            self._loading
            or not self.doc
            or not self.team_list.curselection()
        ):
            return
        visible = self.team_list.curselection()[0]
        team_index = self.visible_team_indexes[visible]
        if team_index == self.selected_team:
            return
        if not self.apply_player(silent=False):
            self.refresh_team_list(select_team=self.selected_team)
            return
        if not self.apply_team(silent=False):
            self.refresh_team_list(select_team=self.selected_team)
            return
        if not self.apply_rotation(silent=False):
            self.refresh_team_list(select_team=self.selected_team)
            return
        self.load_team(team_index, select_slot=0)

    def load_team(self, index: int, select_slot: int = 0):
        if not self.doc:
            return
        self._loading = True
        try:
            self.selected_team = index
            self.selected_slot = min(
                select_slot, self.doc.max_roster_slots - 1
            )
            team = self.doc.teams[index]
            self.team_title.config(text=team.name)
            self.team_subtitle.config(
                text=(
                    f"Team {index + 1} of {len(self.doc.teams)} · "
                    f"{self.doc.max_roster_slots}-slot "
                    f"{self.doc.source_kind} roster"
                )
            )
            self.team_original = {}
            for key, var in self.team_vars.items():
                value = str(getattr(team, key))
                var.set(value)
                self.team_original[key] = value
            self.team_meta.config(
                text=(
                    f"Location ID {team.location_id}   ·   "
                    f"Conference {team.conference_id}   ·   "
                    f"Division {team.division_index}   ·   "
                    f"Asset ID {team.asset_id}\n"
                    f"Metadata top3 {team.metadata_top3}   ·   "
                    f"Special bit {team.metadata_bit0}"
                )
            )
            self._load_rotation(team)
            self.refresh_roster(select_slot=self.selected_slot)
            self.load_player(self.selected_slot)
        finally:
            self._loading = False

    def on_player(self, _event=None):
        if (
            self._loading
            or not self.doc
            or not self.roster.selection()
        ):
            return
        slot_index = int(self.roster.selection()[0])
        if slot_index == self.selected_slot:
            return
        old = self.selected_slot
        if not self.apply_player(silent=False):
            self._loading = True
            try:
                if str(old) in self.roster.get_children():
                    self.roster.selection_set(str(old))
                    self.roster.focus(str(old))
            finally:
                self._loading = False
            return
        self.load_player(slot_index)

    def load_player(self, slot_index: int):
        if not self.doc:
            return
        self.selected_slot = slot_index
        team = self.doc.teams[self.selected_team]
        slot = team.roster[slot_index]
        self.player_id_var.set(f"0x{slot.player_id:08X}")
        self.role_flags_var.set(f"0x{slot.role_flags:08X}")
        self.save_index.set("")
        self.save_payload.set("")

        for binding in self.field_bindings.values():
            binding.variable.set("")
            binding.original_table = binding.table
            binding.original_raw = ""

        if not slot.player_id:
            self.player_title.config(text="Empty roster slot")
            self.player_meta.config(text=f"Slot {slot_index + 1}")
            return

        name = self.doc.player_display_name(slot.player_id)
        self.player_title.config(text=name)
        self.player_meta.config(
            text=(
                f"Slot {slot_index + 1} · "
                f"Player ID 0x{slot.player_id:08X}"
            )
        )
        fields = self.doc.player_fields(slot.player_id)
        save_fields = fields.get("save", {})

        for (table, field), binding in self.field_bindings.items():
            effective_table = table
            raw = fields.get(table, {}).get(field, "")
            if (
                field in {"first_name", "last_name"}
                and raw == ""
                and field in save_fields
            ):
                effective_table = "save"
                raw = save_fields[field]
            binding.original_table = effective_table
            binding.original_raw = str(raw)
            binding.variable.set(
                field_spec(field).display_value(str(raw))
            )

        self.save_index.set(
            str(save_fields.get("player_index", ""))
        )
        self.save_payload.set(
            str(save_fields.get("packed_attributes_hex", ""))
        )

    def _load_rotation(self, team):
        self.rotation_choice_to_index = {}
        choices = []
        for i, slot in enumerate(team.roster):
            if not slot.player_id:
                continue
            name = self.doc.player_display_name(slot.player_id)
            label = f"{name}  ·  Slot {i + 1:02d}"
            self.rotation_choice_to_index[label] = i
            choices.append(label)
        for combo in self.rotation_combos:
            combo.configure(values=choices)

        starters = tuple(team.starter_indexes)
        self.rotation_original = (
            starters if len(starters) == 3 else None
        )
        by_index = {
            value: key
            for key, value in self.rotation_choice_to_index.items()
        }
        for i, var in enumerate(self.rotation_vars):
            index = starters[i] if i < len(starters) else -1
            var.set(
                by_index.get(
                    index,
                    f"Slot {index + 1:02d}" if index >= 0 else "",
                )
            )

    def apply_player(self, silent: bool = False) -> bool:
        if not self.doc:
            return True
        slot = self.doc.teams[
            self.selected_team
        ].roster[self.selected_slot]
        if not slot.player_id:
            return True

        changes: dict[str, dict[str, str]] = {}
        try:
            for binding in self.field_bindings.values():
                entered = binding.variable.get().strip()
                shown_original = field_spec(
                    binding.field
                ).display_value(binding.original_raw)
                if entered == shown_original:
                    continue
                if binding.original_raw == "" and entered == "":
                    continue
                new_raw = validate_field_value(
                    binding.field,
                    entered,
                    binding.original_raw,
                )
                if new_raw != binding.original_raw:
                    changes.setdefault(
                        binding.original_table, {}
                    )[binding.field] = new_raw
        except ValueError as exc:
            if not silent:
                messagebox.showerror(
                    "Invalid player value", str(exc)
                )
            return False

        if not changes:
            if not silent:
                self._set_status("No player changes to apply")
            return True

        before = self._snapshot()
        try:
            self.doc.set_player_fields(slot.player_id, changes)
        except Exception as exc:
            if not silent:
                messagebox.showerror(
                    "Player edit failed", str(exc)
                )
            return False

        self._record_change(
            before,
            f"Edit {self.doc.player_display_name(slot.player_id)}",
        )
        self.load_player(self.selected_slot)
        self.refresh_roster(select_slot=self.selected_slot)
        if not silent:
            self._set_status(
                f"Applied player edits · {len(changes)} field group(s)"
            )
        return True

    def apply_slot(self) -> bool:
        if not self.doc:
            return True
        team = self.doc.teams[self.selected_team]
        old = team.roster[self.selected_slot]
        try:
            role_flags = int(
                self.role_flags_var.get().strip(), 0
            )
            if not 0 <= role_flags <= 0xFFFFFFFF:
                raise ValueError(
                    "Role flags must fit in an unsigned 32-bit value"
                )
        except ValueError as exc:
            messagebox.showerror("Invalid role flags", str(exc))
            return False
        if role_flags == old.role_flags:
            return True

        before = self._snapshot()
        team.set_roster_slot(
            self.selected_slot, old.player_id, role_flags
        )
        self._record_change(
            before,
            f"Edit roster role · {team.name} "
            f"slot {self.selected_slot + 1}",
        )
        self.refresh_roster(select_slot=self.selected_slot)
        self.load_player(self.selected_slot)
        self._set_status(
            f"Updated roster role for slot {self.selected_slot + 1}"
        )
        return True

    def apply_team(self, silent: bool = False) -> bool:
        if not self.doc:
            return True
        team = self.doc.teams[self.selected_team]
        values = {
            key: var.get()
            for key, var in self.team_vars.items()
        }
        if all(
            values[key] == self.team_original.get(key, "")
            for key in values
        ):
            return True

        before = self._snapshot()
        try:
            for key, value in values.items():
                if value != self.team_original.get(key, ""):
                    setattr(team, key, value)
        except Exception as exc:
            self.doc = before
            if not silent:
                messagebox.showerror("Team edit failed", str(exc))
            return False

        self._record_change(before, f"Edit team · {team.name}")
        self.team_original = {
            key: str(getattr(team, key))
            for key in values
        }
        self.refresh_team_list(select_team=self.selected_team)
        self.refresh_roster(select_slot=self.selected_slot)
        if not silent:
            self._set_status(
                f"Applied team edits · {team.name}"
            )
        return True

    def apply_rotation(self, silent: bool = False) -> bool:
        if not self.doc:
            return True
        try:
            indexes = tuple(
                self._rotation_index(var.get())
                for var in self.rotation_vars
            )
            if len(set(indexes)) != 3:
                raise ValueError(
                    "Starting rotation must contain three different players"
                )
        except ValueError as exc:
            if not silent:
                messagebox.showerror(
                    "Invalid rotation", str(exc)
                )
            return False

        if indexes == self.rotation_original:
            return True

        before = self._snapshot()
        team = self.doc.teams[self.selected_team]
        try:
            team.starter_indexes = list(indexes)
        except Exception as exc:
            if not silent:
                messagebox.showerror(
                    "Rotation edit failed", str(exc)
                )
            return False

        self._record_change(
            before, f"Edit starting rotation · {team.name}"
        )
        self._load_rotation(team)
        if not silent:
            self._set_status(
                f"Updated starting rotation · {team.name}"
            )
        return True

    def _rotation_index(self, text: str) -> int:
        value = text.strip()
        if value in self.rotation_choice_to_index:
            return self.rotation_choice_to_index[value]
        if value.lower().startswith("slot "):
            value = value.split()[-1]
        try:
            index = int(value, 0) - 1
        except ValueError as exc:
            raise ValueError(
                f"Select a player from the rotation list: {text!r}"
            ) from exc
        if not 0 <= index < self.doc.max_roster_slots:
            raise ValueError(
                f"Rotation slot must be 1..{self.doc.max_roster_slots}"
            )
        if not self.doc.teams[
            self.selected_team
        ].roster[index].player_id:
            raise ValueError(
                f"Rotation slot {index + 1} is empty"
            )
        return index

    def export_csv(self):
        if not self.doc:
            messagebox.showinfo(
                "Export CSV", "Open a roster first."
            )
            return False
        if not self._apply_pending_edits():
            return False
        default = (
            f"{self.path.stem if self.path else 'mvp07_roster'}"
            "_export.csv"
        )
        name = filedialog.asksaveasfilename(
            title="Export roster CSV",
            defaultextension=".csv",
            initialfile=default,
            filetypes=[
                ("CSV", "*.csv"),
                ("All files", "*.*"),
            ],
        )
        if not name:
            return False
        try:
            rows = export_roster_csv(self.doc, Path(name))
        except Exception as exc:
            messagebox.showerror(
                "CSV export failed", str(exc)
            )
            return False
        self._set_status(
            f"Exported {rows} roster rows to {Path(name).name}"
        )
        return True

    def import_csv(self):
        if not self.doc:
            messagebox.showinfo(
                "Import CSV",
                "Open the roster that this CSV should modify first.",
            )
            return False
        if not self._apply_pending_edits():
            return False

        name = filedialog.askopenfilename(
            title="Import roster CSV",
            filetypes=[
                ("CSV", "*.csv"),
                ("All files", "*.*"),
            ],
        )
        if not name:
            return False

        before = self._snapshot()
        try:
            result = import_roster_csv(
                self.doc, Path(name)
            )
        except Exception as exc:
            self.doc = before
            messagebox.showerror(
                "CSV import failed", str(exc)
            )
            return False

        if result.total_changes:
            self._record_change(
                before, f"Import CSV · {Path(name).name}"
            )
            self.refresh_team_list(
                select_team=self.selected_team
            )
            self.load_team(
                self.selected_team,
                select_slot=self.selected_slot,
            )
        self._set_status(
            f"CSV import: {result.player_changes} players, "
            f"{result.slot_changes} roles, "
            f"{result.team_changes} teams changed"
        )
        return True

    def _snapshot(self):
        return copy.deepcopy(self.doc)

    def _record_change(self, before, description: str):
        self.undo_stack.append((before, description))
        if len(self.undo_stack) > self.HISTORY_LIMIT:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self._set_dirty(True)
        self._update_history_buttons()

    def undo(self):
        if not self.doc or not self.undo_stack:
            return False
        current = self._snapshot()
        previous, description = self.undo_stack.pop()
        self.redo_stack.append((current, description))
        self.doc = previous
        self._set_dirty(True)
        self._restore_view()
        self._set_status(f"Undid: {description}")
        self._update_history_buttons()
        return True

    def redo(self):
        if not self.doc or not self.redo_stack:
            return False
        current = self._snapshot()
        next_state, description = self.redo_stack.pop()
        self.undo_stack.append((current, description))
        self.doc = next_state
        self._set_dirty(True)
        self._restore_view()
        self._set_status(f"Redid: {description}")
        self._update_history_buttons()
        return True

    def _restore_view(self):
        team = min(
            self.selected_team, len(self.doc.teams) - 1
        )
        slot = min(
            self.selected_slot, self.doc.max_roster_slots - 1
        )
        self.refresh_team_list(select_team=team)
        self.load_team(team, select_slot=slot)

    def _update_history_buttons(self):
        self.undo_button.configure(
            state="normal" if self.undo_stack else "disabled"
        )
        self.redo_button.configure(
            state="normal" if self.redo_stack else "disabled"
        )

    def _apply_pending_edits(self) -> bool:
        return (
            self.apply_player(silent=False)
            and self.apply_team(silent=False)
            and self.apply_rotation(silent=False)
        )

    def save_as(self):
        if not self.doc:
            return False
        if not self._apply_pending_edits():
            return False

        source_suffix = self.path.suffix if self.path else ""
        default_ext = source_suffix or ".sav"
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
            return False

        try:
            out = Path(name)
            self.doc.save(out)
            open_roster_document(out)
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return False

        self.path = out
        self._set_dirty(False)
        self.source_label.config(
            text=f"{out.name}  ·  {self.doc.source_kind}"
        )
        self._set_status(
            f"Saved and structurally verified {out.name}"
        )
        return True

    def _set_dirty(self, dirty: bool):
        self.dirty = dirty
        self.dirty_label.config(
            text="● Unsaved changes" if dirty else ""
        )
        base = "MVP 07 Modding Suite — Roster Editor"
        self.master.title(
            f"{base}{' *' if dirty else ''}"
        )

    def _set_status(self, text: str):
        self.status.config(text=text)

    def _on_close(self):
        if not self.dirty:
            self.master.destroy()
            return
        answer = messagebox.askyesnocancel(
            "Unsaved changes",
            "Save your changes before closing?",
        )
        if answer is None:
            return
        if answer and not self.save_as():
            return
        self.master.destroy()


def main():
    root = tk.Tk()
    Editor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
