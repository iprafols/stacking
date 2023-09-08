""" This module define the class MultipleRegionsNornalization that normalizes
the spectra using multiple regions """
from datetime import datetime
import logging
import multiprocessing

from astropy.io import fits
from numba import njit, prange
import numpy as np
import pandas as pd

from stacking._version import __version__
from stacking.errors import NormalizerError
from stacking.normalizer import (Normalizer, defaults, accepted_options,
                                 required_options)
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)

accepted_options = update_accepted_options(accepted_options, [
    "intervals",
    "log directory",
    "main interval",
    "num processors",
    "save format",
])
required_options = update_required_options(required_options, ["log directory"])
defaults = update_default_options(
    defaults, {
        "intervals": "1300 - 1500, 2000 - 2600, 4400 - 4800",
        "main interval": 1,
        "save format": "fits.gz",
    })

ACCEPTED_SAVE_FORMATS = ["csv", "fits", "fits.gz", "txt"]


class MultipleRegionsNormalization(Normalizer):
    """This class is set to circunvent the normalization procedure

    Methods
    -------
    __init__
    __parse_config
    compute_normalisation_factors
    normalize_spectrum

    Attributes
    ----------
    correction_factors: array of float
    Correction factors that relate the differnt intervals

    interals:  array of (float, float)
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
        NormalizerError if the reading mode is not supported
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

        self.save_format = config.get("save format")
        if self.save_format is None:
            raise NormalizerError("Missing argument 'save format' required by "
                                  "MultipleRegionsNormalization")
        if self.save_format not in ACCEPTED_SAVE_FORMATS:
            raise NormalizerError(
                "Invalid save format. Accepted options are '" +
                " ".join(ACCEPTED_SAVE_FORMATS) +
                f"' Found: {self.save_format}")

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
                        "the main intervals were found.")

    def compute_norm_factors(self, spectra):
        """ Compute the normalization factors

        Arguments
        ---------
        spectra: list of Spectrum
        The list of spectra
        """
        # first compute individual normalisation factors
        arguments = [(spectrum.flux, spectrum.ivar, spectrum.wavelength,
                      self.num_intervals, self.intervals)
                     for spectrum in spectra]

        if self.num_processors > 1:
            context = multiprocessing.get_context('fork')
            with context.Pool(processes=self.num_processors) as pool:
                imap_it = pool.imap(compute_norm_factors, arguments)
        else:
            imap_it = [
                compute_norm_factors(*argument) for argument in arguments
            ]

        # unpack them together in a dataframe
        self.norm_factors = pd.DataFrame(
            imap_it,
            columns=[
                f"{col_type} {index}" for index in range(self.num_intervals)
                for col_type in ["norm factor", "norm S/N", "num pixels"]
            ])
        self.norm_factors["specid"] = [spectrum.specid for spectrum in spectra]

        # create relations between the main normalisation factor and the secondary
        self.compute_correction_factors()

        # select final normalisation factor
        self.norm_factors[["norm factor", "norm S/N",
                           "chosen interval"]] = self.norm_factors.apply(
                               select_final_normalisation_factor,
                               axis=1,
                               args=(self.correction_factors,),
                               result_type='expand',
                           )

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
        norm_factor = self.norm_factors[self.norm_factors["specid"] == spectrum.
                                        specid]["norm factor"].values[0]

        if norm_factor > 0.0:
            spectrum.set_normalized_flux(spectrum.flux_common_grid /
                                         norm_factor)
        else:
            spectrum.set_normalized_flux(
                np.zeros_like(spectrum.flux_common_grid) + np.nan)
        return spectrum

    def save_norm_factors(self):
        """ Save the normalisation factors for future reference """
        filename = f"{self.log_directory}normalization_factors.{self.save_format}"

        # save as ascii file
        if self.save_format in ["csv", "txt"]:
            # norm factors
            self.norm_factors.to_csv(
                filename,
                index=False,
                float_format='%.6f',
                encoding="utf-8",
            )

            # intervals used
            filename = f"{self.log_directory}normalization_intervals.{self.save_format}"
            with open(filename, "w", encoding="utf-8") as results:
                results.write("start,end\n")
                for index in range(self.intervals.shape[0]):
                    results.write(
                        f"{self.intervals[index, 0]:.6f},{self.intervals[index, 1]:.6f}\n"
                    )

            # correction_factors
            filename = f"{self.log_directory}correction_factors.{self.save_format}"
            with open(filename, "w", encoding="utf-8") as results:
                results.write("interval,correction factor\n")
                for index, correction_factor in enumerate(
                        self.correction_factors):
                    results.write(f"{index},{correction_factor:.6f}\n")

        # save as fits file
        elif self.save_format in ["fits", "fits.gz"]:
            # primary HDU
            primary_hdu = fits.PrimaryHDU()
            now = datetime.now()
            primary_hdu.header["COMMENT"] = (
                f"Normalisation factors computed using class {__name__}"
                f" of code stacking")
            primary_hdu.header["VERSION"] = (__version__, "Code version")
            primary_hdu.header["DATETIME"] = (now.strftime("%Y-%m-%dT%H:%M:%S"),
                                              "DateTime file created")

            # norm factors
            cols = [
                fits.Column(name=col,
                            format="E",
                            disp="F7.3",
                            array=self.norm_factors[col].values) if "num pixels"
                not in col else fits.Column(name=col,
                                            format="J",
                                            disp="I4",
                                            array=self.norm_factors[col].values)
                for col in self.norm_factors.columns
            ]
            hdu = fits.BinTableHDU.from_columns(cols, name="NORM_FACTORS")

            # intervals used
            cols = [
                fits.Column(name="START",
                            format="E",
                            disp="F7.3",
                            array=self.intervals[:, 0]),
                fits.Column(name="END",
                            format="E",
                            disp="F7.3",
                            array=self.intervals[:, 1]),
            ]
            hdu2 = fits.BinTableHDU.from_columns(cols, name="NORM_INTERVALS")

            # correction factors
            cols = [
                fits.Column(name="CORRECTION_FACTOR",
                            format="E",
                            disp="F7.3",
                            array=self.correction_factors),
                fits.Column(name="INTERVAL",
                            format="J",
                            disp="I4",
                            array=np.arange(self.correction_factors.size,
                                            dtype=int)),
            ]
            hdu3 = fits.BinTableHDU.from_columns(cols,
                                                 name="CORRECTION_FACTORS")

            hdul = fits.HDUList([primary_hdu, hdu, hdu2, hdu3])
            hdul.writeto(filename, overwrite=True, checksum=True)

        # this should never enter unless new saving formats are not properly added
        else:  # pragma: no cover
            raise NormalizerError(
                f"Don't know what to do with save format {self.save_format}. "
                "This is one of the supported saving formats, maybe it "
                "was not properly coded. If you did the change yourself, check "
                "that you added the behaviour of the new mode to method `save_norm_factors`. "
                "Otherwise contact 'stacking' developpers.")


@njit
def compute_norm_factors(flux, ivar, wavelength, num_intervals, intervals):
    """ Compute the normalisation factors for the specified intervals.

    The normalisation factor, n, is computed doing the average of the fluxes, f_i,
    inside the normalisation interval:
        n = sum_i f_i / N
    where N is the number of pixels used.

    The normalisation signal-to-noise, s, is computed dividing the normalisation
    factor, n, by sum in quadrature of the errors, e_i:
        s = n / sqrt(sum_i e_i^2 / N)

    Pixels where ivar is set to 0 are ignored in these calculations.

    Arguments
    ---------
    flux: array of float
    The flux array

    ivar: array of float
    The inverse variance associated with the flux

    wavelength: array of float
    The wavelength array

    num_intervals: int
    The number of intervals

    intervals: array of (float, float)
    Array containing the selected intervals. Each item must contain
    two floats signaling the starting and ending wavelength of the interval.
    Naturally, the starting wavelength must be smaller than the ending wavelength.

    Return
    ------
    results: array of float
    Array of size `3*num_intervals`. Indexs 3X contains the normalization
    factor of the Xth region, indexs 3X + 1 contains the normalization
    signal to noise of the Xth region, and indexs 3X + 2 contains the number of
    pixels used to compute the normalization of the Xth region.
    """
    # normalization factors occupy the indexs 3X
    # normalization signal-to-noise occupy indexs 3X + 1
    # number of pixels occupy indexs 3X + 2
    results = np.zeros(3 * num_intervals, dtype=np.float64)

    # Disabling pylint warning, see https://github.com/PyCQA/pylint/issues/2910
    for index in prange(num_intervals):  # pylint: disable=not-an-iterable
        pos = np.where((wavelength >= intervals[index][0]) &
                       (wavelength <= intervals[index][1]) & (ivar != 0.0))
        # number of pixels
        num_pixels = float(pos[0].size)
        results[3 * index + 2] = num_pixels

        if num_pixels == 0:
            # norm factor
            results[3 * index] = np.nan
            # norm sn
            results[3 * index + 1] = np.nan
        else:
            # norm factor
            norm_factor = np.sum(flux[pos]) / num_pixels
            results[3 * index] = norm_factor

            mean_noise = np.sqrt(np.sum(1.0 / ivar[pos]) /
                                 num_pixels)  #[index])
            # norm sn
            results[3 * index + 1] = norm_factor / mean_noise

    return results


def select_final_normalisation_factor(row, correction_factors):
    """ Select the final normalisation factor

    This function should be called using pd.apply with axis=1

    Arguments
    ---------
    row: array
    A dataframe row with the normalisation factors. Should contain the columns
    'norm factor X', 'norm S/N X', 'num pixels X', where X = 0, 1, ... N and
    N is the size of intervals_corretion_factors

    correction_factors: array of float
    Correction factors to correct the chosen normalisation factors
    """
    # select best interval
    cols = [f"num pixels {index}" for index in range(correction_factors.size)]
    selected_interval = row[cols].values.argmax()

    norm_factor = row[f"norm factor {selected_interval}"] * correction_factors[
        selected_interval]
    norm_sn = row[f"norm S/N {selected_interval}"]

    return norm_factor, norm_sn, selected_interval
