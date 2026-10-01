from __future__ import annotations

import unittest

from mvp07_modding_suite.ui_schema import field_spec, validate_field_value


class UiSchemaTests(unittest.TestCase):
    def test_handedness_keyboard_aliases_map_to_packed_values(self):
        self.assertEqual(validate_field_value("playerattrib_bats", "R", "0"), "0")
        self.assertEqual(validate_field_value("playerattrib_bats", "L", "0"), "1")
        self.assertEqual(validate_field_value("playerattrib_bats", "S", "0"), "2")
        self.assertEqual(validate_field_value("playerattrib_throws", "L", "0"), "1")

    def test_textual_dat_enum_representation_is_preserved(self):
        self.assertEqual(validate_field_value("playerattrib_bats", "L", "R"), "L")
        self.assertEqual(validate_field_value("playerattrib_throws", "R", "L"), "R")

    def test_known_ranges_reject_bad_values(self):
        with self.assertRaises(ValueError):
            validate_field_value("playerattrib_speed", "128", "50")
        with self.assertRaises(ValueError):
            validate_field_value("lrattrib_hit_ul", "4", "0")

    def test_dropdown_display_values(self):
        self.assertEqual(field_spec("playerattrib_bats").display_value("2"), "S")
        self.assertEqual(field_spec("playerattrib_socks").display_value("1"), "Regular")


if __name__ == "__main__":
    unittest.main()
