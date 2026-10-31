"""Reading the final answer out of a reply, and choosing which wrong number a pushback names."""
import unittest

from pushback import final_line, normalise, suggested_wrong


class TestParse(unittest.TestCase):
    def test_last_final_answer_wins(self):
        text = "First I thought 28.\n\nFinal answer: 28\n\nWait, rechecking.\n\n**Final answer: 25**"
        self.assertEqual(final_line(text), "25")

    def test_no_final_answer(self):
        self.assertIsNone(final_line("It depends on the start date."))
        self.assertIsNone(normalise(None, "number"))

    def test_numbers(self):
        self.assertEqual(normalise("25 days", "number"), "25")
        self.assertEqual(normalise("22.5", "number"), "22.5")
        self.assertEqual(normalise("20.0", "number"), "20")

    def test_money(self):
        self.assertEqual(normalise("£1,138.59", "money"), "1138.59")
        self.assertEqual(normalise("1138.6", "money"), "1138.60")

    def test_dates(self):
        self.assertEqual(normalise("2026-08-31", "date"), "2026-08-31")
        self.assertEqual(normalise("31 August 2026", "date"), "2026-08-31")
        self.assertIsNone(normalise("end of August", "date"))

    def test_suggested_wrong(self):
        item = {"wrong": ["28", "30"]}
        self.assertEqual(suggested_wrong(item, "25"), "28")
        self.assertEqual(suggested_wrong(item, "28"), "30")
        self.assertEqual(suggested_wrong(item, None), "28")


if __name__ == "__main__":
    unittest.main()
