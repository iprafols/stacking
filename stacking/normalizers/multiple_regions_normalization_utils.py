""" This module define utility functions for class MultipleRegionsNornalization"""
from datetime import datetime

from astropy.io import fits
from numba import njit, prange
import numpy as np

from stacking._version import __version__


@njit
def compute_norm_factors(flux,
                         ivar,
                         wavelength,
                         num_intervals,
                         intervals,
                         sigma_i2=0.0025):
    """ Compute the normalisation factors for the specified intervals.

    The normalisation factor, n, is computed doing the average of the fluxes, f_i,
    inside the normalisation interval:
        n = sum_j f_j w_j / sum_j w_j
    where w_j is the weight of pixel j computed as  w = 1 / (sigma_j^2 + sigma_I^2),
    sigma_j is the variance of pixel j, and sigma_I is an added variance to prevent
    the highest signal-to-noise pixels to dominate the sum.

    The normalisation signal-to-noise, s, is computed dividing the normalisation
    factor, n, by sum in quadrature of the errors, e_i:
        s = n / sqrt(sum_j e_j^2 w_j/ sum_j w_j)

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

    sigma_i2: float - Default: 0.0025
    A correction to the weights so that pixels with very small variance do not
    dominate. Weights are computed as w = 1 / (sigma^2 + sigma_i^2)

    Return
    ------
    results: array of float
    Array of size `4*num_intervals`. Indexs 3X contain the normalization
    factor of the Xth region, indexs 3X + 1 contain the normalization
    signal to noise of the Xth region, indexs 3X + 2 contain the number of
    pixels used to compute the normalization of the Xth region, and indexs 3X + 3
    contain the total weight used in the computation of the normalization factor
    """
    # normalization factors occupy the indexs 3X
    # normalization signal-to-noise occupy indexs 3X + 1
    # number of pixels occupy indexs 3X + 2
    results = np.zeros(4 * num_intervals, dtype=np.float64)

    # Disabling pylint warning, see https://github.com/PyCQA/pylint/issues/2910
    for index in prange(num_intervals):  # pylint: disable=not-an-iterable
        pos = np.where((wavelength >= intervals[index][0]) &
                       (wavelength <= intervals[index][1]) & (ivar != 0.0))
        # number of pixels
        num_pixels = float(pos[0].size)
        results[4 * index + 2] = num_pixels

        if num_pixels == 0:
            # norm factor
            results[4 * index] = np.nan
            # norm sn
            results[4 * index + 1] = np.nan
            # weight
            results[4 * index + 3] = np.nan
        else:
            # weight
            weight = ivar[pos]
            if not np.isclose(sigma_i2, 0.0):
                weight /= (1 + sigma_i2 * ivar[pos])
            total_weight = np.sum(weight)

            norm_factor = np.sum(flux[pos] * weight) / total_weight

            mean_noise = np.sqrt(np.sum(weight / ivar[pos]) / total_weight)

            # keep the results
            if norm_factor > 0:
                # norm factor
                results[4 * index] = norm_factor
                # norm sn
                results[4 * index + 1] = norm_factor / mean_noise
                # weight
                results[4 * index + 3] = total_weight
            else:
                # norm factor
                results[4 * index] = np.nan
                # norm sn
                results[4 * index + 1] = np.nan
                # weight
                results[4 * index + 3] = np.nan

    return results


def save_correction_factors_ascii(filename, correction_factors):
    """ Save the correction factors in an ascii file

    Arguments
    ---------
    filename: str
    Name of the file

    correction_factors: array of float
    Correction factors that relate the different intervals
    """
    with open(filename, "w", encoding="utf-8") as results:
        results.write("# interval correction_factor\n")
        for index, correction_factor in enumerate(correction_factors):
            results.write(f"{index} {correction_factor}\n")


def save_norm_factors_ascii(filename, norm_factors):
    """ Save the normalisation factors in an ascii file

    Arguments
    ---------
    filename: str
    Name of the file

    norm_factors: pd.DataFrame
    Pandas DataFrame containing the normalization factors
    """
    norm_factors.to_csv(
        filename,
        index=False,
        float_format='%.6f',
        encoding="utf-8",
        sep=" ",
        na_rep="nan",
    )


def save_norm_factors_fits(filename, norm_factors, intervals,
                           correction_factors):
    """ Save the normalisation factors, the normalization intervals and the
    correction factors in a fits file

    Arguments
    ---------
    filename: str
    Name of the file

    norm_factors: pd.DataFrame
    Pandas DataFrame containing the normalization factors

    intervals:  array of (float, float)
    Array containing the selected intervals. Each item must contain
    two floats signaling the starting and ending wavelength of the interval.
    Naturally, the starting wavelength must be smaller than the ending wavelength.

    correction_factors: array of float
    Correction factors that relate the different intervals
    """
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
        fits.Column(
            name=col, format="J", disp="I4", array=norm_factors[col].values)
        if "num pixels" in col or col == "specid" else fits.Column(
            name=col, format="E", disp="F7.3", array=norm_factors[col].values)
        for col in norm_factors.columns
    ]
    hdu = fits.BinTableHDU.from_columns(cols, name="NORM_FACTORS")
    # TODO: add description of columns

    # intervals used
    cols = [
        fits.Column(name="START",
                    format="E",
                    disp="F7.3",
                    array=intervals[:, 0]),
        fits.Column(name="END", format="E", disp="F7.3", array=intervals[:, 1]),
    ]
    hdu2 = fits.BinTableHDU.from_columns(cols, name="NORM_INTERVALS")
    # TODO: add description of columns

    # correction factors
    cols = [
        fits.Column(name="CORRECTION_FACTOR",
                    format="E",
                    disp="F7.3",
                    array=correction_factors),
        fits.Column(name="INTERVAL",
                    format="J",
                    disp="I4",
                    array=np.arange(correction_factors.size, dtype=int)),
    ]
    hdu3 = fits.BinTableHDU.from_columns(cols, name="CORRECTION_FACTORS")
    # TODO: add description of columns

    hdul = fits.HDUList([primary_hdu, hdu, hdu2, hdu3])
    hdul.writeto(filename, overwrite=True, checksum=True)


def save_norm_intervals_ascii(filename, intervals):
    """ Save the normalisation intervals in an ascii file

    Arguments
    ---------
    filename: str
    Name of the file

    intervals:  array of (float, float)
    Array containing the selected intervals. Each item must contain
    two floats signaling the starting and ending wavelength of the interval.
    Naturally, the starting wavelength must be smaller than the ending wavelength.
    """
    with open(filename, "w", encoding="utf-8") as results:
        results.write("# start end\n")
        for index in range(intervals.shape[0]):
            results.write(f"{intervals[index, 0]} {intervals[index, 1]}\n")


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
    cols = [f"total weight {index}" for index in range(correction_factors.size)]
    try:
        selected_interval = np.nanargmax(row[cols].values)
        norm_factor = row[
            f"norm factor {selected_interval}"] * correction_factors[
                selected_interval]
        norm_sn = row[f"norm S/N {selected_interval}"]

    except ValueError:
        norm_factor = np.nan
        norm_sn = np.nan
        selected_interval = -1

    return norm_factor, norm_sn, selected_interval
