""" This module defines the class MeanStacker to compute the stack
using the mean of the stacked values"""
import logging
import numpy as np

from stacking.spectrum import Spectrum
from stacking.stacker import Stacker


class MeanStacker(Stacker):
    """Class to compute the satck using the mean of the different spectra

    Methods
    -------
    (see Stacker in stacking/stacker.py)
    __init__
    stack

    Attributes
    ----------
    (see Stacker in stacking/stacker.py)

    logger: logging.Logger
    Logger object

    stacked_flux: array of float
    The stacked flux

    stacked_weight: array of float
    The sum of weights associated with each flux

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
        self.logger = logging.getLogger(__name__)
        super().__init__(config)

        # initialize results
        self.stacked_flux = np.zeros(Spectrum.common_wavelength_grid.size)
        self.stacked_weight = np.zeros(Spectrum.common_wavelength_grid.size)

    def stack(self, spectra):
        """ Stack spectra

        Arguments
        ---------
        spectra: list of Spectrum
        The spectra to stack

        Raise
        -----
        ReaderError if function was not overloaded by child class
        """
        for spectrum in spectra:
            self.stacked_flux += spectrum.flux * spectrum.ivar
            self.stacked_weight += spectrum.ivar

        # normalize
        good_pixels = np.where(self.stacked_weight == 0.0)
        self.stacked_flux[good_pixels] /= self.stacked_weight[good_pixels]
