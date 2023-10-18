""" This module defines the class MeanStacker to compute the stack
using the mean of the stacked values"""
import numpy as np

from stacking.stacker import Stacker
from stacking.stacker import (  # pylint: disable=unused-import
    defaults, accepted_options, required_options)

ASSOCIATED_WRITER = "StandardWriter"


class MeanStacker(Stacker):
    """Class to compute the satck using the mean of the different spectra

    Methods
    -------
    (see Stacker in stacking/stacker.py)
    stack

    Attributes
    ----------
    (see Stacker in stacking/stacker.py)
    """

    def stack(self, spectra):
        """ Stack spectra

        Arguments
        ---------
        spectra: list of Spectrum
        The spectra to stack
        """
        # TODO: parallelize this to also save memory
        weights = np.stack([
            spectrum.ivar_common_grid /
            (1 + 0.05**2 * spectrum.ivar_common_grid) for spectrum in spectra
        ])
        self.stacked_flux = np.nansum(
            np.stack([spectrum.normalized_flux for spectrum in spectra]) *
            weights,
            axis=0)
        self.stacked_weight = np.nansum(weights, axis=0)

        # normalize
        good_pixels = np.where(self.stacked_weight != 0.0)
        self.stacked_flux[good_pixels] /= self.stacked_weight[good_pixels]
