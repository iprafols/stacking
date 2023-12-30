""" This module defines the class MeanStacker to compute the stack
using the mean of the stacked values"""

from stacking.stackers.merge_median_stacker import MergeMedianStacker
from stacking.stackers.merge_median_stacker import defaults as defaults_merge_median_stacker
from stacking.stackers.merge_median_stacker import (
    accepted_options as accepted_options_merge_median_stacker)
from stacking.stackers.merge_median_stacker import (
    required_options as required_options_merge_median_stacker)
from stacking.stackers.merge_split_stacker import (MergeSplitStacker, defaults,
                                             accepted_options, required_options)
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)

accepted_options = update_accepted_options(
    accepted_options, accepted_options_merge_median_stacker)
defaults = update_default_options(defaults, defaults_merge_median_stacker)
required_options = update_required_options(
    required_options, required_options_merge_median_stacker)

ASSOCIATED_WRITER = "SplitWriter"


class MergeSplitMedianStacker(MergeSplitStacker, MergeMedianStacker):
    """Class to compute mulitple stacks splitting on one
    or more properties of the spectra. Uses class MergeMedianStacker

    Methods
    -------
    (see MergeSplitStacker in stacking/stackers/merge_split_stacker.py)
    (see MergeMeanStacker in stacking/stackers/merge_median_stacker.py)

    Attributes
    ----------
    (see MergeSplitStacker in stacking/stackers/merge_split_stacker.py)
    (see MergeMeanStacker in stacking/stackers/merge_median_stacker.py)
    """
