import unittest

from recognition import WordFormer


class WordFormerTests(unittest.TestCase):
    def setUp(self):
        self.words = WordFormer(
            confidence_threshold=0.7,
            margin_threshold=0.1,
            stability_seconds=1.0,
            release_seconds=0.3,
            space_seconds=1.5,
        )

    def sign(self, letter, now, confidence=0.9, margin=0.3):
        return self.words.update(letter, confidence, margin, True, now)

    def no_hand(self, now):
        return self.words.update("", 0.0, 0.0, False, now)

    def test_stable_letter_is_added_once_until_release(self):
        self.sign("A", 0.0)
        self.sign("A", 1.1)
        self.sign("A", 2.5)
        self.assertEqual(self.words.sentence, "A")

        self.no_hand(2.6)
        self.no_hand(3.0)
        self.sign("A", 3.1)
        self.sign("A", 4.2)
        self.assertEqual(self.words.sentence, "AA")

    def test_low_margin_prediction_is_rejected(self):
        self.sign("B", 0.0, margin=0.02)
        result = self.sign("B", 2.0, margin=0.02)
        self.assertEqual(self.words.sentence, "")
        self.assertEqual(result["pred_letter"], "")

    def test_pause_adds_only_one_space(self):
        self.sign("C", 0.0)
        self.sign("C", 1.1)
        self.no_hand(1.2)
        self.no_hand(2.7)
        self.no_hand(5.0)
        self.assertEqual(self.words.sentence, "C ")


if __name__ == "__main__":
    unittest.main()
