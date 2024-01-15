"""This file contains writer tests"""
from configparser import ConfigParser
from copy import copy
import os
import unittest

from stacking.errors import WriterError
from stacking.tests.abstract_test import AbstractTest
from stacking.tests.utils import stacker, split_stacker_or, split_stacker_and
from stacking.writer import Writer, ACCEPTED_SAVE_FORMATS
from stacking.writer import defaults as defaults_writer
from stacking.writers.split_writer import SplitWriter
from stacking.writers.standard_writer import StandardWriter

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR

WRITER_KWARGS = {
    "output directory": f"{THIS_DIR}/results/",
    "output file": "output_file.fits.gz",
    "overwrite": "True",
}


class WriterTest(AbstractTest):
    """Test the writers.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    test_standard_writer
    test_writer
    test_writer_missing_options
    test_writer_parse_options
    """

    def test_standard_writer(self):
        """Test the class StandardWriter"""
        out_dir = f"{THIS_DIR}/results/"
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        out_file = "standard_writer.fits.gz"
        test_file = f"{THIS_DIR}/data/standard_writer.fits.gz"

        config = create_writer_config({
            "output directory": out_dir,
            "output file": out_file,
            "overwrite": "True",
        })
        writer = StandardWriter(config["writer"])

        writer.write_results(stacker)

        self.compare_fits(test_file, out_dir + out_file)

    def test_split_writer(self):
        """Test the class SplitWriter"""
        out_dir = f"{THIS_DIR}/results/"
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # case 1: split type = 'or'
        out_file = "split_writer_or.fits.gz"
        test_file = f"{THIS_DIR}/data/split_writer_or.fits.gz"

        config = create_writer_config({
            "output directory": out_dir,
            "output file": out_file,
            "overwrite": "True",
        })
        writer = SplitWriter(config["writer"])
        writer.write_results(split_stacker_or)
        self.compare_fits(test_file, out_dir + out_file)

        # case 1: split type = 'and'
        out_file = "split_writer_and.fits.gz"
        test_file = f"{THIS_DIR}/data/split_writer_and.fits.gz"

        config = create_writer_config({
            "output directory": out_dir,
            "output file": out_file,
            "overwrite": "True",
        })
        writer = SplitWriter(config["writer"])
        writer.write_results(split_stacker_and)
        self.compare_fits(test_file, out_dir + out_file)

    def test_split_writer_no_column_desc(self):
        """Test the class SplitWriter when a some fields do not have
        column description"""
        out_dir = f"{THIS_DIR}/results/"
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        out_file = "split_writer_no_column_desc.fits.gz"
        test_file = f"{THIS_DIR}/data/split_writer_no_column_desc.fits.gz"

        config = create_writer_config({
            "output directory": out_dir,
            "output file": out_file,
            "overwrite": "True",
        })
        writer = SplitWriter(config["writer"])

        # modify catalogue in stacker so that some column names are not
        # in variable COLUMNS_DESCRIPTION
        split_stacker_mod = copy(split_stacker_or)
        split_stacker_mod.split_catalogue.rename(columns={"Z": "MISSING"},
                                                 inplace=True)

        writer.write_results(split_stacker_mod)

        self.compare_fits(test_file, out_dir + out_file)

    def test_writer(self):
        """Test the abstract writer"""
        writer = initialize_writer(WRITER_KWARGS)

        # calling normalize_spectrum should raise an error
        expected_message = (
            "Method 'write_results' was not overloaded by child class")
        with self.assertRaises(WriterError) as context_manager:
            writer.write_results(stacker)
        self.compare_error_message(context_manager, expected_message)

    def test_writer_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("output directory", f"{THIS_DIR}/results/"),
            ("output file", "output_file.fits.gz"),
            ("overwrite", "False"),
        ]

        self.check_missing_options(options_and_values, Writer, WriterError)

    def test_writer_parse_options(self):
        """Check behaviour of Writer.__parse_config"""
        # case: output directory does not end with /
        writer_kwargs = copy(WRITER_KWARGS)
        writer_kwargs.update({"output directory": f"{THIS_DIR}/results"})
        writer = initialize_writer(writer_kwargs)
        self.assertTrue(writer.output_directory == f"{THIS_DIR}/results/")

        # case: output file contains a folder
        writer_kwargs = copy(WRITER_KWARGS)
        writer_kwargs.update({"output file": "folder/output_file.fits.gz"})
        expected_message = ("Variable 'output file' should not incude folders. "
                            "Found: folder/output_file.fits.gz")
        with self.assertRaises(WriterError) as context_manager:
            initialize_writer(writer_kwargs)
        self.compare_error_message(context_manager, expected_message)

        # case: output file does not have a valid extension
        writer_kwargs = copy(WRITER_KWARGS)
        writer_kwargs.update({"output file": "output_file.invalid"})
        expected_message = (
            "Invalid extension for 'output file'. Expected one of " +
            " ".join(ACCEPTED_SAVE_FORMATS) +
            " Given filename: output_file.invalid")
        with self.assertRaises(WriterError) as context_manager:
            initialize_writer(writer_kwargs)
        self.compare_error_message(context_manager, expected_message)


def create_writer_config(rebin_kwargs):
    """Create a configuration instance to run Writer

    Arguments
    ---------
    writer_kwargs: dict
    Keyword arguments to set the configuration run

    Return
    ------
    config: ConfigParser
    Run configuration
    """
    config = ConfigParser()
    config.read_dict({"writer": rebin_kwargs})
    for key, value in defaults_writer.items():
        if key not in config["writer"]:
            config["writer"][key] = str(value)

    return config


def initialize_writer(writer_kwargs):
    """Initialize a writer instance

    Arguments
    ---------
    writer_kwargs: dict
    Keyword arguments to set the configuration run

    Return
    ------
    writer: Writer
    The writer instance
    """
    config = create_writer_config(writer_kwargs)
    writer = Writer(config["writer"])

    return writer


if __name__ == '__main__':
    unittest.main()
