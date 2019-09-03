from unittest import TestCase
from autocat import *


class TestDisambiguator(TestCase):
    def test_generic_cases(self):
        auto = StraightAutodisambiguation(
            lemma_key="lemma",
            categorizable={"quis": "1"}
        )
        pos = CategoryAutodisambiguation(
            lemma_key="lemma",
            category_key="pos",
            categorizable={"qui": {'ADV': '4', 'ADVint': '3', 'ADVrel': '2', 'PROrel': '1'}}
        )
        gend = CategoryAutodisambiguation(
            lemma_key="lemma",
            category_key="gend",
            categorizable={"nauta": {'F': 'N'}}
        )
        unk = NeedsDisambiguation(
            lemma_key="lemma",
            categorizable=["data"]
        )
        group = GroupAutodisambiguation((auto, pos, gend, unk))
        self.assertEqual(
            group.disambiguate({"lemma": "qui", "pos": "ADV"}), "4",
            "Lemma qui should be categorized by POS"
        )
        self.assertEqual(
            group.disambiguate({"lemma": "quis", "pos": "ADV"}), "1",
            "Lemma qui should be categorized by itself automatically"
        )
        self.assertEqual(
            group.disambiguate({"lemma": "quod", "pos": "ADV"}), None,
            "If no disambiguation, then no disambiguation"
        )
        self.assertEqual(
            list(group.disambiguate_rows([
                {"lemma": "qui", "pos": "ADV", "gend": "_"},
                {"lemma": "quis", "pos": "ADV", "gend": "_"},
                {"lemma": "quod", "pos": "ADV", "gend": "_"},
                {"lemma": "nauta", "pos": "ADV", "gend": "F"},
                {"lemma": "data", "pos": "ADV", "gend": "F"}
            ])), ["4", "1", "", "N", "?"],
            "Disambiguating rows should return interpretable results"
        )
