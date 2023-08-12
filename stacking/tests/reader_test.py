"""This file contains configuration tests"""
from configparser import ConfigParser
import os
import unittest

from stacking.errors import ReaderError
from stacking.reader import Reader
from stacking.readers.dr16_reader import Dr16Reader
from stacking.readers.dr16_reader import defaults as defaults_dr16_reader
from stacking.spectrum import Spectrum
from stacking.tests.abstract_test import AbstractTest

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR

DR16_READER_KWARGS = {
    "drq catalogue": f"{THIS_DIR}/data/drq_catalogue_plate3655.fits.gz",
    "input directory": f"{THIS_DIR}/data",
}


class ReaderTest(AbstractTest):
    """Test the readers.

    Methods
    -------
    (see AbstractTest in stacking/tests/abstract_test.py)
    test_config
    """

    def test_dr16_reader_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("input directory", f"{THIS_DIR}/data/"),
            ("best obs", "False"),
            ("drq catalogue",
             f"{THIS_DIR}/data/drq_catalogue_plate3655.fits.gz"),
            ("keep BAL", "False"),
            ("read mode", "spplate"),
            ("z max", "10.0"),
            ("z min", "0.0"),
        ]

        self.check_missing_options(options_and_values, Dr16Reader, ReaderError,
                                   Reader)

    def test_dr16_reader_spec(self):
        """Test SdssData when run in spec mode"""
        config = ConfigParser()
        reader_kwargs = DR16_READER_KWARGS.copy()
        reader_kwargs.update({"read mode": "spec"})
        config.read_dict({"reader": reader_kwargs})
        for key, value in defaults_dr16_reader.items():
            if key not in config["reader"]:
                config["reader"][key] = str(value)
        reader = Dr16Reader(config["reader"])
        spectra = reader.read_data()

        self.assertTrue(len(reader.catalogue) == 93)
        self.assertTrue(len(reader.spectra) == 79)
        self.assertTrue(reader.read_mode == "spec")
        self.assertTrue(len(spectra) == 79)
        self.assertTrue(
            all(isinstance(spectrum, Spectrum) for spectrum in spectra))

    def test_dr16_reader_spplate(self):
        """Tests Dr16Reader when run in spplate mode"""
        # using default  value for 'mode'
        config = ConfigParser()
        config.read_dict({"reader": DR16_READER_KWARGS})
        for key, value in defaults_dr16_reader.items():
            if key not in config["reader"]:
                config["reader"][key] = str(value)
        reader = Dr16Reader(config["reader"])
        spectra = reader.read_data()

        self.assertTrue(len(reader.catalogue) == 93)
        self.assertTrue(len(reader.spectra) == 93)
        self.assertTrue(reader.read_mode == "spplate")
        self.assertTrue(len(spectra) == 93)
        self.assertTrue(
            all(isinstance(spectrum, Spectrum) for spectrum in spectra))

        # specifying 'mode'
        config = ConfigParser()
        reader_kwargs = DR16_READER_KWARGS.copy()
        reader_kwargs.update({"mode": "spplate"})
        config.read_dict({"reader": reader_kwargs})
        for key, value in defaults_dr16_reader.items():
            if key not in config["reader"]:
                config["reader"][key] = str(value)
        reader = Dr16Reader(config["reader"])
        spectra = reader.read_data()

        self.assertTrue(len(reader.catalogue) == 93)
        self.assertTrue(len(reader.spectra) == 93)
        self.assertTrue(reader.read_mode == "spplate")
        self.assertTrue(len(spectra) == 93)
        self.assertTrue(
            all(isinstance(spectrum, Spectrum) for spectrum in spectra))

    def test_reader(self):
        """Test the abstract reader"""
        config = ConfigParser()
        config.read_dict({"reader": {"input directory": f"{THIS_DIR}/data/"}})

        reader = Reader(config["reader"])

        self.assertTrue(len(reader.spectra) == 0)
        self.assertTrue(reader.catalogue is None)
        self.assertTrue(reader.input_directory == f"{THIS_DIR}/data/")

        expected_message = "Method 'read_data' was not overloaded by child class"
        with self.assertRaises(ReaderError) as context_manager:
            reader.read_data()
        self.compare_error_message(context_manager, expected_message)

    def test_reader_missing_options(self):
        """Check that errors are raised when required options are missing"""
        options_and_values = [
            ("input directory", f"{THIS_DIR}/data/"),
        ]

        self.check_missing_options(options_and_values, Reader, ReaderError)


if __name__ == '__main__':
    unittest.main()
