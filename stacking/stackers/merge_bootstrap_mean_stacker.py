""" This module defines the abstract class MergeBootstrapStacker to compute
the stack using different partial runs including bootstrap errors"""
from copy import copy

from stacking.errors import StackerError
from stacking.stackers.merge_mean_stacker import MergeMeanStacker
from stacking.stackers.merge_mean_stacker import (defaults as
                                                  defaults_merge_mean_stacker)
from stacking.stackers.merge_mean_stacker import (
    accepted_options as accepted_options_merge_mean_stacker)
from stacking.stackers.merge_mean_stacker import (
    required_options as required_options_merge_mean_stacker)
from stacking.stackers.bootstrap_stacker import (BootstrapStacker, defaults,
                                                 accepted_options,
                                                 required_options)
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)

accepted_options = update_accepted_options(accepted_options,
                                           accepted_options_merge_mean_stacker)
defaults = update_default_options(defaults, defaults_merge_mean_stacker)
required_options = update_required_options(required_options,
                                           required_options_merge_mean_stacker)

ASSOCIATED_WRITER = "BootstrapWriter"


class MergeBootstrapMeanStacker(BootstrapStacker):
    """Class to compute the satck using different partial runs
    including bootstrap errors

    Methods
    -------
    (see BootstrapStacker in stacking/stackers/split_stacker.py)
    __init__

    Attributes
    ----------
    (see BootstrapStacker in stacking/stackers/split_stacker.py)
    """

    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        StackerError if the selected reading mode is not supported
        """
        super().__init__(config)

        self.main_stacker = MergeMeanStacker(config)
        for bootstrap in range(self.num_bootstrap):
            bootstrap_config = copy(config)
            bootstrap_config["hdu name"] = f"BOOTSTRAP_{bootstrap}"
            self.bootstrap_stackers.append(MergeMeanStacker(bootstrap_config))

    def stack(self, spectra):
        """ Stack spectra

        Arguments
        ---------
        spectra: list of Spectrum
        The spectra to stack

        Raise
        -----
        StackerError if the stackers have not been intialized by the child class
        """
        if spectra is not None:
            raise StackerError(
                "MergeBootstrapMeanStacker expects the argument 'spectra' "
                "to be 'None'. This means you probably called this class from "
                "'run_stacking.py' and it should be called only with "
                "'merge_stack_partial_runs.py'. Please double check your "
                "configuration or contact stacking developers if the problem "
                "persists")

        # compute stack
        self.main_stacker.stack(None)

        # compute boostrap realizations
        for stacker in self.bootstrap_stackers:
            stacker.stack(None)

        # compute bootstrap errors
        self.compute_errors()
