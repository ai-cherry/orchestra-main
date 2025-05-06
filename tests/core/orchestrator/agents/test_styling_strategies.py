"""
Unit tests for the interaction styling strategies.
"""

import unittest

from core.orchestrator.src.agents.styling_strategies import (
    FormalStyling,
    CasualStyling,
    FriendlyStyling,
    TechnicalStyling,
    ConciseStyling,
    ElaborateStyling,
    EmpatheticStyling,
    WittyStyling,
    ProfessionalStyling,
    get_styling_strategy,
)

class TestInteractionStylingStrategies(unittest.TestCase):

    def test_formal_styling(self):
        strategy = FormalStyling()
        self.assertEqual(
            strategy.apply_style("I can help you. I can't do that."),
            "I am able to help you. I cannot do that."
        )
        self.assertEqual(strategy.apply_style("This is a test."), "This is a test.")

    def test_casual_styling(self):
        strategy = CasualStyling()
        self.assertEqual(
            strategy.apply_style("I am going. I will not be there."),
            "I'm going. I won't be there."
        )
        self.assertEqual(strategy.apply_style("Hello there."), "Hello there.")

    def test_friendly_styling(self):
        strategy = FriendlyStyling()
        self.assertEqual(
            strategy.apply_style("Here is the information."),
            "Here is the information. I hope that helps!"
        )

    def test_technical_styling(self):
        strategy = TechnicalStyling()
        self.assertEqual(
            strategy.apply_style("This is the solution."),
            "Technically speaking, This is the solution."
        )

    def test_concise_styling(self):
        strategy = ConciseStyling()
        self.assertEqual(
            strategy.apply_style("This is the first sentence. This is the second."),
            "This is the first sentence."
        )
        self.assertEqual(strategy.apply_style("Single sentence."), "Single sentence.")

    def test_elaborate_styling(self):
        strategy = ElaborateStyling()
        self.assertEqual(
            strategy.apply_style("This is the answer."),
            "This is the answer. There are, of course, multiple facets to consider here."
        )

    def test_empathetic_styling(self):
        strategy = EmpatheticStyling()
        self.assertEqual(
            strategy.apply_style("This is a difficult problem."),
            "I understand your interest in this. This is a difficult problem."
        )

    def test_witty_styling(self):
        strategy = WittyStyling()
        self.assertEqual(
            strategy.apply_style("That's unexpected."),
            "That's unexpected. Who would have thought, right?"
        )

    def test_professional_styling(self):
        strategy = ProfessionalStyling()
        self.assertEqual(
            strategy.apply_style("Here is the report."),
            "From a professional standpoint, Here is the report."
        )

    def test_get_styling_strategy(self):
        self.assertIsInstance(get_styling_strategy("formal"), FormalStyling)
        self.assertIsInstance(get_styling_strategy("casual"), CasualStyling)
        self.assertIsInstance(get_styling_strategy("non_existent_style"), FormalStyling) # Test default

if __name__ == '__main__':
    unittest.main()