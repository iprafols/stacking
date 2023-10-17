""" This module define the class MultipleRegionsNornalization that normalizes
the spectra using multiple regions """
import logging
import multiprocessing
import os

from astropy.table import Table
import numpy as np
import pandas as pd

from stacking._version import __version__
from stacking.errors import NormalizerError
from stacking.normalizer import (Normalizer, defaults, accepted_options,
                                 required_options)
from stacking.spectrum import Spectrum
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)
from stacking.normalizers.multiple_regions_normalization_utils import (
    compute_norm_factors, save_correction_factors_ascii,
    save_norm_factors_ascii, save_norm_factors_fits, save_norm_intervals_ascii,
    select_final_normalisation_factor)

accepted_options = update_accepted_options(accepted_options, [
    "intervals", "load norm factors from", "log directory", "main interval",
    "num processors", "save format", "sigma_I"
])
required_options = update_required_options(required_options, ["log directory"])
defaults = update_default_options(
    defaults, {
        "intervals": "1300 - 1500, 2000 - 2600, 4400 - 4800",
        "main interval": 1,
        "save format": "fits.gz",
        "sigma_I": 0.05,
    })

ACCEPTED_SAVE_FORMATS = ["csv", "fits", "fits.gz", "txt"]


class MultipleRegionsNormalization(Normalizer):
    """This class is set to compute the normalization factors using multiple
    normalization regions

    Methods
    -------
    __init__
    __parse_config
    compute_normalisation_factors
    normalize_spectrum

    Attributes
    ----------
    correction_factors: array of float
    Correction factors that relate the different intervals

    intervals:  array of (float, float)
    Array containing the selected intervals. Each item must contain
    two floats signaling the starting and ending wavelength of the interval.
    Naturally, the starting wavelength must be smaller than the ending wavelength.

    log_directory: str
    Directory where log data is saved. Normalization factors will be saved there

    logger: logging.Logger
    Logger object

    main_interval: int
    Number of main normalizeation interval

    norm_factor: pd.DataFrame
    Pandas DataFrame with the normalization factors

    num_intervals: int
    Number of intervals

    save_format: str
    Saving format, e.g. 'csv', 'txt', 'fits' or 'fits.gz'

    sigma_i: float
    A correction to the weights so that pixels with very small variance do not
    dominate. Weights are computed as w = 1 / (sigma^2 + sigma_i^2)
    """

    def __init__(self, config):
        """ Initialize instance """

        self.logger = logging.getLogger(__name__)

        # load variables from config
        self.intervals = []
        self.log_directory = []
        self.main_interval = None
        self.num_intervals = None
        self.save_format = None
        self.sigma_i = None
        self.__parse_config(config)

        # initialize data frame to store normalization factors
        self.norm_factors = None
        self.correction_factors = np.zeros(self.num_intervals, dtype=float)

    def __parse_config(self, config):
        """Parse the configuration options

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        NormalizerError upon missing required variables
        """
        intervals_str = config.get("intervals")
        if intervals_str is None:
            raise NormalizerError("Missing argument 'intervals' required by "
                                  "MultipleRegionsNormalization")
        try:
            self.intervals = np.array([
                (float(interval.split("-")[0]), float(interval.split("-")[1]))
                for interval in intervals_str.split(",")
            ])
        except (ValueError, IndexError) as error:
            raise NormalizerError(
                "Wrong format for variable 'intervals'. Expected "
                "'start0 - end0, start1 - end1, ..., startN - endN'"
                " where startX and endX are positive numbers. Found: "
                f"{intervals_str}") from error
        for interval in self.intervals:
            if interval[0] > interval[1]:
                raise NormalizerError(
                    f"Invalid interval found: {interval}. Starting wavelength "
                    "should be smaller than ending interval")
        self.num_intervals = len(self.intervals)

        self.load_norm_factors_from = config.get("load norm factors from")

        self.log_directory = config.get("log directory")
        if self.log_directory is None:
            raise NormalizerError(
                "Missing argument 'log directory' required by "
                "MultipleRegionsNormalization")

        self.main_interval = config.getint("main interval")
        if self.main_interval is None:
            raise NormalizerError(
                "Missing argument 'main interval' required by "
                "MultipleRegionsNormalization")
        if self.main_interval < 0:
            raise NormalizerError(
                "Invalid value for 'main interval'. Expected a positive integer. "
                f"Found: {self.main_interval}")
        if self.main_interval > self.num_intervals:
            raise NormalizerError(
                "Invalid value for 'main interval'. Selected interval "
                f"{self.main_interval} as main interval, but I only read "
                f"{len(self.intervals)} intervals (keep in mind the zero-based "
                "indexing in python)")

        self.num_processors = config.getint("num processors")
        if self.num_processors is None:
            raise NormalizerError(
                "Missing argument 'num processors' required by "
                "MultipleRegionsNormalization")
        if self.num_processors == 0:
            self.num_processors = multiprocessing.cpu_count() // 2

        self.save_format = config.get("save format")
        if self.save_format is None:
            raise NormalizerError("Missing argument 'save format' required by "
                                  "MultipleRegionsNormalization")
        if self.save_format not in ACCEPTED_SAVE_FORMATS:
            raise NormalizerError(
                "Invalid save format. Accepted options are '" +
                " ".join(ACCEPTED_SAVE_FORMATS) +
                f"' Found: {self.save_format}")

        self.sigma_i = config.getfloat("sigma_I")
        if self.sigma_i is None:
            raise NormalizerError("Missing argument 'sigma_I' required by "
                                  "MultipleRegionsNormalization")
        if self.sigma_i < 0:
            raise NormalizerError(
                "Argument 'sigma_I' should be positive. Found "
                f"{self.sigma_i}")

    def compute_correction_factors(self):
        """ Compute the correction factor that relate the differnt intervals

        Raise
        -----
        NormalizerError if any of the correction factor cannot be computed
        """
        for index in range(self.num_intervals):
            if index == self.main_interval:
                self.correction_factors[index] = 1
            else:
                aux = self.norm_factors[
                    ~self.norm_factors[f"norm factor {index}"].isna() & ~self.
                    norm_factors[f"norm factor {self.main_interval}"].isna()]
                if aux.shape[0] > 0:
                    self.correction_factors[index] = (
                        aux[f"norm factor {self.main_interval}"].mean() /
                        aux[f"norm factor {index}"].mean())
                else:
                    raise NormalizerError(
                        "Error computing the correction for normalisation "
                        f"factor interval {index}. No common measurements with "
                        "the main interval were found.")

    def compute_norm_factors(self, spectra):
        """ Compute the normalization factors

        Arguments
        ---------
        spectra: list of Spectrum
        The list of spectra
        """
        # load from file
        if self.load_norm_factors_from is not None:
            self.logger.progress("Found a folder to read them instead")
            self.norm_factors, self.correction_factors = self.load_norm_factors(
                self.load_norm_factors_from)

        # compute normalization factors
        else:
            # first compute individual normalisation factors
            arguments = [(spectrum.flux_common_grid, spectrum.ivar_common_grid,
                          Spectrum.common_wavelength_grid, self.num_intervals,
                          self.intervals, self.sigma_i) for spectrum in spectra]

            if self.num_processors > 1:
                context = multiprocessing.get_context('fork')
                with context.Pool(processes=self.num_processors) as pool:
                    norm_factors = pool.starmap(compute_norm_factors, arguments)
            else:
                norm_factors = [
                    compute_norm_factors(*argument) for argument in arguments
                ]

            # unpack them together in a dataframe
            self.norm_factors = pd.DataFrame(
                norm_factors,
                columns=[
                    f"{col_type} {index}" for index in range(self.num_intervals)
                    for col_type in
                    ["norm factor", "norm S/N", "num pixels", "total weight"]
                ])
            self.norm_factors["specid"] = [
                spectrum.specid for spectrum in spectra
            ]

            # create relations between the main normalisation factor and the secondary
            self.compute_correction_factors()

            # select final normalisation factor
            self.select_final_normalisation_factor()

    def load_norm_factors(self, folder):
        """Load normalilzation factors from file

        Arguments
        ---------
        folder: str
        Folder where the normalization files are saved.
        Must contain a file named normalization_factors with a valid extension
        (see ACCEPTED_SAVE_FORMATS)

        Return
        ------
        norm_factors: pd.DataFrame
        A pandas DataFrame with the read normalization_factors

        correction_factors: array of float
        The correction factors that relate the differnt intervals.
        """
        file_format = None
        filename = None
        for item in ACCEPTED_SAVE_FORMATS:
            filename = f"{os.path.expandvars(folder)}normalization_factors.{item}"
            if os.path.exists(filename):
                file_format = item
                break

        if file_format is None:
            raise NormalizerError(
                "Unable to find file normalization_factors.EXT in the specified "
                "folder, where EXT is one of '" +
                " ".join(ACCEPTED_SAVE_FORMATS) +
                f"'. Specified folder: {folder}")
        if file_format in ["csv", "txt"]:
            norm_factors = pd.read_csv(filename, delim_whitespace=True)

            correction_factors_filename = (
                f"{os.path.expandvars(folder)}correction_factors.{file_format}")
            if os.path.exists(correction_factors_filename):
                correction_factors = pd.read_csv(
                    correction_factors_filename,
                    delim_whitespace=True)["correction_factor"].values
            else:
                raise NormalizerError(
                    f"Unable to find file correction_factors.{file_format}. "
                    f"Specified folder: {os.path.expandvars(folder)}")
        elif file_format in ["fits", "fits.gz"]:
            norm_factors = Table.read(filename,
                                      format='fits',
                                      hdu="NORM_FACTORS").to_pandas()

            correction_factors = Table.read(filename,
                                            format='fits',
                                            hdu="CORRECTION_FACTORS").to_pandas(
                                            )["CORRECTION_FACTOR"].values
        # this should never enter unless new reading formats are not properly added
        else:  # pragma: no cover
            raise NormalizerError(
                f"Don't know what to do with file format {file_format}. "
                "This is one of the supported formats, maybe it "
                "was not properly coded. If you did the change yourself, check "
                "that you added the behaviour of the new mode to method `save_norm_factors`. "
                "Otherwise contact 'stacking' developpers.")

        return norm_factors, correction_factors

    def normalize_spectrum(self, spectrum):
        """ Set the flux as normalized flux

        Arguments
        ---------
        spectrum: Spectrum
        A spectrum to normalize

        Return
        ------
        spectrum: Spectrum
        The normalized spectrum
        """
        try:
            norm_factor = self.norm_factors[
                self.norm_factors["specid"] ==
                spectrum.specid]["norm factor"].values[0]
        except IndexError as error:
            raise NormalizerError(
                f"Failed to normalize spectrum with specid={spectrum.specid}. "
                "Could not find the specid in the norm_factor tables. If you "
                "loaded the table, make sure the table is correct. Otherwise "
                "contact stacking developers") from error

        if spectrum.specid in [140014224, 183482272, 48727840.0]:
            print(f"specid={spectrum.specid}; norm_factor={norm_factor}")
            print(self.norm_factors[self.norm_factors["specid"] ==
                                    spectrum.specid][["specid", "norm factor"]])

        if norm_factor > 0.0:
            spectrum.set_normalized_flux(spectrum.flux_common_grid /
                                         norm_factor)
        else:
            spectrum.set_normalized_flux(
                np.zeros_like(spectrum.flux_common_grid) + np.nan)
        return spectrum

    def save_norm_factors(self):
        """ Save the normalisation factors for future reference """
        # norm factors loaded, do not save
        if self.load_norm_factors_from is not None:
            self.logger.progress(
                "Normalization factors were loaded from file. Skipping saving "
                "operation")
        else:
            filename = f"{self.log_directory}normalization_factors.{self.save_format}"

            # save as ascii file
            if self.save_format in ["csv", "txt"]:
                save_norm_factors_ascii(filename, self.norm_factors)

                # intervals used
                filename = f"{self.log_directory}normalization_intervals.{self.save_format}"
                save_norm_intervals_ascii(filename, self.intervals)

                # correction_factors
                filename = f"{self.log_directory}correction_factors.{self.save_format}"
                save_correction_factors_ascii(filename, self.correction_factors)

            # save as fits file
            elif self.save_format in ["fits", "fits.gz"]:
                save_norm_factors_fits(filename, self.norm_factors,
                                       self.intervals, self.correction_factors)

            # this should never enter unless new saving formats are not properly added
            else:  # pragma: no cover
                raise NormalizerError(
                    f"Don't know what to do with save format {self.save_format}. "
                    "This is one of the supported saving formats, maybe it "
                    "was not properly coded. If you did the change yourself, check "
                    "that you added the behaviour of the new mode to method `save_norm_factors`. "
                    "Otherwise contact 'stacking' developpers.")

    def select_final_normalisation_factor(self):
        """Select the final normalization factors"""
        self.norm_factors[["norm factor", "norm S/N",
                           "chosen interval"]] = self.norm_factors.apply(
                               select_final_normalisation_factor,
                               axis=1,
                               args=(self.correction_factors,),
                               result_type='expand',
                           )
