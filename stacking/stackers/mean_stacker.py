""" This module defines the class MeanStacker to compute the stack
using the mean of the stacked values"""
import numpy as np

from stacking.errors import StackerError
from stacking.stacker import Stacker, defaults, accepted_options
from stacking.stacker import required_options  # pylint: disable=unused-import
from stacking.utils import update_accepted_options, update_default_options

ASSOCIATED_WRITER = "StandardWriter"

accepted_options = update_accepted_options(
    accepted_options,
    {
        # option: description
        "sigma_I":
            ("Additional variance added to the inverse variance of the spectra "
             "to suppress the brightest pixels. **Type: float**"),
    })
defaults = update_default_options(defaults, {
    "sigma_I": 0.05,
})


class MeanStacker(Stacker):
    """Class to compute the satck using the mean of the different spectra

    Methods
    -------
    (see Stacker in stacking/stacker.py)
    stack

    Attributes
    ----------
    (see Stacker in stacking/stacker.py)

    sigma_i2: float
    Additional variance added to the inverse variance of the spectra to suppress the 
    brightest pixels
    """

    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class
        """
        super().__init__(config)

        self.sigma_i2 = None
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
        sigma_i = config.getfloat("sigma_I")
        if sigma_i is None:
            raise StackerError("Missing argument 'sigma_I' required by "
                               "MeanStacker")
        if sigma_i < 0:
            raise StackerError("Argument 'sigma_I' should be positive. Found "
                               f"{sigma_i}")
        self.sigma_i2 = sigma_i * sigma_i

    def stack(self, spectra):
        """ Stack spectra

        Arguments
        ---------
        spectra: list of Spectrum
        The spectra to stack
        """
        # TODO: parallelize this to also save memory
        weights = np.stack([
            spectrum.ivar_common_grid /
            (1 + self.sigma_i2 * spectrum.ivar_common_grid)
            for spectrum in spectra
        ])
        self.stacked_flux = np.nansum(
            np.stack([spectrum.normalized_flux for spectrum in spectra]) *
            weights,
            axis=0)
        self.stacked_weight = np.nansum(weights, axis=0)

        # normalize
        good_pixels = np.where(self.stacked_weight != 0.0)
        self.stacked_flux[good_pixels] /= self.stacked_weight[good_pixels]
