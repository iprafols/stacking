""" This module defines the class MedianStacker to compute the stack
using the median of the stacked values"""
import warnings

import numpy as np

from stacking.errors import StackerError
from stacking.stacker import Stacker, defaults, accepted_options
from stacking.stacker import (  # pylint: disable=unused-import
    required_options)
from stacking.utils import update_accepted_options, update_default_options

accepted_options = update_accepted_options(accepted_options, ["weighted"])
defaults = update_default_options(defaults, {"weighted": False})

ASSOCIATED_WRITER = "StandardWriter"


class MedianStacker(Stacker):
    """Class to compute the satck using the median of the different spectra

    Methods
    -------
    (see Stacker in stacking/stacker.py)
    stack

    Attributes
    ----------
    (see Stacker in stacking/stacker.py)

    weighted: boolean
    If True, then compute the weighted median. Otherwise, compute the regular
    median
    """

    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class
        """
        super().__init__(config)

        self.weighted = None
        self.__parse_config(config)

    def __parse_config(self, config):
        """Parse the configuration options

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        StackerError upon missing required variables
        """
        self.weighted = config.getboolean("weighted")
        if self.weighted is None:
            raise StackerError(
                "Missing argument 'weighted' required by MedianStacker")

    def stack(self, spectra):
        """ Stack spectra

        Arguments
        ---------
        spectra: list of Spectrum
        The spectra to stack
        """
        if self.weighted:  # pylint: disable=no-else-raise
            # TODO: compute weighted median
            raise StackerError("Not implemented")
        else:
            # TODO: parallelize this to also save memory
            with warnings.catch_warnings():
                # suppress known RuntimeWarnings
                warnings.filterwarnings(
                    "ignore", message="invalid value encountered in divide")
                warnings.filterwarnings("ignore",
                                        message="All-NaN slice encountered")

                self.stacked_flux = np.nanmedian(np.stack([
                    spectrum.normalized_flux / (spectrum.ivar_common_grid != 0)
                    for spectrum in spectra
                ]),
                                                 axis=0)

            self.stacked_weight = np.nansum(np.stack(
                [spectrum.ivar_common_grid for spectrum in spectra]),
                                            axis=0)
