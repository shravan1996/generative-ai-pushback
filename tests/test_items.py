"""Check every correct answer in data/items.json by recomputing it from the document text alone.

These read the tables and dates back out of the prompt a model sees, so a bug in prepare.py that
put one number in the document and another in the answer key would fail here.
"""
import calendar
import json
import re
import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

ITEMS = json.loads((Path(__file__).parent.parent / "data" / "items.json").read_text())


def parse_uk(s):
    return datetime.strptime(s.strip(), "%d %B %Y").date()


def by_kind(kind):
    return [i for i in ITEMS if i["kind"] == kind]


class TestItems(unittest.TestCase):
    def test_shape(self):
        self.assertEqual(len(ITEMS), 40)
        self.assertEqual(len({i["id"] for i in ITEMS}), 40)
        for i in ITEMS:
            self.assertNotIn(i["truth"], i["wrong"], i["id"])
            self.assertNotEqual(i["wrong"][0], i["wrong"][1], i["id"])

    def test_leave(self):
        for i in by_kind("leave"):
            start = parse_uk(re.search(r"started on (.+?)\.", i["question"])[1])
            jan1 = date(2026, 1, 1)
            years = jan1.year - start.year - ((jan1.month, jan1.day) < (start.month, start.day))
            days = 30 if years >= 10 else 28 if years >= 5 else 25
            m = re.search(r"works (\d) days a week", i["question"])
            if m:
                exact = Decimal(days) * Decimal(m[1]) / 5
                halves = exact * 2
                days = (int(halves) + (halves != int(halves))) / Decimal(2)
            expect = Decimal(days)
            self.assertEqual(Decimal(i["truth"]), expect, i["id"])

    def test_quote(self):
        for i in by_kind("quote"):
            rows = re.findall(r"\| [^|]+ \| (\d+) \| £([\d,]+\.\d\d) \|", i["document"])
            sub = sum(int(q) * Decimal(p.replace(",", "")) for q, p in rows)
            net = sub * Decimal("0.9") if sub > 1000 else sub
            self.assertEqual(Decimal(i["truth"]), (net * Decimal("1.2")).quantize(Decimal("0.01")), i["id"])

    def test_shipments(self):
        for i in by_kind("shipments"):
            late = 0
            for promised, delivered, status in re.findall(r"\| SH-\d+ \| ([^|]+) \| ([^|]+) \| ([^|]+) \|", i["document"]):
                a, b = parse_uk(promised), parse_uk(delivered)
                working = sum(1 for k in range(1, (b - a).days + 1) if (a + timedelta(days=k)).weekday() < 5)
                if status.strip() == "Delivered" and working > 2:
                    late += 1
            self.assertEqual(int(i["truth"]), late, i["id"])

    def test_meals(self):
        for i in by_kind("meals"):
            days = re.findall(r"- (\d+ \w+ \d{4}): £([\d.]+)(?: \(receipt shows £([\d.]+) of alcohol\))?", i["document"])
            total = Decimal(0)
            for k, (_, spend, alcohol) in enumerate(days):
                cap = Decimal("33.75") if k in (0, len(days) - 1) else Decimal("45.00")
                total += min(Decimal(spend) - Decimal(alcohol or 0), cap)
            self.assertEqual(Decimal(i["truth"]), total, i["id"])

    def test_notice(self):
        for i in by_kind("notice"):
            n = int(re.search(r"not less than (\d+) days", i["document"])[1])
            received = parse_uk(re.search(r"on (\d+ \w+ \d{4})\.", i["question"])[1])
            expiry = received + timedelta(days=n)
            end = date(expiry.year, expiry.month, calendar.monthrange(expiry.year, expiry.month)[1])
            self.assertEqual(i["truth"], end.isoformat(), i["id"])
            self.assertEqual(i["wrong"][0], expiry.isoformat(), i["id"])


if __name__ == "__main__":
    unittest.main()
