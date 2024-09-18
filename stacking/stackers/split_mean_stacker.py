""" This module defines the class SplitMeanStacker to compute multiple
stacks splitting on one or more properties of the spectra using the mean of the
stacked values"""

from stacking.stackers.mean_stacker import MeanStacker
from stacking.stackers.mean_stacker import defaults as defaults_mean_stacker
from stacking.stackers.mean_stacker import accepted_options as accepted_options_mean_stacker
from stacking.stackers.mean_stacker import required_options as required_options_mean_stacker
from stacking.stackers.split_stacker import (SplitStacker, defaults,
                                             accepted_options, required_options)
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)

accepted_options = update_accepted_options(accepted_options,
                                           accepted_options_mean_stacker)
defaults = update_default_options(defaults, defaults_mean_stacker)
required_options = update_required_options(required_options,
                                           required_options_mean_stacker)

ASSOCIATED_WRITER = "SplitWriter"


class SplitMeanStacker(SplitStacker):
    """Class to compute multiple stacks splitting on one
    or more properties of the spectra. Uses class MeanStacker

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

    def __init__(self, config, groups_info=None, split_catalogue=None):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        groups_info: pd.DataFrame or None - default: None
        If not None, then the groups information will be computed upon initialization. 
        Otherwise, this must be pandas DataFrame with the previously computed information

        split_catalogue: pd.DataFrame or None - default: None
        If not None, then the catalogue will be read from split_catalogue_name
        Otherwise, this must be pandas DataFrame with the previously read catalogue
        """
        super().__init__(config,
                         groups_info=groups_info,
                         split_catalogue=split_catalogue)

        self.stackers = [MeanStacker(config) for _ in range(self.num_groups)]
