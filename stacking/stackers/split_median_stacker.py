""" This module defines the class SplitMedianStacker to compute multiple
stacks splitting on one or more properties of the spectra using the mean of the
stacked values"""

from stacking.stackers.median_stacker import MedianStacker
from stacking.stackers.median_stacker import defaults as defaults_median_stacker
from stacking.stackers.median_stacker import accepted_options as accepted_options_median_stacker
from stacking.stackers.median_stacker import required_options as required_options_median_stacker
from stacking.stackers.split_stacker import (SplitStacker, defaults,
                                             accepted_options, required_options)
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)

accepted_options = update_accepted_options(accepted_options,
                                           accepted_options_median_stacker)
defaults = update_default_options(defaults, defaults_median_stacker)
required_options = update_required_options(required_options,
                                           required_options_median_stacker)

ASSOCIATED_WRITER = "SplitWriter"


class SplitMedianStacker(SplitStacker):
    """Class to compute multiple stacks splitting on one
    or more properties of the spectra. Uses class MedianStacker

    Methods
    -------
    (see SplitStacker in stacking/stackers/split_stacker.py)
    __init__

    Attributes
    ----------
    (see SplitStacker in stacking/stackers/split_stacker.py)

    stackers: list of Stacker
    Stacker instances that will contain the stacked spectra for each of the groups
    Must be initialized by the child class
    """

    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class
        """
        super().__init__(config)

        self.stackers = [MedianStacker(config) for _ in range(self.num_groups)]
