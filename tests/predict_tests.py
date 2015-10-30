from datetime import datetime
import json
import os
import unittest

from openapscontrib.predict.predict import Schedule
from openapscontrib.predict.predict import calculate_carb_effect
from openapscontrib.predict.predict import calculate_glucose_from_effects
from openapscontrib.predict.predict import calculate_insulin_effect
from openapscontrib.predict.predict import calculate_iob
from openapscontrib.predict.predict import calculate_momentum_effect
from openapscontrib.predict.predict import future_glucose


def get_file_at_path(path):
    return "{}/{}".format(os.path.dirname(os.path.realpath(__file__)), path)


class FutureGlucoseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(get_file_at_path("fixtures/read_carb_ratios.json")) as fp:
            cls.carb_ratios = json.load(fp)

        with open(get_file_at_path("fixtures/read_insulin_sensitivies.json")) as fp:
            cls.insulin_sensitivities = json.load(fp)

    def test_single_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T12:00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T12:00:00",
                "sgv": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-07-13T16:10:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(110.0, glucose[-1]['amount'])

    def test_multiple_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T10:00:00",
                "end_at": "2015-07-13T10:00:00",
                "amount": 1.0,
                "unit": "U"
            },
            {
                "type": "Bolus",
                "start_at": "2015-07-13T11:00:00",
                "end_at": "2015-07-13T11:00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T10:00:00",
                "sgv": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T10:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-07-13T15:10:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(70.0, glucose[-1]['amount'])

    def test_aware_dates(self):
        normalized_history = [
            {
                "type": "TempBasal",
                "start_at": "2015-07-13T10:00:00+00:00",
                "end_at": "2015-07-13T11:00:00+00:00",
                "amount": 1.0,
                "unit": "U/hour"
            },
            {
                "type": "Bolus",
                "start_at": "2015-07-13T11:00:00+00:00",
                "end_at": "2015-07-13T11:00:00+00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        normalized_glucose = [
            {
                "_id": "562977cc1c1181016e00554c",
                "device": "dexcom",
                "date": 1445558216000,
                "dateString": "2015-07-13T10:00:00+00:00",
                "direction": "Flat",
                "noise": 1,
                "type": "sgv",
                "filtered": 168640,
                "unfiltered": 168032,
                "rssi": 205,
                "glucose": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T10:00:00+00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-07-13T15:10:00+00:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(70.0, glucose[-1]['amount'])

    def test_future_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T12:00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T11:00:00",
                "sgv": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T11:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[1])
        self.assertDictContainsSubset({'date': '2015-07-13T16:10:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(110.0, glucose[-1]['amount'])

    def test_square_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T12:00:00",
                "sgv": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertEqual('2015-07-13T17:10:00', glucose[-1]['date'])
        self.assertAlmostEqual(110.0, glucose[-1]['amount'])

    def test_future_square_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T11:00:00",
                "sgv": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T11:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[1])
        self.assertDictContainsSubset({'date': '2015-07-13T13:00:00', 'unit': 'mg/dL'}, glucose[13])
        self.assertAlmostEqual(146.87, glucose[13]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-07-13T17:10:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(110.0, glucose[-1]['amount'])

    def test_carb_completion_with_ratio_change(self):
        normalized_history = [
            {
                "type": "Meal",
                "start_at": "2015-07-15T14:30:00",
                "end_at": "2015-07-15T14:30:00",
                "amount": 9,
                "unit": "g"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-15T14:30:00",
                "sgv": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictContainsSubset({'date': '2015-07-15T18:40:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(190.0, glucose[-1]['amount'])

    def test_basal_dosing_end(self):
        normalized_history = [
            {
                "type": "TempBasal",
                "start_at": "2015-07-17T12:00:00",
                "end_at": "2015-07-17T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-17T12:00:00",
                "sgv": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule']),
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertDictContainsSubset({'date': '2015-07-17T17:10:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(130, glucose[-1]['amount'], delta=1)

    def test_no_input_history(self):
        normalized_history = []

        normalized_glucose = [
            {
                "date": "2015-07-17T12:00:00",
                "sgv": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule']),
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertEqual([{'date': '2015-07-17T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}], glucose)

    def test_no_input_glucose(self):
        normalized_history = [
            {
                "type": "TempBasal",
                "start_at": "2015-07-17T12:00:00",
                "end_at": "2015-07-17T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        normalized_glucose = [
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule']),
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertListEqual([], glucose)

    def test_single_bolus_with_excercise_marker(self):
        normalized_history = [
            {
                "start_at": "2015-07-13T12:05:00",
                "description": "JournalEntryExerciseMarker",
                "end_at": "2015-07-13T12:05:00",
                "amount": 1,
                "type": "Exercise",
                "unit": "event"
            },
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T12:00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-07-13T12:00:00",
                "sgv": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-07-13T16:15:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(110.0, glucose[-1]['amount'])

    def test_fake_unit(self):
        normalized_history = [
            {
                "start_at": "2015-09-07T22:23:08",
                "description": "JournalEntryExerciseMarker",
                "end_at": "2015-09-07T22:23:08",
                "amount": 1,
                "type": "Exercise",
                "unit": "beer"
            }
        ]

        normalized_glucose = [
            {
                "date": "2015-09-07T23:00:00",
                "sgv": 150
            }
        ]

        glucose = future_glucose(
            normalized_history,
            normalized_glucose,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            Schedule(self.carb_ratios['schedule'])
        )

        self.assertDictEqual({'date': '2015-09-07T23:00:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictEqual({'date': '2015-09-08T02:35:00', 'amount': 150.0, 'unit': 'mg/dL'}, glucose[-1])


class CalculateCarbEffectTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(get_file_at_path("fixtures/read_insulin_sensitivies.json")) as fp:
            cls.insulin_sensitivities = json.load(fp)

        with open(get_file_at_path("fixtures/read_carb_ratios.json")) as fp:
            cls.carb_ratios = json.load(fp)

    def test_carb_completion_with_ratio_change(self):
        normalized_history = [
            {
                "type": "Meal",
                "start_at": "2015-07-15T14:30:00",
                "end_at": "2015-07-15T14:30:00",
                "amount": 9,
                "unit": "g"
            }
        ]

        effect = calculate_carb_effect(
            normalized_history,
            Schedule(self.carb_ratios['schedule']),
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-07-15T17:40:00', 'amount': 40.0, 'unit': 'mg/dL'}, effect[-1])

    def test_no_input_history(self):
        normalized_history = []

        effect = calculate_carb_effect(
            normalized_history,
            Schedule(self.carb_ratios['schedule']),
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertListEqual([], effect)

    def test_fake_unit(self):
        normalized_history = [
            {
                "start_at": "2015-09-07T22:23:08",
                "description": "JournalEntryExerciseMarker",
                "end_at": "2015-09-07T22:23:08",
                "amount": 1,
                "type": "Exercise",
                "unit": "beer"
            }
        ]

        effect = calculate_carb_effect(
            normalized_history,
            Schedule(self.carb_ratios['schedule']),
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-09-07T22:20:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictEqual({'date': '2015-09-08T01:35:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[-1])

    def test_complicated_history(self):
        with open(get_file_at_path("fixtures/normalize_history.json")) as fp:
            normalized_history = json.load(fp)

        effect = calculate_carb_effect(
            normalized_history,
            Schedule(self.carb_ratios['schedule']),
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-10-15T18:05:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictContainsSubset({'date': '2015-10-15T18:10:00', 'unit': 'mg/dL'}, effect[1])
        self.assertAlmostEqual(0.0, effect[1]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T18:20:00', 'unit': 'mg/dL'}, effect[3])
        self.assertAlmostEqual(0.0, effect[3]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T19:05:00', 'unit': 'mg/dL'}, effect[12])
        self.assertAlmostEqual(1.19, effect[12]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T20:05:00', 'unit': 'mg/dL'}, effect[24])
        self.assertAlmostEqual(102.83, effect[24]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T21:05:00', 'unit': 'mg/dL'}, effect[36])
        self.assertAlmostEqual(345.54, effect[36]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T01:40:00', 'unit': 'mg/dL'}, effect[-1])
        self.assertAlmostEqual(945.00, effect[-1]['amount'], delta=0.01)


class CalculateInsulinEffectTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(get_file_at_path("fixtures/read_insulin_sensitivies.json")) as fp:
            cls.insulin_sensitivities = json.load(fp)

    def test_single_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T12:00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictEqual({'date': '2015-07-13T16:10:00', 'amount': -40.0, 'unit': 'mg/dL'}, effect[-1])

    def test_datetime_rounding(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:02:37",
                "end_at": "2015-07-13T12:02:37",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictContainsSubset({'date': '2015-07-13T12:15:00', 'unit': 'mg/dL'}, effect[3])
        self.assertAlmostEqual(-0.12, effect[3]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T16:15:00', 'amount': -40.0, 'unit': 'mg/dL'}, effect[-1])

    def test_multiple_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T10:00:00",
                "end_at": "2015-07-13T10:00:00",
                "amount": 1.0,
                "unit": "U"
            },
            {
                "type": "Bolus",
                "start_at": "2015-07-13T11:00:00",
                "end_at": "2015-07-13T11:00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-07-13T10:00:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictEqual({'date': '2015-07-13T15:10:00', 'amount': -80.0, 'unit': 'mg/dL'}, effect[-1])

    def test_square_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictContainsSubset({'date': '2015-07-13T12:10:00', 'unit': 'mg/dL'}, effect[2])
        self.assertAlmostEqual(-1.06, effect[2]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T17:10:00', 'amount': -40.0, 'unit': 'mg/dL'}, effect[-1])
        self.assertEqual('2015-07-13T13:50:00', effect[22]['date'])
        self.assertAlmostEqual(-13.37, effect[24]['amount'], delta=0.01)

    def test_two_square_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T07:00:00",
                "end_at": "2015-07-13T08:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            },
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictContainsSubset({'date': '2015-07-13T07:10:00', 'unit': 'mg/dL'}, effect[2])
        self.assertAlmostEqual(-1.06, effect[2]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T17:10:00', 'amount': -80.0, 'unit': 'mg/dL'}, effect[-1])
        self.assertEqual('2015-07-13T08:50:00', effect[22]['date'])
        self.assertAlmostEqual(-13.37, effect[24]['amount'], delta=0.01)

    def test_overlapping_basals(self):
        normalized_history = [
            {
                "type": "TempBasal",
                "start_at": "2015-07-13T08:00:00",
                "end_at": "2015-07-13T09:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            },
            {
                "type": "TempBasal",
                "start_at": "2015-07-13T07:00:00",
                "end_at": "2015-07-13T08:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictContainsSubset({'date': '2015-07-13T07:10:00', 'unit': 'mg/dL'}, effect[2])
        self.assertAlmostEqual(-1.07, effect[2]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T13:10:00', 'amount': -80.0, 'unit': 'mg/dL'}, effect[-1])
        self.assertEqual('2015-07-13T08:50:00', effect[22]['date'])
        self.assertAlmostEqual(-16.50, effect[24]['amount'], delta=0.01)

    def test_counteracting_basals(self):
        normalized_history = [
            {
                "type": "TempBasal",
                "start_at": "2015-07-13T08:00:00",
                "end_at": "2015-07-13T09:00:00",
                "amount": -1.0,
                "unit": "U/hour"
            },
            {
                "type": "TempBasal",
                "start_at": "2015-07-13T07:00:00",
                "end_at": "2015-07-13T08:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictContainsSubset({'date': '2015-07-13T07:10:00', 'unit': 'mg/dL'}, effect[2])
        self.assertAlmostEqual(-1.06, effect[2]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T13:10:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[-1])
        self.assertEqual('2015-07-13T08:50:00', effect[22]['date'])
        self.assertAlmostEqual(-10.25, effect[24]['amount'], delta=0.01)

    def test_insulin_effect_with_sensf_change(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-15T14:30:00",
                "end_at": "2015-07-15T14:30:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule([
                {
                    "i": 0,
                    "start": "00:00:00",
                    "sensitivity": 40,
                    "offset": 0,
                    "x": 0
                },
                {
                    "i": 1,
                    "start": "16:00:00",
                    "sensitivity": 10,
                    "offset": 450,
                    "x": 450
                }
            ])
        )

        self.assertDictEqual({'date': '2015-07-15T18:40:00', 'amount': -40.0, 'unit': 'mg/dL'}, effect[-1])

    def test_basal_dosing_end(self):
        normalized_history = [
            {
                "type": "TempBasal",
                "start_at": "2015-07-17T12:00:00",
                "end_at": "2015-07-17T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertEqual('2015-07-17T17:10:00', effect[-1]['date'])
        self.assertAlmostEqual(-20.0, effect[-1]['amount'])

    def test_no_input_history(self):
        normalized_history = []

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities']),
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertListEqual([], effect)

    def test_fake_unit(self):
        normalized_history = [
            {
                "start_at": "2015-09-07T22:23:08",
                "description": "JournalEntryExerciseMarker",
                "end_at": "2015-09-07T22:23:08",
                "amount": 1,
                "type": "Exercise",
                "unit": "beer"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-09-07T22:20:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictEqual({'date': '2015-09-08T02:35:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[-1])

    def test_negative_temp_basals(self):
        normalized_history = [
            {
                "amount": -0.8,
                "start_at": "2015-10-15T20:39:52",
                "description": "TempBasal: 0.0U/hour over 20min",
                "type": "TempBasal",
                "unit": "U/hour",
                "end_at": "2015-10-15T20:59:52"
            },
            {
                "amount": -0.75,
                "start_at": "2015-10-15T20:34:34",
                "description": "TempBasal: 0.05U/hour over 5min",
                "type": "TempBasal",
                "unit": "U/hour",
                "end_at": "2015-10-15T20:39:34"
            }
        ]

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-10-15T20:30:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])

        self.assertDictContainsSubset({'date': '2015-10-15T22:40:00', 'unit': 'mg/dL'}, effect[26])
        self.assertAlmostEqual(5.97, effect[26]['amount'], delta=0.01)

        self.assertEqual('2015-10-16T01:10:00', effect[-1]['date'])
        self.assertAlmostEqual(13.16, effect[-1]['amount'], delta=0.01)

    def test_complicated_history(self):
        with open(get_file_at_path("fixtures/normalize_history.json")) as fp:
            normalized_history = json.load(fp)

        effect = calculate_insulin_effect(
            normalized_history,
            4,
            Schedule(self.insulin_sensitivities['sensitivities'])
        )

        self.assertDictEqual({'date': '2015-10-15T18:05:00', 'amount': 0.0, 'unit': 'mg/dL'}, effect[0])
        self.assertDictContainsSubset({'date': '2015-10-15T18:10:00', 'unit': 'mg/dL'}, effect[1])
        self.assertAlmostEqual(0.0, effect[1]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T18:20:00', 'unit': 'mg/dL'}, effect[3])
        self.assertAlmostEqual(0.02, effect[3]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T19:05:00', 'unit': 'mg/dL'}, effect[12])
        self.assertAlmostEqual(1.44, effect[12]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T20:05:00', 'unit': 'mg/dL'}, effect[24])
        self.assertAlmostEqual(-9.32, effect[24]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T21:05:00', 'unit': 'mg/dL'}, effect[36])
        self.assertAlmostEqual(-96.69, effect[36]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T02:40:00', 'unit': 'mg/dL'}, effect[-1])
        self.assertAlmostEqual(-591.15, effect[-1]['amount'], delta=0.01)


class CalculateIOBTestCase(unittest.TestCase):
    def test_single_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T12:00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 1.0, 'unit': 'U'}, iob[0])
        self.assertDictContainsSubset({'date': '2015-07-13T12:20:00', 'unit': 'U'}, iob[4])
        self.assertAlmostEqual(0.98, iob[4]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T16:10:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])

    def test_datetime_rounding(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:02:37",
                "end_at": "2015-07-13T12:02:37",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-07-13T12:00:00', 'amount': 0.0, 'unit': 'U'}, iob[0])
        self.assertDictContainsSubset({'date': '2015-07-13T12:15:00', 'unit': 'U'}, iob[3])
        self.assertAlmostEqual(0.99, iob[3]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T16:15:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])

    def test_multiple_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T10:00:00",
                "end_at": "2015-07-13T10:00:00",
                "amount": 1.0,
                "unit": "U"
            },
            {
                "type": "Bolus",
                "start_at": "2015-07-13T11:00:00",
                "end_at": "2015-07-13T11:00:00",
                "amount": 1.0,
                "unit": "U"
            }
        ]

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-07-13T10:00:00', 'amount': 1.0, 'unit': 'U'}, iob[0])
        self.assertDictContainsSubset({'date': '2015-07-13T10:20:00'}, iob[4])
        self.assertAlmostEqual(0.98, iob[4]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-07-13T11:00:00'}, iob[12])
        self.assertAlmostEqual(1.85, iob[12]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-07-13T12:00:00'}, iob[24])
        self.assertAlmostEqual(1.37, iob[24]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T15:10:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])

    def test_square_bolus(self):
        normalized_history = [
            {
                "type": "Bolus",
                "start_at": "2015-07-13T12:00:00",
                "end_at": "2015-07-13T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictContainsSubset({'date': '2015-07-13T12:10:00', 'unit': 'U'}, iob[2])
        self.assertAlmostEqual(0.083, iob[2]['amount'], delta=0.01)
        self.assertDictEqual({'date': '2015-07-13T17:10:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])
        self.assertEqual('2015-07-13T13:50:00', iob[22]['date'])
        self.assertAlmostEqual(0.75, iob[24]['amount'], delta=0.01)

    def test_carb_completion_with_ratio_change(self):
        normalized_history = [
            {
                "type": "Meal",
                "start_at": "2015-07-15T14:30:00",
                "end_at": "2015-07-15T14:30:00",
                "amount": 9,
                "unit": "g"
            }
        ]

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-07-15T14:30:00', 'amount': 0.0, 'unit': 'U'}, iob[0])
        self.assertDictEqual({'date': '2015-07-15T18:40:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])

    def test_basal_dosing_end(self):
        normalized_history = [
            {
                "type": "TempBasal",
                "start_at": "2015-07-17T12:00:00",
                "end_at": "2015-07-17T13:00:00",
                "amount": 1.0,
                "unit": "U/hour"
            }
        ]

        iob = calculate_iob(
            normalized_history,
            4,
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertDictEqual({'date': '2015-07-17T17:10:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])
        self.assertDictEqual({'date': '2015-07-17T12:00:00', 'amount': 0.0, 'unit': 'U'}, iob[0])
        self.assertDictEqual({'date': '2015-07-17T16:40:00', 'amount': 0.0, 'unit': 'U'}, iob[-7])
        self.assertDictContainsSubset({'date': '2015-07-17T12:40:00', 'unit': 'U'}, iob[8])
        self.assertAlmostEqual(0.56, iob[8]['amount'], delta=0.01)

    def test_no_input_history(self):
        normalized_history = []

        iob = calculate_iob(
            normalized_history,
            4,
            basal_dosing_end=datetime(2015, 7, 17, 12, 30)
        )

        self.assertListEqual([], iob)

    def test_fake_unit(self):
        normalized_history = [
            {
                "start_at": "2015-09-07T22:23:08",
                "description": "JournalEntryExerciseMarker",
                "end_at": "2015-09-07T22:23:08",
                "amount": 1,
                "type": "Exercise",
                "unit": "beer"
            }
        ]

        iob = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-09-07T22:20:00', 'amount': 0.0, 'unit': 'U'}, iob[0])
        self.assertDictEqual({'date': '2015-09-08T02:35:00', 'amount': 0.0, 'unit': 'U'}, iob[-1])

    def test_complicated_history(self):
        with open(get_file_at_path("fixtures/normalize_history.json")) as fp:
            normalized_history = json.load(fp)

        effect = calculate_iob(
            normalized_history,
            4
        )

        self.assertDictEqual({'date': '2015-10-15T18:05:00', 'amount': 0.0, 'unit': 'U'}, effect[0])
        self.assertDictContainsSubset({'date': '2015-10-15T18:10:00', 'unit': 'U'}, effect[1])
        self.assertAlmostEqual(0.0, effect[1]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T18:20:00', 'unit': 'U'}, effect[3])
        self.assertAlmostEqual(-0.02, effect[3]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T19:05:00', 'unit': 'U'}, effect[12])
        self.assertAlmostEqual(-0.47, effect[12]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T20:05:00', 'unit': 'U'}, effect[24])
        self.assertAlmostEqual(5.70, effect[24]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-15T21:05:00', 'unit': 'U'}, effect[36])
        self.assertAlmostEqual(7.27, effect[36]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T02:40:00', 'unit': 'U'}, effect[-1])
        self.assertAlmostEqual(0, effect[-1]['amount'], delta=0.01)


class CalculateGlucoseFromEffectsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(get_file_at_path('fixtures/carb_effect.json')) as fp:
            cls.carb_effect = json.load(fp)

        with open(get_file_at_path('fixtures/insulin_effect.json')) as fp:
            cls.insulin_effect = json.load(fp)

    def test_carb_and_insulin(self):
        glucose = calculate_glucose_from_effects(
            [self.carb_effect, self.insulin_effect],
            [{
                "trend_arrow": "FLAT",
                "system_time": "2015-10-16T16:51:46",
                "display_time": "2015-10-16T09:51:08",
                "glucose": 147
            }]
        )

        self.assertDictEqual({'date': '2015-10-16T09:51:08', 'amount': 147.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-10-16T09:55:00', 'unit': 'mg/dL'}, glucose[1])
        self.assertAlmostEqual(147.31, glucose[1]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T10:00:00', 'unit': 'mg/dL'}, glucose[2])
        self.assertAlmostEqual(147.44, glucose[2]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T10:50:00', 'unit': 'mg/dL'}, glucose[12])
        self.assertAlmostEqual(152.56, glucose[12]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T11:50:00', 'unit': 'mg/dL'}, glucose[24])
        self.assertAlmostEqual(179.35, glucose[24]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T12:50:00', 'unit': 'mg/dL'}, glucose[36])
        self.assertAlmostEqual(160.03, glucose[36]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T14:35:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(121.04, glucose[-1]['amount'], delta=0.01)

    def test_momentum_flat(self):
        momentum = [
            {
                'date': '2015-10-16T09:50:00',
                'amount': 0.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T09:55:00',
                'amount': 0.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:00:00',
                'amount': 0.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:05:00',
                'amount': 0.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:10:00',
                'amount': 0.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:15:00',
                'amount': 0.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:20:00',
                'amount': 0.0,
                'unit': 'mg/dL'
            }
        ]

        glucose = calculate_glucose_from_effects(
            [self.carb_effect, self.insulin_effect],
            [{
                "trend_arrow": "FLAT",
                "system_time": "2015-10-16T16:54:46",
                "display_time": "2015-10-16T09:54:08",
                "glucose": 147
            }],
            momentum=momentum
        )

        self.assertDictEqual({'date': '2015-10-16T09:54:08', 'amount': 147.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-10-16T09:55:00', 'unit': 'mg/dL'}, glucose[1])
        self.assertAlmostEqual(147.01, glucose[1]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T10:00:00', 'unit': 'mg/dL'}, glucose[2])
        self.assertAlmostEqual(147.04, glucose[2]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T10:50:00', 'unit': 'mg/dL'}, glucose[12])
        self.assertAlmostEqual(152.23, glucose[12]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T11:50:00', 'unit': 'mg/dL'}, glucose[24])
        self.assertAlmostEqual(179.03, glucose[24]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T12:50:00', 'unit': 'mg/dL'}, glucose[36])
        self.assertAlmostEqual(159.70, glucose[36]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T14:35:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(120.70, glucose[-1]['amount'], delta=0.01)

    def test_momentum_up(self):
        momentum = [
            {
                'date': '2015-10-16T09:50:00',
                'amount': 0.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T09:55:00',
                'amount': 3.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:00:00',
                'amount': 6.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:05:00',
                'amount': 9.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:10:00',
                'amount': 12.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:15:00',
                'amount': 15.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:20:00',
                'amount': 18.0,
                'unit': 'mg/dL'
            }
        ]

        glucose = calculate_glucose_from_effects(
            [self.carb_effect, self.insulin_effect],
            [{
                "trend_arrow": "FLAT",
                "system_time": "2015-10-16T16:51:46",
                "display_time": "2015-10-16T09:51:08",
                "glucose": 147
            }],
            momentum=momentum
        )

        self.assertDictEqual({'date': '2015-10-16T09:51:08', 'amount': 147.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-10-16T09:55:00', 'unit': 'mg/dL'}, glucose[1])
        self.assertAlmostEqual(149.58, glucose[1]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T10:00:00', 'unit': 'mg/dL'}, glucose[2])
        self.assertAlmostEqual(151.56, glucose[2]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T10:50:00', 'unit': 'mg/dL'}, glucose[12])
        self.assertAlmostEqual(158.97, glucose[12]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T11:50:00', 'unit': 'mg/dL'}, glucose[24])
        self.assertAlmostEqual(185.75, glucose[24]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T12:50:00', 'unit': 'mg/dL'}, glucose[36])
        self.assertAlmostEqual(166.42, glucose[36]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T14:35:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(127.43, glucose[-1]['amount'], delta=0.01)

    def test_momentum_down(self):
        momentum = [
            {
                'date': '2015-10-16T09:50:00',
                'amount': -0.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T09:55:00',
                'amount': -3.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:00:00',
                'amount': -6.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:05:00',
                'amount': -9.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:10:00',
                'amount': -12.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:15:00',
                'amount': -15.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-16T10:20:00',
                'amount': -18.0,
                'unit': 'mg/dL'
            }
        ]

        glucose = calculate_glucose_from_effects(
            [self.carb_effect, self.insulin_effect],
            [{
                "trend_arrow": "FLAT",
                "system_time": "2015-10-16T16:51:46",
                "display_time": "2015-10-16T09:51:08",
                "glucose": 147
            }],
            momentum=momentum
        )

        self.assertDictEqual({'date': '2015-10-16T09:51:08', 'amount': 147.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-10-16T09:55:00', 'unit': 'mg/dL'}, glucose[1])
        self.assertAlmostEqual(144.51, glucose[1]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T10:00:00', 'unit': 'mg/dL'}, glucose[2])
        self.assertAlmostEqual(142.62, glucose[2]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T10:50:00', 'unit': 'mg/dL'}, glucose[12])
        self.assertAlmostEqual(145.60, glucose[12]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T11:50:00', 'unit': 'mg/dL'}, glucose[24])
        self.assertAlmostEqual(172.40, glucose[24]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T12:50:00', 'unit': 'mg/dL'}, glucose[36])
        self.assertAlmostEqual(153.07, glucose[36]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T14:35:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(114.07, glucose[-1]['amount'], delta=0.01)

    def test_momentum_empty(self):
        glucose = calculate_glucose_from_effects(
            [self.carb_effect, self.insulin_effect],
            [{
                "trend_arrow": "FLAT",
                "system_time": "2015-10-16T16:51:46",
                "display_time": "2015-10-16T09:51:08",
                "glucose": 147
            }],
            momentum=[]
        )

        self.assertDictEqual({'date': '2015-10-16T09:51:08', 'amount': 147.0, 'unit': 'mg/dL'}, glucose[0])
        self.assertDictContainsSubset({'date': '2015-10-16T09:55:00', 'unit': 'mg/dL'}, glucose[1])
        self.assertAlmostEqual(147.31, glucose[1]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T10:50:00', 'unit': 'mg/dL'}, glucose[12])
        self.assertAlmostEqual(152.56, glucose[12]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T11:50:00', 'unit': 'mg/dL'}, glucose[24])
        self.assertAlmostEqual(179.35, glucose[24]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T12:50:00', 'unit': 'mg/dL'}, glucose[36])
        self.assertAlmostEqual(160.03, glucose[36]['amount'], delta=0.01)
        self.assertDictContainsSubset({'date': '2015-10-16T14:35:00', 'unit': 'mg/dL'}, glucose[-1])
        self.assertAlmostEqual(121.04, glucose[-1]['amount'], delta=0.01)


class CalculateMomentumEffectTestCase(unittest.TestCase):
    def test_rising_glucose(self):
        glucose = [
            {
                'date': '2015-10-25T19:30:00',
                'amount': 129
            },
            {
                'date': '2015-10-25T19:25:00',
                'amount': 126
            },
            {
                'date': '2015-10-25T19:20:00',
                'amount': 123
            },
            {
                'date': '2015-10-25T19:15:00',
                'amount': 120
            }
        ]

        momentum = calculate_momentum_effect(glucose)

        self.assertListEqual(
            [
                {
                    'date': '2015-10-25T19:30:00',
                    'amount': 0.0,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:35:00',
                    'amount': 3,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:40:00',
                    'amount': 6,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:45:00',
                    'amount': 9,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:50:00',
                    'amount': 12,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:55:00',
                    'amount': 15,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T20:00:00',
                    'amount': 18,
                    'unit': 'mg/dL'
                }
            ],
            momentum
        )

    def test_bouncing_glucose(self):
        glucose = [
            {
                'date': '2015-10-25T19:30:00',
                'amount': 129
            },
            {
                'date': '2015-10-25T19:25:00',
                'amount': 120
            },
            {
                'date': '2015-10-25T19:20:00',
                'amount': 123
            },
            {
                'date': '2015-10-25T19:15:00',
                'amount': 126
            }
        ]

        momentum = calculate_momentum_effect(glucose)

        self.assertListEqual(
            [
                {
                    'date': '2015-10-25T19:30:00',
                    'amount': 0.0,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:35:00',
                    'amount': 3,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:40:00',
                    'amount': 6,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:45:00',
                    'amount': 9,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:50:00',
                    'amount': 12,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:55:00',
                    'amount': 15,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T20:00:00',
                    'amount': 18,
                    'unit': 'mg/dL'
                }
            ],
            momentum
        )

    def test_falling_glucose(self):
        glucose = [
            {
                'date': '2015-10-25T19:30:00',
                'amount': 120
            },
            {
                'date': '2015-10-25T19:25:00',
                'amount': 123
            },
            {
                'date': '2015-10-25T19:20:00',
                'amount': 126
            },
            {
                'date': '2015-10-25T19:15:00',
                'amount': 129
            }
        ]

        momentum = calculate_momentum_effect(glucose)

        self.assertListEqual(
            [
                {
                    'date': '2015-10-25T19:30:00',
                    'amount': 0.0,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:35:00',
                    'amount': -3,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:40:00',
                    'amount': -6,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:45:00',
                    'amount': -9,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:50:00',
                    'amount': -12,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:55:00',
                    'amount': -15,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T20:00:00',
                    'amount': -18,
                    'unit': 'mg/dL'
                }
            ],
            momentum
        )

    def test_stable_glucose(self):
        glucose = [
            {
                'date': '2015-10-25T19:30:00',
                'amount': 120
            },
            {
                'date': '2015-10-25T19:25:00',
                'amount': 120
            },
            {
                'date': '2015-10-25T19:20:00',
                'amount': 120
            },
            {
                'date': '2015-10-25T19:15:00',
                'amount': 123
            }
        ]

        momentum = calculate_momentum_effect(glucose)

        self.assertListEqual(
            [
                {
                    'date': '2015-10-25T19:30:00',
                    'amount': 0.0,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:35:00',
                    'amount': 0.0,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:40:00',
                    'amount': 0.0,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:45:00',
                    'amount': 0.0,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:50:00',
                    'amount': 0.0,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T19:55:00',
                    'amount': 0.0,
                    'unit': 'mg/dL'
                },
                {
                    'date': '2015-10-25T20:00:00',
                    'amount': 0.0,
                    'unit': 'mg/dL'
                }
            ],
            momentum
        )

    def test_missing_number_of_entries(self):
        glucose = [
            {
                'date': '2015-10-25T19:30:00',
                'amount': 120
            },
            {
                'date': '2015-10-25T19:25:00',
                'amount': 120
            }
        ]

        momentum = calculate_momentum_effect(glucose)

        self.assertListEqual([], momentum)

    def test_missing_range_of_entries(self):
        glucose = [
            {
                'date': '2015-10-25T19:30:00',
                'amount': 120
            },
            {
                'date': '2015-10-25T19:20:00',
                'amount': 120
            },
            {
                'date': '2015-10-25T19:14:59',
                'amount': 120
            },
            {
                'date': '2015-10-25T19:10:00',
                'amount': 123
            }
        ]

        momentum = calculate_momentum_effect(glucose)

        self.assertListEqual([], momentum)

    def test_recent_calibrations(self):
        with open(get_file_at_path('fixtures/cgms_calibrations.json')) as fp:
            calibrations = json.load(fp)

        glucose = [
            {
                "trend_arrow": "FLAT",
                "system_time": "2015-10-28T01:16:47",
                "display_time": "2015-10-27T17:17:38",
                "glucose": 147
            },
            {
                "trend_arrow": "FLAT",
                "system_time": "2015-10-28T01:16:47",
                "display_time": "2015-10-27T17:17:38",
                "glucose": 153
            },
            {
                "trend_arrow": "FLAT",
                "system_time": "2015-10-28T01:11:46",
                "display_time": "2015-10-27T17:12:37",
                "glucose": 146
            },
            {
                "trend_arrow": "FLAT",
                "system_time": "2015-10-28T01:06:45",
                "display_time": "2015-10-27T17:07:37",
                "glucose": 148
            },
            {
                "trend_arrow": "FLAT",
                "system_time": "2015-10-28T01:01:46",
                "display_time": "2015-10-27T17:02:38",
                "glucose": 149
            }
        ]

        momentum = calculate_momentum_effect(glucose, recent_calibrations=calibrations)

        self.assertListEqual([], momentum)

    def test_timestamp_rounding(self):
        glucose = [
            {
                "trend_arrow": "FLAT",
                "system_time": "2015-10-28T01:16:47",
                "display_time": "2015-10-27T17:17:38",
                "glucose": 153
            },
            {
                "trend_arrow": "FLAT",
                "system_time": "2015-10-28T01:11:46",
                "display_time": "2015-10-27T17:12:37",
                "glucose": 146
            },
            {
                "trend_arrow": "FLAT",
                "system_time": "2015-10-28T01:06:45",
                "display_time": "2015-10-27T17:07:37",
                "glucose": 148
            },
            {
                "trend_arrow": "FLAT",
                "system_time": "2015-10-28T01:01:46",
                "display_time": "2015-10-27T17:02:38",
                "glucose": 149
            }
        ]

        momentum = calculate_momentum_effect(glucose)

        self.assertListEqual([
            {
                'date': '2015-10-27T17:15:00',
                'amount': 0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-27T17:20:00',
                'amount': 2.5,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-27T17:25:00',
                'amount': 5.0,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-27T17:30:00',
                'amount': 7.49,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-27T17:35:00',
                'amount': 9.99,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-27T17:40:00',
                'amount': 12.49,
                'unit': 'mg/dL'
            },
            {
                'date': '2015-10-27T17:45:00',
                'amount': 14.99,
                'unit': 'mg/dL'
            }
        ], [{'date': m['date'], 'unit': m['unit'], 'amount': round(m['amount'], 2)} for m in momentum])
