""" This module defines the class MergeMeanStacker to compute the stack
using the mean of the different partial runs"""
import numpy as np

from stacking.errors import StackerError
from stacking.stackers.median_stacker import MedianStacker
from stacking.stackers.median_stacker import (accepted_options,
                                              required_options, defaults)
from stacking.stackers.merge_stacker import MergeStacker
from stacking.stackers.merge_stacker import (accepted_options as
                                             accepted_options_merge_stacker,
                                             required_options as
                                             required_options_merge_stacker,
                                             defaults as defaults_merge_stacker)
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)

accepted_options = update_accepted_options(accepted_options,
                                           accepted_options_merge_stacker)
defaults = update_default_options(defaults, defaults_merge_stacker)
required_options = update_required_options(required_options,
                                           required_options_merge_stacker)

ASSOCIATED_WRITER = "StandardWriter"


class MergeMedianStacker(MergeStacker, MedianStacker):
    """Class to compute the satck using the median of different partial runs

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
                "MergeMedianStacker expects the argument 'spectra' "
                "to be 'None'. This means you probably called this class from "
                "'run_stacking.py' and it should be called only with "
                "'merge_stack_partial_runs.py'. Please double check your "
                "configuration or contact stacking developers if the problem "
                "persists")

        if self.weighted:  # pylint: disable=no-else-raise
            # TODO: compute weighted median
            raise StackerError("Not implemented")
        else:
            self.stacked_flux = np.nanmedian(np.stack(
                [flux for (flux, _) in self.stacks]),
                                             axis=0)
            self.stacked_weight = np.nansum(np.stack(
                [weight for (_, weight) in self.stacks]),
                                            axis=0)
