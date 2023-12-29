""" This module defines the class MergeMeanStacker to compute the stack
using the mean of the different partial runs"""
import numpy as np

from stacking.errors import StackerError
from stacking.stackers.merge_stacker import MergeStacker
from stacking.stackers.merge_stacker import (  # pylint: disable=unused-import
    accepted_options, required_options, defaults)

ASSOCIATED_WRITER = "StandardWriter"


class MergeMeanStacker(MergeStacker):
    """Class to compute the satck using the mean of different partial runs

    Methods
    -------
    (see MergeStacker in stacking/stacker.py)
    stack

    Attributes
    ----------
    (see MergeStacker in stacking/stacker.py)
    """

    def stack(self, spectra):
        """ Stack spectra

        Arguments
        ---------
        spectra: list of Spectrum
        The spectra to stack
        """
        if spectra is not None:
            raise StackerError(
                "MergeMeanStacker expects the argument 'spectra' "
                "to be 'None'. This means you probably called this class from "
                "'run_stacking.py' and it should be called only with "
                "'merge_stack_partial_runs.py'. Please double check your "
                "configuration or contact stacking developers if the problem "
                "persists")

        # combine the stacks
        self.stacked_flux = np.nansum(np.stack(
            [flux * weight for (flux, weight) in self.stacks]),
                                      axis=0)
        self.stacked_weight = np.nansum(np.stack(
            [weight for (_, weight) in self.stacks]),
                                        axis=0)

        # normalize
        good_pixels = np.where(self.stacked_weight != 0.0)
        self.stacked_flux[good_pixels] /= self.stacked_weight[good_pixels]
