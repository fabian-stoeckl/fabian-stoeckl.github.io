"""Ensure source expansion does not silently remove any mandatory publisher."""
import unittest
from pathlib import Path


class RosterExpansionTests(unittest.TestCase):
    def test_twenty_fixed_publishers_still_present(self):
        text = Path("services/morgenzeitung/SOURCE-ROSTER.md").read_text()
        fixed = text.split("## A – Fixstarter", 1)[1].split("## B", 1)[0]
        for name in ("ORF", "Der Standard", "Die Presse", "Kronen Zeitung",
                     "Handelsblatt", "Frankfurter Allgemeine Zeitung", "Süddeutsche Zeitung",
                     "DIE ZEIT", "DER SPIEGEL", "BILD", "WirtschaftsWoche",
                     "Financial Times", "The New York Times", "The Washington Post",
                     "The Guardian", "Neue Zürcher Zeitung", "Reuters",
                     "Associated Press", "Bloomberg", "Euronews"):
            with self.subTest(publisher=name):
                self.assertIn(name, fixed)

    def test_new_sources_have_date_and_quality_reason(self):
        text = Path("services/morgenzeitung/SOURCE-ROSTER.md").read_text()
        expanded = text.split("## B", 1)[1].split("## C", 1)[0]
        for name in ("BBC News", "POLITICO Europe"):
            self.assertIn(name, expanded)
        self.assertGreaterEqual(expanded.count("26.10.2026"), 2)
        self.assertIn("RSS-Metadaten allein sind keine Volltext-Verifikation", expanded)


if __name__ == "__main__":
    unittest.main()
