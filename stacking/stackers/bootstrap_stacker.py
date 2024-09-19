""" This module defines the class BootstrapStacker to compute bootstrap errors
of the stack"""
import numpy as np

from stacking.errors import StackerError
from stacking.stacker import Stacker
from stacking.stacker import defaults, accepted_options
from stacking.stacker import required_options  # pylint: disable=unused-import
from stacking.utils import (update_accepted_options, update_default_options)

accepted_options = update_accepted_options(
    accepted_options,
    {
        # option: description
        "num booststrap": "Number of bootstrap realizations. **Type: int**",
        "random seed": "Seed for the random number generator. **Type: int**",
    })
defaults = update_default_options(defaults, {
    "num bootstrap": 100,
    "random seed": 65375475,
})


class BootstrapStacker(Stacker):
    """Class to compute stacks with bootstrap errors

    Methods
    -------
    (see Stacker in stacking/stacker.py)
    __init__
    __parse_config
    stack

    Attributes
    ----------
    (see Stacker in stacking/stacker.py)

    bootstrap_stackers: list of Stacker
    Stacker instances that will contain the stacked spectra for each of the
    bootstrap realizations. They will all be instances of the same type as
    `main_stacker`

    main_stacker: Stacker
    Stacker instance that will contain the stacked spectrum/spectra.
    """

    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class
        """
        super().__init__(config)

        self.num_bootstrap = None
        self.random_seed = None
        self.__parse_config(config)

        # This needs to be defined in the child class
        self.main_stacker = None
        self.bootstrap_stackers = []

    def __parse_config(self, config):
        """Parse the configuration options

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        StackerError upon missing required variables
        StackerError if variables are not properly formatted
        StackerError if variables are not coherent
        """
        self.num_bootstrap = config.getint("num bootstrap")
        if self.num_bootstrap is None:
            raise StackerError("Missing argument 'num bootstrap' required by "
                               "BootstrapStacker")
        if self.num_bootstrap < 0:
            raise StackerError(
                "Expected a positive integer for argument 'num boostrap'. "
                f"Found: {self.num_bootstrap}")

        self.random_seed = config.getint("random seed")
        if self.random_seed is None:
            raise StackerError("Missing argument 'random seed' required by "
                               "BootstrapStacker")
        if self.random_seed < 0:
            raise StackerError(
                "Expected a positive integer for argument 'random seed'. "
                f"Found: {self.random_seed}")

    def compute_errors(self):
        """ Compute the bootstrap errors

        Arguments
        ---------
        spectra: list of Spectrum
        The spectra to stack

        Raise
        -----
        StackerError if the stackers have not been intialized by the child class
        """
        self.main_stacker.set_stacked_error(
            np.nanstd(np.stack(
                [stacker.stacked_flux for stacker in self.bootstrap_stackers]),
                      axis=0))

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
        # compute stack
        self.main_stacker.stack(spectra)

        # initialize random seed
        np.random.seed(self.random_seed)

        # compute boostrap realizations
        for stacker in self.bootstrap_stackers:
            bootstrap_set = np.random.choice(spectra, size=len(spectra))
            stacker.stack(bootstrap_set)

        # compute bootstrap errors
        self.compute_errors()
