from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldSpec:
    label: str
    minimum: int | None = None
    maximum: int | None = None
    choices: tuple[tuple[str, str], ...] = ()
    help_text: str = ""

    def display_value(self, raw: str) -> str:
        value = str(raw)
        for display, stored in self.choices:
            if value == stored or value.upper() == display.upper():
                return display
        return value

    def stored_value(self, display: str, original_raw: str = "") -> str:
        value = display.strip()
        original = str(original_raw).strip()
        if original and not _looks_int(original):
            for label, _stored in self.choices:
                if value.upper() == label.upper():
                    return label
        for label, stored in self.choices:
            if value.upper() == label.upper():
                return stored
        return value

    @property
    def combo_values(self) -> tuple[str, ...]:
        return tuple(label for label, _stored in self.choices)


POSITION_CHOICES = (
    ("P", "0"),
    ("C", "1"),
    ("1B", "2"),
    ("2B", "3"),
    ("3B", "4"),
    ("SS", "5"),
    ("LF", "6"),
    ("CF", "7"),
    ("RF", "8"),
    ("DH", "9"),
    ("P/Bullpen", "10"),
)

FIELD_SPECS: dict[str, FieldSpec] = {
    "first_name": FieldSpec("First name"),
    "last_name": FieldSpec("Last name"),
    "playerattrib_jerseynum": FieldSpec("Jersey #", 0, 99),
    "playerattrib_bats": FieldSpec(
        "Bats", 0, 2, (("R", "0"), ("L", "1"), ("S", "2")),
        "Type R, L, or S. Numeric storage is preserved for packed saves.",
    ),
    "playerattrib_throws": FieldSpec(
        "Throws", 0, 1, (("R", "0"), ("L", "1")), "Type R or L."
    ),
    "playerattrib_primaryposition": FieldSpec("Primary position", 0, 10, POSITION_CHOICES),
    "playerattrib_secondaryposition": FieldSpec("Secondary position", 0, 10, POSITION_CHOICES),
    "playerattrib_height": FieldSpec("Height", 0, 63),
    "playerattrib_weight": FieldSpec("Weight", 0, 255),
    "playerattrib_year": FieldSpec("Year", 0, 3),
    "playerattrib_homelocation": FieldSpec("Home location", 0, 63),
    "playerattrib_speed": FieldSpec("Speed", 0, 127),
    "playerattrib_fielding": FieldSpec("Fielding", 0, 15),
    "playerattrib_range": FieldSpec("Range", 0, 15),
    "playerattrib_throwstrength": FieldSpec("Throw strength", 0, 15),
    "playerattrib_throwaccuracy": FieldSpec("Throw accuracy", 0, 15),
    "playerattrib_bunting": FieldSpec("Bunting", 0, 15),
    "playerattrib_platediscipline": FieldSpec("Plate discipline", 0, 15),
    "playerattrib_baserunning": FieldSpec("Baserunning", 0, 15),
    "playerattrib_durability": FieldSpec("Durability", 0, 15),
    "playerattrib_battingstance": FieldSpec("Batting stance", 0, 63),
    "playerattrib_swingtype": FieldSpec("Swing type", 0, 1),
    "playerattrib_ditty": FieldSpec("Ditty", 0, 7),
    "playerattrib_starpower": FieldSpec("Star power", 0, 7),
    "playerattrib_scholarshiptenths": FieldSpec("Scholarship tenths", 0, 15),
    "playerattrib_attitude": FieldSpec("Attitude", 0, 3),
    "playerattrib_academic": FieldSpec("Academic", 0, 3),
    "playerattrib_facemorphindex": FieldSpec("Face morph", 0, 15),
    "playerattrib_boneprofile": FieldSpec("Bone profile", 0, 31),
    "playerattrib_skintone": FieldSpec("Skin tone", 0, 7),
    "playerattrib_eyecolour": FieldSpec("Eye colour", 0, 7),
    "playerattrib_haircolour": FieldSpec("Hair colour", 0, 7),
    "playerattrib_sideburns": FieldSpec("Sideburns", 0, 7),
    "playerattrib_facialhair": FieldSpec("Facial hair", 0, 15),
    "playerattrib_captype": FieldSpec("Cap type", 0, 3),
    "playerattrib_capposition": FieldSpec("Cap position", 0, 3),
    "derived_eyeblack": FieldSpec("Eye black", 0, 1, (("Off", "0"), ("On", "1"))),
    "derived_sunglasses_style": FieldSpec(
        "Sunglasses", 0, 3,
        (("None", "0"), ("Style 1", "1"), ("Style 2", "2"), ("Style 3", "3")),
    ),
    "playerattrib_battinghelmet": FieldSpec("Batting helmet", 0, 3),
    "playerattrib_elbowguard": FieldSpec("Elbow guard", 0, 1, (("Off", "0"), ("On", "1"))),
    "playerattrib_wristbandleftarm": FieldSpec("Left wristband", 0, 3),
    "playerattrib_wristbandrightarm": FieldSpec("Right wristband", 0, 3),
    "playerattrib_shinguard": FieldSpec("Shin guard", 0, 1, (("Off", "0"), ("On", "1"))),
    "playerattrib_socks": FieldSpec(
        "Pants / socks", 0, 2, (("Low", "0"), ("Regular", "1"), ("High", "2"))
    ),
    "playerattrib_catchermask": FieldSpec(
        "Catcher mask", 0, 1, (("Mask 1", "0"), ("Mask 2", "1"))
    ),
    "pitchattrib_pitcher_delivery": FieldSpec("Delivery", 0, 31),
    "pitchattrib_stamina": FieldSpec("Stamina", 0, 127),
    "pitchattrib_pickoff": FieldSpec("Pickoff", 0, 15),
}

for _name in (
    "lrattrib_contact", "lrattrib_power",
    "lrattrib_lf_pct", "lrattrib_cf_pct", "lrattrib_rf_pct", "lrattrib_hr_pct",
    "lrattrib_fb_pct", "lrattrib_ld_pct", "lrattrib_gb_pct",
    "pitchattrib_fastball_control", "pitchattrib_fastball_velocity",
    "pitchattrib_pitch2_control", "pitchattrib_pitch2_velocity",
    "pitchattrib_pitch3_control", "pitchattrib_pitch3_velocity",
    "pitchattrib_pitch4_control", "pitchattrib_pitch4_velocity",
    "pitchattrib_pitch5_control", "pitchattrib_pitch5_velocity",
):
    FIELD_SPECS.setdefault(_name, FieldSpec(_name.replace("_", " ").title(), 0, 127))

for _name in (
    "lrattrib_chasefb", "lrattrib_chaseslowbreak", "lrattrib_chasehardbreak",
    "lrattrib_takefb", "lrattrib_takeslowbreak", "lrattrib_takehardbreak",
    "lrattrib_missfb", "lrattrib_missslowbreak", "lrattrib_misshardbreak",
    "pitchattrib_pitch2_type", "pitchattrib_pitch2_movement",
    "pitchattrib_pitch3_type", "pitchattrib_pitch3_movement",
    "pitchattrib_pitch4_type", "pitchattrib_pitch4_movement",
    "pitchattrib_pitch5_type", "pitchattrib_pitch5_movement",
):
    FIELD_SPECS.setdefault(_name, FieldSpec(_name.replace("_", " ").title(), 0, 15))

for _name in (
    "lrattrib_hit_ul", "lrattrib_hit_um", "lrattrib_hit_ur",
    "lrattrib_hit_cl", "lrattrib_hit_cm", "lrattrib_hit_cr",
    "lrattrib_hit_ll", "lrattrib_hit_lm", "lrattrib_hit_lr",
):
    FIELD_SPECS.setdefault(_name, FieldSpec(_name.replace("_", " ").title(), 0, 3))

for _name in (
    "pitchattrib_pitch2_description", "pitchattrib_pitch3_description",
    "pitchattrib_pitch4_description", "pitchattrib_pitch5_description",
):
    FIELD_SPECS.setdefault(_name, FieldSpec(_name.replace("_", " ").title(), 0, 7))


def field_spec(name: str) -> FieldSpec:
    return FIELD_SPECS.get(name, FieldSpec(humanize(name)))


def humanize(name: str) -> str:
    for prefix in ("playerattrib_", "lrattrib_", "pitchattrib_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    return name.replace("_", " ").strip().title()


def validate_field_value(name: str, value: str, original_raw: str = "") -> str:
    spec = field_spec(name)
    raw = spec.stored_value(value, original_raw)
    if raw == "":
        return raw
    if spec.minimum is None and spec.maximum is None:
        return raw
    if spec.choices and any(
        raw.upper() == label.upper() for label, _stored in spec.choices
    ):
        return raw
    if not _looks_int(raw):
        raise ValueError(f"{spec.label} must be a number or a listed choice")
    number = int(raw, 0)
    if spec.minimum is not None and number < spec.minimum:
        raise ValueError(f"{spec.label} must be at least {spec.minimum}")
    if spec.maximum is not None and number > spec.maximum:
        raise ValueError(f"{spec.label} must be at most {spec.maximum}")
    return str(number)


def _looks_int(value: str) -> bool:
    try:
        int(str(value).strip(), 0)
        return True
    except (TypeError, ValueError):
        return False
