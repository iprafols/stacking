"""This file contains an abstract class to define functions common to all tests"""
from configparser import ConfigParser
import os
import re
import unittest

from astropy.io import fits
import numpy as np
import pandas as pd

from stacking.logging_utils import setup_logger, reset_logger
from stacking.spectrum import Spectrum
from stacking.tests.utils import COMMON_WAVELENGTH_GRID

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class AbstractTest(unittest.TestCase):
    """Abstract test class to define functions used in all tests

    Methods
    -------
    (check unittest.TestCase)
    compare_ascii
    compare_fits
    setUp
    """

    def setUp(self):
        """ Actions done at test startup
        - Check that the results folder exists and create it
        if it does not.
        - Setup logger
        - Ensure Spectrum.common_wavelength_grid is defined
        """
        # setup results folder
        if not os.path.exists(f"{THIS_DIR}/results/"):
            os.makedirs(f"{THIS_DIR}/results/")

        # setup logger
        setup_logger()

        # setup Spectrum.common_wavelength_grid
        Spectrum.common_wavelength_grid = COMMON_WAVELENGTH_GRID

    def tearDown(self):
        """ Actions done at test end
        - Reset Spectrum.common_wavelength_grid
        - Reset logger
        """
        # reset Spectrum.common_wavelength_grid
        Spectrum.common_wavelength_grid = None

        reset_logger()

    def check_missing_options(self,
                              options_and_values,
                              test_class,
                              error_type,
                              parent_classes=None):
        """Check that errors are raised when required options are missing

        Arguments
        ---------
        options_and_values: list of tuples
        The tuples on the list are pairs of (option, value). They are added to
        the initializing config file iteratively and thus should be sorted

        test_class: class
        Class to be tested

        error_type: class
        Expected error type

        parent_classes: class or list of class - Default: []
        Parent(s) of the test class
        """
        if parent_classes is None:
            parent_classes = []
        elif not isinstance(parent_classes, list):
            parent_classes = [parent_classes]

        config = ConfigParser()
        config.read_dict({"test": {}})

        for option, value in options_and_values:
            # check that the error is raised
            expected_messages = [
                f"Missing argument '{option}' required by {test_class.__name__}"
            ]
            for parent_class in parent_classes:
                expected_messages.append(
                    f"Missing argument '{option}' required by {parent_class.__name__}"
                )
            with self.assertRaises(error_type) as context_manager:
                test_class(config["test"])

            self.compare_error_message(context_manager, expected_messages)

            # add the option to test the next option
            config["test"][option] = value

    def compare_ascii(self, orig_file, new_file):
        """Compare two ascii files to check that they are equal

        Arguments
        ---------
        orig_file: str
        Control file

        new_file: str
        New file

        expand_dir: bool - Default: False
        If set to true, replace the instances of the string 'THIS_DIR' by
        its value
        """
        with open(orig_file, 'r',
                  encoding="utf-8") as orig, open(new_file,
                                                  'r',
                                                  encoding="utf-8") as new:
            for orig_line, new_line in zip(orig.readlines(), new.readlines()):
                # this is necessary to remove the system dependent bits of
                # the paths
                if "py/picca/tests/delta_extraction" in orig_line:
                    orig_line = re.sub(r"\/[^ ]*\/stacking\/tests\/", "",
                                       orig_line)
                    new_line = re.sub(r"\/[^ ]*\/stacking\/tests\/", "",
                                      new_line)

                if not orig_line == new_line:
                    report_mismatch(orig_file, new_file)
                    print("Lines not equal")
                    print("Original line:")
                    print(orig_line)
                    print("New line:")
                    print(new_line)
                    self.fail()

    def compare_ascii_numeric(self, orig_file, new_file):
        """Compare two numeric ascii files to check that they are equal

        Arguments
        ---------
        orig_file: str
        Control file

        new_file: str
        New file

        expand_dir: bool - Default: False
        If set to true, replace the instances of the string 'THIS_DIR' by
        its value
        """
        orig_df = pd.read_csv(orig_file, delim_whitespace=True)
        new_df = pd.read_csv(orig_file, delim_whitespace=True)

        if orig_df.shape != new_df.shape:
            report_mismatch(orig_file, new_file)
            print("Read data has different shapes")
            print(f"Original shape: {orig_df.shape}")
            print(f"New shape: {new_df.shape}")
            self.fail()

        if any(orig_df.columns != new_df.columns):
            report_mismatch(orig_file, new_file)
            print("Different columns found")
            print(f"Original columns: {orig_df.columns}")
            print(f"New columns: {new_df.columns}")
            self.fail()

        for col in orig_df.columns:
            if not np.allclose(orig_df[col], new_df[col], equal_nan=True):
                report_mismatch(orig_file, new_file)
                print(f"Different data found for column {col}")
                print("orig new is_close orig-new\n")
                for index in orig_df.shape[1]:
                    print(
                        f"{orig_df[col][index]} {new_df[col][index]} "
                        f"{np.isclose(orig_df[col][index], new_df[col][index])} "
                        f"{orig_df[col][index] - new_df[col][index]}\n")
                self.fail()

    def compare_error_message(self,
                              context_manager,
                              expected_messages,
                              startswith=False):
        """Check the received error message is the same as the expected

        Arguments
        ---------
        context_manager: unittest.case._AssertRaisesContext
        Context manager when errors are expected to be raised.

        expected_messages: str or list of str
        Expected error message(s)

        startswith: bool - Default: False
        If True, check that one of the expected messages is the beginning of the
        actual error message. Otherwise check that one of the expected messages
        is the entire message
        """
        if not isinstance(expected_messages, list):
            expected_messages = [expected_messages]

        # remove system dependent bits of the expected messages
        for index, expected_message in enumerate(expected_messages):
            if "stacking/tests/" in expected_message:
                expected_messages[index] = re.sub(r"\/[^ ]*\/stacking\/tests\/",
                                                  "", expected_message)

        # remove system dependent bits of the received message
        received_message = str(context_manager.exception)
        if "stacking/tests/" in received_message:
            received_message = re.sub(r"\/[^ ]*\/stacking\/tests\/", "",
                                      received_message)

        if startswith:
            if not any(
                    received_message.startswith(expected_message)
                    for expected_message in expected_messages):
                print("\nReceived incorrect error message")
                print("Expected message to start with one of:")
                for expected_message in expected_messages:
                    print(expected_message)
                print("Received:")
                print(received_message)
            self.assertTrue(
                any(
                    received_message.startswith(expected_message)
                    for expected_message in expected_messages))
        else:
            if received_message not in expected_messages:
                print("\nReceived incorrect error message")
                print("Expected one of:")
                for expected_message in expected_messages:
                    print(expected_message)
                print("Received:")
                print(received_message)
            self.assertTrue(received_message in expected_messages)

    def compare_files(self, orig_file, new_file):
        """Compare two files to check that they are equal.

        This assumes the files contain numeric data

        This will call methods compare_ascii_numeric or compare_fits based
        on the file extension. The file extension is determined from
        the original file. The new file is assumed to have the same
        extension.

        Arguments
        ---------
        orig_file: str
        Control file

        new_file: str
        New file
        """
        # ascii files
        if orig_file.endswith(".txt") or orig_file.endswith(".csv"):
            self.compare_ascii_numeric(orig_file, new_file)
        # fits files
        elif orig_file.endswith(".fits") or orig_file.endswith(".fits.gz"):
            self.compare_fits(orig_file, new_file)
        # unkown
        else:
            report_mismatch(orig_file, new_file)
            print("Unrecognized file extension")

    def compare_fits(self, orig_file, new_file):
        """Compare two fits files to check that they are equal

        Arguments
        ---------
        orig_file: str
        Control file

        new_file: str
        New file
        """
        # open fits files
        orig_hdul = fits.open(orig_file)
        new_hdul = fits.open(new_file)
        try:
            # compare them
            if not len(orig_hdul) == len(new_hdul):
                self.report_fits_mismatch_hdul(orig_file, new_file, orig_hdul,
                                               new_hdul)

            # loop over HDUs
            for hdu_index, hdu in enumerate(orig_hdul):
                if "EXTNAME" in hdu.header:
                    hdu_name = hdu.header["EXTNAME"]
                else:
                    hdu_name = hdu_index
                # check header
                self.compare_fits_headers(orig_file, new_file,
                                          orig_hdul[hdu_name].header,
                                          new_hdul[hdu_name].header)
                # check data
                self.compare_fits_data(orig_file, new_file, orig_hdul[hdu_name],
                                       new_hdul[hdu_name])
        finally:
            orig_hdul.close()
            new_hdul.close()

    def compare_fits_data(self, orig_file, new_file, orig_hdu, new_hdu):
        """Compare the data of two HDUs

        Arguments
        ---------
        orig_file: str
        Control file. Used only for error reporting

        new_file: str
        New file. Used only for error reporting

        orig_hdu: fits.hdu.table.BinTableHDU or fits.hdu.image.ImageHDU
        Control header

        new_hdu: fits.hdu.table.BinTableHDU or fits.hdu.image.ImageHDU
        New header
        """
        orig_data = orig_hdu.data
        new_data = new_hdu.data

        # Empty HDU
        if orig_data is None:
            if new_data is not None:
                self.report_fits_mismatch_data(orig_file, new_file, orig_data,
                                               new_data,
                                               orig_hdu.header["EXTNAME"])

        # Image HDU
        elif orig_data.dtype.names is None:
            if not np.allclose(orig_data, new_data, equal_nan=True):
                self.report_fits_mismatch_data(orig_file, new_file, orig_data,
                                               new_data,
                                               orig_hdu.header["EXTNAME"])

        # Table HDU
        else:
            for col in orig_data.dtype.names:
                if not col in new_data.dtype.names:
                    self.report_fits_mismatch_data(orig_file,
                                                   new_file,
                                                   orig_data,
                                                   new_data,
                                                   orig_hdu.header["EXTNAME"],
                                                   col=col,
                                                   missing_col="new")
                self.assertTrue(col in new_data.dtype.names)
                # This is passed to np.allclose and np.isclose to properly handle IDs
                if col in ['LOS_ID', 'TARGETID', 'THING_ID']:
                    rtol = 0
                # This is the default numpy rtol value
                else:
                    rtol = 1e-5

                if (np.all(orig_data[col] != new_data[col]) and not np.allclose(
                        orig_data[col], new_data[col], equal_nan=True,
                        rtol=rtol)):
                    self.report_fits_mismatch_data(orig_file,
                                                   new_file,
                                                   orig_data,
                                                   new_data,
                                                   orig_hdu.header["EXTNAME"],
                                                   col=col,
                                                   rtol=rtol)
            for col in new_data.dtype.names:
                if col not in orig_data.dtype.names:
                    self.report_fits_mismatch_data(orig_file,
                                                   new_file,
                                                   orig_data,
                                                   new_data,
                                                   orig_hdu.header["EXTNAME"],
                                                   col=col,
                                                   missing_col="orig")

    def compare_fits_headers(self, orig_file, new_file, orig_header,
                             new_header):
        """Compare the headers of two HDUs

        Arguments
        ---------
        orig_file: str
        Control file. Used only for error reporting

        new_file: str
        New file. Used only for error reporting

        orig_header: fits.header.Header
        Control header

        new_header: fits.header.Header
        New header
        """
        for key in orig_header:
            if key not in new_header:
                self.report_fits_mismatch_header(orig_file,
                                                 new_file,
                                                 orig_header,
                                                 new_header,
                                                 key,
                                                 missing_key="new")
            if key in ["CHECKSUM", "DATASUM", "DATETIME"]:
                continue
            if (orig_header[key] != new_header[key] and
                (isinstance(orig_header[key], str) or
                 not np.isclose(orig_header[key], new_header[key]))):
                self.report_fits_mismatch_header(orig_file, new_file,
                                                 orig_header, new_header, key)
        for key in new_header:
            if key not in orig_header:
                self.report_fits_mismatch_header(orig_file,
                                                 new_file,
                                                 orig_header,
                                                 new_header,
                                                 key,
                                                 missing_key="orig")

    def report_fits_mismatch_data(self,
                                  orig_file,
                                  new_file,
                                  orig_data,
                                  new_data,
                                  hdu_name,
                                  col=None,
                                  missing_col=None,
                                  rtol=1e-5):
        """Print messages to give more details on a mismatch when comparing
        data arrays in fits files

        Arguments
        ---------
        orig_file: str
        Control file

        new_file: str
        New file

        orig_data: fits.fitsrec.FITS_rec
        Control data

        new_data: fits.fitsrec.FITS_rec
        New data

        hdu_name: str
        Name of the ofending HDU

        col: str or None - Default: None
        Name of the offending column. None if there are differences
        in the data array in ImageHDUs

        missing_col: "new", "orig" or None - Default: None
        HDU where the key is missing. None if it is present in both

        rtol: float - Default: 1e-5
        Relative tolerance parameter (see documentation for
        numpy.islcose or np.allclose)
        """
        report_mismatch(orig_file, new_file)

        if col is None:
            if orig_data is None:
                print("Data found in new HDU but not in orig HDU")
            else:
                print(f"Different values found for HDU {hdu_name}")
                print("original new isclose original-new\n")
                for new, orig in zip(orig_data, new_data):
                    print(f"{orig} {new} "
                          f"{np.isclose(orig, new, equal_nan=True)} "
                          f"{orig-new}")

        else:
            if missing_col is None:
                print(f"Different values found for column {col} in "
                      f"HDU {hdu_name}")
                print("original new isclose original-new\n")
                for new, orig in zip(new_data[col], orig_data[col]):
                    print(f"{orig} {new} "
                          f"{np.isclose(orig, new, equal_nan=True, rtol=rtol)} "
                          f"{orig-new}")
            else:
                print(
                    f"Column {col} in HDU {hdu_name} missing in {missing_col} file"
                )

        self.fail()

    def report_fits_mismatch_header(self,
                                    orig_file,
                                    new_file,
                                    orig_header,
                                    new_header,
                                    key,
                                    missing_key=None):
        """Print messages to give more details on a mismatch when comparing
        headers in fits files

        Arguments
        ---------
        orig_file: str
        Control file

        new_file: str
        New file

        orig_obj: fits.header.Header
        Control header.

        new_obj: fits.header.Header
        New header

        key: str
        Name of the offending key

        missing_key: "new", "orig" or None - Default: None
        HDU where the key is missing. None if it is present in both
        """
        report_mismatch(orig_file, new_file)

        if missing_key is None:
            if "EXTNAME" in orig_header:
                print(f"\n For header {orig_header['EXTNAME']}")
            else:
                print("\n For nameless header (possibly a PrimaryHDU)")
            print(f"Different values found for key {key}: "
                  f"orig: {orig_header[key]}, new: {new_header[key]}")

        else:
            print(f"key {key} missing in {missing_key} header")

        self.fail()

    def report_fits_mismatch_hdul(self, orig_file, new_file, orig_hdul,
                                  new_hdul):
        """Print messages to give more details on a mismatch when comparing
        HDU lists in fits files

        Arguments
        ---------
        orig_file: str
        Control file

        new_file: str
        New file

        orig_hdul: fits.hdu.hdulist.HDUList
        Control HDU list

        new_hdul: fits.hdu.hdulist.HDUList
        New HDU list
        """
        report_mismatch(orig_file, new_file)

        print("Different number of extensions found")
        print("orig_hdul.info():")
        orig_hdul.info()
        print("new_hdul.info():")
        new_hdul.info()

        self.fail()


def report_mismatch(orig_file, new_file):
    """Print messages to give more details on a mismatch when comparing
    files

    Arguments
    ---------
    orig_file: str
    Control file

    new_file: str
    New file
    """
    print(f"\nOriginal file: {orig_file}")
    print(f"New file: {new_file}")


if __name__ == '__main__':
    pass
