"""This file contains configuration tests"""
from configparser import ConfigParser
import os
import unittest

from stacking.errors import ReaderError
from stacking.reader import Reader
from stacking.readers.dr16_reader import Dr16Reader, SUPPORTED_READING_MODES
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
    run_dr16_reader_with_errors
    run_dr16_reader_without_errors
    test_dr16_reader_best_obs
    test_dr16_reader_missing_options
    test_dr16_reader_no_spectra
    test_dr16_reader_read_drq_issues
    test_dr16_reader_spall_issues
    test_dr16_reader_spec
    test_dr16_reader_spplate
    test_dr16_reader_unsupported_reading_mode
    test_reader
    test_reader_missing_options
    """

    def run_dr16_reader_with_errors(self, reader_kwargs, expected_message):
        """Check behaviour of Dr16Reader when errors are expected

        Arguments
        ---------
        reader_kwargs: dict
        Keyword arguments to set the configuration run

        expected_message: str
        Expected error message
        """
        config = create_dr16_reader_config(reader_kwargs)

        with self.assertRaises(ReaderError) as context_manager:
            reader = Dr16Reader(config["reader"])
            reader.read_data()
        self.compare_error_message(context_manager, expected_message)

    def run_dr16_reader_without_errors(self, reader_kwargs, size_catalogue,
                                       num_spectra, mode):
        """Check behaviour of Dr16Reader when no errors are expected

        Arguments
        ---------
        reader_kwargs: dict
        Keyword arguments to set the configuration run

        size_catalogue: int
        Size of the loaded catalgoue

        num_spectra: int
        Number of loaded spectra

        mode: str
        Reading mode
        """
        config = create_dr16_reader_config(reader_kwargs)

        reader = Dr16Reader(config["reader"])
        spectra = reader.read_data()

        self.assertTrue(len(reader.catalogue) == size_catalogue)
        self.assertTrue(len(reader.spectra) == num_spectra)
        self.assertTrue(reader.read_mode == mode)
        self.assertTrue(len(spectra) == num_spectra)
        self.assertTrue(
            all(isinstance(spectrum, Spectrum) for spectrum in spectra))

    def test_dr16_reader_best_obs(self):
        """Check the best_obs mode"""
        reader_kwargs = DR16_READER_KWARGS.copy()
        reader_kwargs.update({"best obs": "True"})
        self.run_dr16_reader_without_errors(reader_kwargs, 79, 79, "spplate")

    def test_dr16_reader_missing_options(self):
        """Check that errors are raised when required options are missing
        in Dr16Reader"""
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

    def test_dr16_reader_no_spectra(self):
        """Check that errors are raised when no spectra are found"""
        reader_kwargs = DR16_READER_KWARGS.copy()
        reader_kwargs.update({
            "spAll": f"{THIS_DIR}/data/spAll-plate3655.fits",
            "input directory": "non/existent",
        })
        expected_message = (
            "No spectra were read, check the logs for more details")
        self.run_dr16_reader_with_errors(reader_kwargs, expected_message)

    def test_dr16_reader_read_drq_issues(self):
        """Check that errors are raised when there are issues loading the
        the DRQ quasar catalogue"""

        drq_catalogues = [
            f"{THIS_DIR}/data/drq_catalogue_plate3655_zvi.fits.gz",
            f"{THIS_DIR}/data/drq_catalogue_plate3655_noz.fits.gz",
            f"{THIS_DIR}/data/drq_catalogue_plate3655_bal_flag_vi.fits.gz",
            f"{THIS_DIR}/data/drq_catalogue_plate3655_nobi_civ.fits.gz",
            f"{THIS_DIR}/data/drq_catalogue_plate3655_bi_civ.fits.gz",
        ]
        expectations = [
            79,
            ("Error in reading DRQ Catalogue. No valid column for "
             f"redshift found in {drq_catalogues[1]}"),
            1,
            ("Error in reading DRQ Catalogue. 'BI max' was passed but "
             "field BI_CIV was not present in the HDU"),
            77,
        ]

        for drq_catalogue, expectation in zip(drq_catalogues, expectations):
            reader_kwargs = DR16_READER_KWARGS.copy()
            reader_kwargs.update({
                "drq catalogue": drq_catalogue,
                "best obs": "True",
            })
            if "bi_civ" in drq_catalogue:
                reader_kwargs.update({"max balnicity index": 0.5})
            if isinstance(expectation, int):
                self.run_dr16_reader_without_errors(reader_kwargs, expectation,
                                                    expectation, "spplate")
            else:
                self.run_dr16_reader_with_errors(reader_kwargs, expectation)

    def test_dr16_reader_spall_issues(self):
        """Check that errors are raised when there are issues with the
        spAll file"""

        input_directories = [
            f"{THIS_DIR}/data/config_tests",  # missing spAll file
            f"{THIS_DIR}/data/spAll_multiple_files",  #multiple files
        ]

        for input_directory in input_directories:
            reader_kwargs = DR16_READER_KWARGS.copy()
            reader_kwargs.update({"input directory": input_directory})
            expected_message = "Missing argument 'spAll' required by Dr16Reader"
            self.run_dr16_reader_with_errors(reader_kwargs, expected_message)

        # specifying non-exitant file
        reader_kwargs = DR16_READER_KWARGS.copy()
        reader_kwargs.update({"spall": "missing.fits.gz"})
        expected_message = (
            "Error in reading spAll catalogue. Error "
            "reading file missing.fits.gz. IOError "
            "message: [Errno 2] No such file or directory: 'missing.fits.gz'")
        self.run_dr16_reader_with_errors(reader_kwargs, expected_message)

    def test_dr16_reader_spec(self):
        """Test SdssData when run in spec mode"""
        reader_kwargs = DR16_READER_KWARGS.copy()
        reader_kwargs.update({"read mode": "spec"})
        self.run_dr16_reader_without_errors(reader_kwargs, 93, 78, "spec")

    def test_dr16_reader_spplate(self):
        """Tests Dr16Reader when run in spplate mode"""
        # using default  value for 'mode'
        self.run_dr16_reader_without_errors(DR16_READER_KWARGS, 93, 92, "spplate")

        # specifying 'mode'
        reader_kwargs = DR16_READER_KWARGS.copy()
        reader_kwargs.update({"mode": "spplate"})
        self.run_dr16_reader_without_errors(reader_kwargs, 93, 92, "spplate")

    def test_dr16_reader_unsupported_reading_mode(self):
        """Check that Dr16Reader raises errors when the reading mode is not
        supported"""
        reader_kwargs = DR16_READER_KWARGS.copy()
        reader_kwargs.update({"read mode": "unsupported"})
        expected_message = (
            "Error reading data in Dr16Reader. Read mode unsupported is not "
            "supported. Supported reading modes are " +
            " ".join(SUPPORTED_READING_MODES))
        self.run_dr16_reader_with_errors(reader_kwargs, expected_message)

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
        """Check that errors are raised when required options are missing
        in Reader"""
        options_and_values = [
            ("input directory", f"{THIS_DIR}/data/"),
        ]

        self.check_missing_options(options_and_values, Reader, ReaderError)


def create_dr16_reader_config(reader_kwargs):
    """Create a configuration instance to run Dr16Reader

    Arguments
    ---------
    reader_kwargs: dict
    Keyword arguments to set the configuration run

    Return
    ------
    config: ConfigParser
    Run configuration
    """
    config = ConfigParser()
    config.read_dict({"reader": reader_kwargs})
    for key, value in defaults_dr16_reader.items():
        if key not in config["reader"]:
            config["reader"][key] = str(value)

    return config

if __name__ == '__main__':
    unittest.main()
