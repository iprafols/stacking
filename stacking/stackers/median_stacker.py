""" This module defines the class MedianStacker to compute the stack
using the median of the stacked values"""
import numpy as np

from stacking.stacker import (Stacker, defaults, accepted_options,
                             required_options)

ASSOCIATED_WRITER = "StandardWriter"


class MedianStacker(Stacker):
    """Class to compute the satck using the median of the different spectra

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
        self.stacked_flux = np.nanmedian(np.stack([
            spectrum.normalized_flux / (spectrum.ivar_common_grid != 0)
            for spectrum in spectra
        ]),
                                         axis=0)

        self.stacked_weight = np.nansum(np.stack(
            [spectrum.ivar_common_grid for spectrum in spectra]),
                                        axis=0)
