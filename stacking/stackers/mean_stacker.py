""" This module defines the class MeanStacker to compute the stack
using the mean of the stacked values"""
import logging
import numpy as np

from stacking.spectrum import Spectrum
from stacking.stacker import Stacker

ASSOCIATED_WRITER = "StandardWriter"


class MeanStacker(Stacker):
    """Class to compute the satck using the mean of the different spectra

    Methods
    -------
    (see Stacker in stacking/stacker.py)
    __init__
    stack

    Attributes
    ----------
    (see Stacker in stacking/stacker.py)

    logger: logging.Logger
    Logger object

    stacked_flux: array of float
    The stacked flux

    stacked_weight: array of float
    The sum of weights associated with each flux

    """

    def stack(self, spectra):
        """ Stack spectra

        Arguments
        ---------
        spectra: list of Spectrum
        The spectra to stack

        Raise
        -----
        ReaderError if function was not overloaded by child class
        """
        # TODO: parallelize this to also save memory
        self.stacked_flux = np.nansum(np.stack([
            spectrum.normalized_flux * spectrum.ivar_common_grid
            for spectrum in spectra
        ], axis=0), axis=0)
        self.stacked_weight = np.nansum(np.stack([
            spectrum.ivar_common_grid
            for spectrum in spectra
        ], axis=0), axis=0)

        # normalize
        good_pixels = np.where(self.stacked_weight != 0.0)
        self.stacked_flux[good_pixels] /= self.stacked_weight[good_pixels]
