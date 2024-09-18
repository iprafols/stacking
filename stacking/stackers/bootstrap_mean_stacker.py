""" This module defines the class BootstrapMeanStacker to compute the stack
(including bootstrap errors) using the mean of the stacked values"""

from stacking.stackers.mean_stacker import MeanStacker
from stacking.stackers.mean_stacker import defaults as defaults_mean_stacker
from stacking.stackers.mean_stacker import accepted_options as accepted_options_mean_stacker
from stacking.stackers.mean_stacker import required_options as required_options_mean_stacker
from stacking.stackers.bootstrap_stacker import (BootstrapStacker, defaults,
                                                 accepted_options,
                                                 required_options)
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)

accepted_options = update_accepted_options(accepted_options,
                                           accepted_options_mean_stacker)
defaults = update_default_options(defaults, defaults_mean_stacker)
required_options = update_required_options(required_options,
                                           required_options_mean_stacker)

ASSOCIATED_WRITER = "BootstrapWriter"


class BootstrapMeanStacker(BootstrapStacker):
    """Class to compute stacks with bootstrap errors. Uses class MeanStacker

    Methods
    -------
    (see BootstrapStacker in stacking/stackers/split_stacker.py)
    __init__

    Attributes
    ----------
    (see BootstrapStacker in stacking/stackers/split_stacker.py)

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

        self.main_stacker = MeanStacker(config)
        self.bootstrap_stackers = [
            MeanStacker(config) for _ in range(self.num_bootstrap)
        ]
