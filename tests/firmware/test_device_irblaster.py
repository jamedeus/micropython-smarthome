import os
import unittest
from ir_tx import Player
from IrBlaster import IrBlaster
from cpython_only import cpython_only
from util import read_ir_macros_from_disk


class TestIrBlaster(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = IrBlaster("4", ["samsung_tv", "whynter_ac"])

        try:
            os.remove('ir_macros.json')
        except OSError:
            pass

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove('ir_macros.json')
        except OSError:
            pass

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, IrBlaster)
        self.assertIsInstance(self.instance.ir, Player)
        self.assertEqual(len(self.instance.codes), 2)
        self.assertEqual(len(self.instance.codes['whynter_ac']), 3)
        self.assertEqual(len(self.instance.codes['samsung_tv']), 12)

    def test_02_send_valid(self):
        # Test keys that exist
        self.assertTrue(self.instance.send("samsung_tv", "power"))
        self.assertTrue(self.instance.send("samsung_tv", "vol_down"))
        self.assertTrue(self.instance.send("samsung_tv", "vol_up"))
        self.assertTrue(self.instance.send("whynter_ac", "OFF"))
        self.assertTrue(self.instance.send("whynter_ac", "start"))

    def test_03_send_invalid(self):
        # Test keys that don't exist
        self.assertFalse(self.instance.send("samsung_tv", "on"))
        self.assertFalse(self.instance.send("samsung_tv", "vol_mute"))
        self.assertFalse(self.instance.send("whynter_ac", "cool"))
        self.assertFalse(self.instance.send("whynter_ac", "hot"))
        self.assertFalse(self.instance.send("whynter_ac", 2))
        self.assertFalse(self.instance.send(5, "foo"))

    def test_04_create_macro(self):
        # Confirm no macros
        self.assertEqual(len(self.instance.macros), 0)

        # Add macro, confirm added to dict
        self.instance.create_macro('test1')
        self.assertEqual(len(self.instance.macros), 1)
        self.assertEqual(self.instance.macros['test1'], [])

    def test_05_create_duplicate_macro(self):
        self.assertEqual(len(self.instance.macros), 1)

        # Confirm exception raised when existing name added again
        with self.assertRaises(ValueError):
            self.instance.create_macro('test1')

        # Confirm not added
        self.assertEqual(len(self.instance.macros), 1)

    def test_06_add_macro_action(self):
        # Confirm empty macro
        self.assertEqual(self.instance.macros['test1'], [])

        # Add action, omit optional args, confirm added with correct defaults
        self.instance.add_macro_action('test1', 'samsung_tv', 'power')
        self.assertEqual(self.instance.macros['test1'][0], ('samsung_tv', 'power', 0, 1))

        # Add action with option args, confirm added correctly
        self.instance.add_macro_action('test1', 'samsung_tv', 'vol_up', 50, 3)
        self.assertEqual(self.instance.macros['test1'][1], ('samsung_tv', 'vol_up', 50, 3))

    def test_07_add_macro_action_errors(self):
        self.assertEqual(len(self.instance.macros['test1']), 2)
        # Confirm exception raised when trying to add to non-existing macro
        with self.assertRaises(ValueError):
            self.instance.add_macro_action('test99', 'samsung_tv', 'power')

        # Confirm exception raised when adding action with invalid target
        with self.assertRaises(ValueError):
            self.instance.add_macro_action('test1', 'refrigerator', 'power')

        # Confirm exception raised when adding action with invalid key
        with self.assertRaises(ValueError):
            self.instance.add_macro_action('test1', 'samsung_tv', 'fake')

        # Confirm exception raised if delay arg is not integer
        with self.assertRaises(ValueError):
            self.instance.add_macro_action('test1', 'samsung_tv', 'power', 'short')

        # Confirm exception raised if repeat arg is not integer
        with self.assertRaises(ValueError):
            self.instance.add_macro_action('test1', 'samsung_tv', 'power', '150', 'yes')

        # Confirm no actions added
        self.assertEqual(len(self.instance.macros['test1']), 2)

    def test_08_run_macro(self):
        # Run macro created in previous tests
        self.instance.run_macro('test1')

    def test_09_run_macro_errors(self):
        # Confirm exception raised when trying to run non-existing macro
        with self.assertRaises(ValueError):
            self.instance.run_macro('test99')

    def test_10_save_macros(self):
        # Confirm no macros in config
        macros = read_ir_macros_from_disk()
        self.assertEqual(len(macros), 0)

        # Save macros, confirm written to config file on disk
        self.instance.save_macros()
        macros = read_ir_macros_from_disk()
        self.assertEqual(len(macros), 1)

    def test_11_delete_macro(self):
        # Confirm macro exists
        self.assertEqual(len(self.instance.macros), 1)

        # Delete, confirm removed
        self.instance.delete_macro('test1')
        self.assertEqual(len(self.instance.macros), 0)

    def test_12_delete_macro_errors(self):
        # Confirm exception raised when trying to delete non-existing macro
        with self.assertRaises(ValueError):
            self.instance.delete_macro('test99')

    @cpython_only
    def test_13_instantiate_with_invalid_targets(self):
        # Confirm ValueError raised when instantiated with invalid targets
        with self.assertRaises(ValueError):
            IrBlaster("4", ["samsung_tv", "invalid"])

    # Original bug: run_macro method did not cast delay and repeats
    # params to int, resulting in uncaught exception if params were
    # string representations of integers.
    def test_14_regression_string_delay_and_repeat(self):
        # Add macro with string ints for delay and repeat
        self.instance.macros['regression_test'] = [
            ('samsung_tv', 'power', '5', '1')
        ]
        # Run macro, should not raise exception
        self.instance.run_macro('regression_test')
