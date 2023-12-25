"""This file contains stacker tests"""
import os
import unittest

import numpy as np
import pandas as pd

from stacking.stackers.split_stacker_utils import (
    assign_group_multiple_cuts,
    assign_group_one_cut,
    extract_split_cut_sets,
    find_interval_index,
    format_split_on,
    format_splits,
    retreive_group_number,
)
from stacking.tests.abstract_test import AbstractTest, highlight_print

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR

ASSIGN_GROUP_DATA = pd.DataFrame.from_dict({
    "var 1": np.arange(10) + 10,
    "var 2": np.array([-0.5, -0.4, 0.3, 0.1, -0.45] * 2),
    "var 3": np.arange(10),
})


class SplitStackerUtilsTest(AbstractTest):
    """Test the SplitStacker utils

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    test_assign_group_multiple_cuts
    test_assign_group_one_cut
    test_extract_split_cut_sets
    test_find_interval_index
    test_format_split_on
    test_format_splits
    test_retreive_group
    """

    def test_assign_group_multiple_cuts(self):
        """Test function assign_group_multiple_cuts"""
        tests = [
            { # single variable
                "variables": ["var 1"],
                "intervals": [np.array([12, 13, 14, 18], dtype=float)],
                "num_intervals": np.array([3]),
                "expectations": np.array([-1, -1, 0, 1, 2, 2, 2, 2, -1, -1]),
            },
            { # two variables
                "variables": ["var 1", "var 2"],
                "intervals": [np.array([12, 13, 14, 18], dtype=float),
                              np.array([-0.45, 0.0, 0.45])],
                "num_intervals": np.array([3, 2]),
                "expectations": np.array([-1, -1, 3, 4, 2, -1, 2, 5, -1, -1]),
            },
            { # three variables
                "variables": ["var 1", "var 2", "var 3"],
                "intervals": [np.array([12, 13, 14, 18], dtype=float),
                              np.array([-0.45, 0.0, 0.45]),
                              np.array([6, 7, 8, 9], dtype=float)],
                "num_intervals": np.array([3, 2]),
                "expectations": np.array([-1, -1, -1, -1, -1, -1, 2, 11, -1, -1]),
            },
        ]

        for test in tests:
            output = ASSIGN_GROUP_DATA.apply(assign_group_multiple_cuts,
                                             axis=1,
                                             args=(test.get("variables"),
                                                   test.get("intervals"),
                                                   test.get("num_intervals")))

            self.assertTrue(np.allclose(output, test.get("expectations")))

    def test_assign_group_one_cut(self):
        """Test function assign_group_one_cut"""

        tests = [(0, np.array([-1, -1, 0, 1, 2, 2, 2, 2, -1, -1])),
                 (15, np.array([-1, -1, 15, 16, 17, 17, 17, 17, -1, -1]))]

        for offset, expectations in tests:
            output = ASSIGN_GROUP_DATA.apply(assign_group_one_cut,
                                             axis=1,
                                             args=("var 1",
                                                   np.array([12, 13, 14, 18],
                                                            dtype=float),
                                                   offset))

            self.assertTrue(np.allclose(output, expectations))

    def test_extract_split_cut_sets(self):
        """Test function extract_split_cut_sets"""
        tests = [
            # single set
            ("1 2 3 4", ["1 2 3 4"]),
            # two sets
            ("1.1, 2.2; 3.3, 4.4", ["1.1, 2.2", "3.3, 4.4"]),
            # three sets
            ("1.1, 2.2; 3.3, 4.4; 5.5, 6", ["1.1, 2.2", "3.3, 4.4", "5.5, 6"]),
        ]

        for value, expectation in tests:
            splits_cuts_sets = extract_split_cut_sets(value)

            if splits_cuts_sets != expectation:
                highlight_print()
                print("Incorrect extraction of split cut sets. Expected "
                      f"{expectation}. Found {splits_cuts_sets}")
                self.fail("Extract split_cut_sets: incorrect formatting")

    def test_find_interval_index(self):
        """Test function find_interval_index"""
        intervals = np.arange(5, dtype=float) + 10

        # test different cases
        tests = [
            (5.0, -1),
            (5, -1),
            (10.5, 0),
            (11.0, 1),
        ]

        for value, expectation in tests:
            output = find_interval_index(value, intervals)
            if not np.isclose(output, expectation):
                highlight_print()
                print(f"Found incorrect inteval index. For value {value} and "
                      f"intervals {intervals} I expected {expectation}. Found "
                      f"{output}")
                self.fail("Find interval index: wrong index")

            output_python = find_interval_index.py_func(value, intervals)
            self.assertTrue(np.allclose(output, output_python))

    def test_format_split_on(self):
        """Test function format_split_on"""
        # test different cases
        tests = [
            # single split
            ("Z", ["Z"]),
            ("z", ["Z"]),
            # multiple splits using space
            ("Z BI_CIV", ["Z", "BI_CIV"]),
            ("z bi_civ", ["Z", "BI_CIV"]),
            ("Z BI_CIV RA", ["Z", "BI_CIV", "RA"]),
            # multiple splits using comma
            ("Z,BI_CIV", ["Z", "BI_CIV"]),
            ("z,bi_civ", ["Z", "BI_CIV"]),
            ("Z,BI_CIV,RA", ["Z", "BI_CIV", "RA"]),
            # multiple splits using semicolon
            ("Z;BI_CIV", ["Z", "BI_CIV"]),
            ("z;bi_civ", ["Z", "BI_CIV"]),
            ("Z;BI_CIV;RA", ["Z", "BI_CIV", "RA"]),
            # multiple splits using multiple separators
            ("Z; BI_CIV", ["Z", "BI_CIV"]),
            ("z, bi_civ", ["Z", "BI_CIV"]),
            ("Z;BI_CIV RA", ["Z", "BI_CIV", "RA"]),
        ]

        for value, expectation in tests:
            split_on = format_split_on(value)

            if split_on != expectation:
                highlight_print()
                print("Incorrect formatting of variable 'split on'. Expected "
                      f"{expectation}. Found {split_on}")
                self.fail("Format split_on: incorrect formatting")

    def test_format_splits(self):
        """Test function format_splits"""
        # test different cases
        tests = [
            # single set
            (["1 2 3 4"], [np.array([1, 2, 3, 4], dtype=float)]),
            (["1.1 2.2 3.3 4.4"], [np.array([1.1, 2.2, 3.3, 4.4])]),
            (["1.1,2.2,3.3,4.4"], [np.array([1.1, 2.2, 3.3, 4.4])]),
            (["1.1, 2.2, 3.3, 4.4"], [np.array([1.1, 2.2, 3.3, 4.4])]),
            (["[1.1, 2.2, 3.3, 4.4]"], [np.array([1.1, 2.2, 3.3, 4.4])]),
            # two sets
            (["1.1, 2.2",
              "3.3, 4.4"], [np.array([1.1, 2.2]),
                            np.array([3.3, 4.4])]),
            (["[1.1, 2.2]",
              "[3.3, 4.4]"], [np.array([1.1, 2.2]),
                              np.array([3.3, 4.4])]),
            # three sets
            (["1.1, 2.2", "3.3, 4.4", "5.5, 6"],
             [np.array([1.1, 2.2]),
              np.array([3.3, 4.4]),
              np.array([5.5, 6.0])]),
            (["[1.1, 2.2]", "[3.3, 4.4]", "[5.5, 6]"],
             [np.array([1.1, 2.2]),
              np.array([3.3, 4.4]),
              np.array([5.5, 6.0])]),
        ]

        for value, expectations in tests:
            splits = format_splits(value)

            if len(splits) != len(expectations):
                highlight_print()
                print("Incorrect formatting of 'splits'. Expected "
                      f"a list of {len(expectations)} items. Found "
                      f"{len(splits)} items instead.\nInput string: {value}\n"
                      f"Expected output: {expectations}")
                self.fail("Format splits: incorrect number of items")

            for split, expectation in zip(splits, expectations):
                if not isinstance(split, np.ndarray):
                    highlight_print()
                    print(
                        "Incorrect formatting of 'splits'. List items are "
                        f"expected to be arrays. Found:{split}\nInput string: "
                        f"{value}\n")
                    self.fail("Format splits: item not an array")
                if not np.allclose(split, expectation):
                    highlight_print()
                    print(
                        "Incorrect loading of 'splits'. Format is fine but cuts"
                        f"do not meet expectations. Found {split}. Expected "
                        f"{expectation}")
                    self.fail("Format splits: incorrect cuts")

    def test_retreive_group_number(self):
        """Test function retreive_group_number"""
        specid = 12345678
        specids = np.array(
            [31345346264346, 12345678, 4522457457457, 4574573543457], dtype=int)
        groups = np.array([-1, 0, 5, 1])
        expected_value = 0

        output = retreive_group_number(specid, specids, groups)
        self.assertTrue(output == expected_value)

        output = retreive_group_number.py_func(specid, specids, groups)
        self.assertTrue(output == expected_value)


if __name__ == '__main__':
    unittest.main()
