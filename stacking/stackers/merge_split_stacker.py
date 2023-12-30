""" This module defines the class MeanStacker to compute the stack
using the mean of the stacked values"""

from stacking.stackers.merge_stacker import MergeStacker
from stacking.stackers.merge_stacker import (  # pylint: disable=unused-import
    defaults, accepted_options, required_options)
from stacking.stackers.merge_stacker_utils import load_splits_info

ASSOCIATED_WRITER = "SplitWriter"


class MergeSplitStacker(MergeStacker):
    """Abstract class to compute mulitple stacks splitting on one
    or more properties of the spectra using different partial runs

    Methods
    -------
    (see MergeStacker in stacking/stackers/merge_stacker.py)
    __init__

    Attributes
    ----------
    (see MergeStacker in stacking/stackers/merge_stacker.py)

    groups_info: pd.DataFrame
    DataFrame containing the group information

    num_groups: int
    Number of groups the data is split on

    split_catalogue: pd.DataFrame
    The catalogue to be split
    """

    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class
        """
        super().__init__(config)

        self.groups_info, self.num_groups, self.split_catalogue = load_splits_info(
            self.stack_list)
