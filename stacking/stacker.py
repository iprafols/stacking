""" Basic structure for stackers """
import numpy as np

from stacking.errors import StackerError
from stacking.spectrum import Spectrum

accepted_options = []
required_options = []
defaults = {}


class Stacker:
    """Abstract class to define the normalizer skeleton

    Methods
    -------
    __init__
    stack

    Attributes
    ----------
    stacked_flux: array of float
    The stacked flux

    stacked_weight: array of float
    The sum of weights associated with each flux
    """

    def __init__(self, config):  # pylint: disable=unused-argument
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Ignored, passed here to have consistent inheritance calls

        Raise
        -----
        StackerError if the selected reading mode is not supported
        """

        # initialize results
        if Spectrum.common_wavelength_grid is None:
            raise StackerError(
                "Spectrum.common_wavelength_grid must be set to initialize any "
                "Stacker instances")
        self.stacked_flux = np.zeros(Spectrum.common_wavelength_grid.size)
        self.stacked_error = np.zeros(Spectrum.common_wavelength_grid.size)
        self.stacked_weight = np.zeros(Spectrum.common_wavelength_grid.size)

    def set_stacked_error(self, stacked_error):
        """ Set the stacked error

        Arguments
        ---------
        stacked_error: np.array
        The stacked error

        Raise
        -----
        StackerError if the shape of the passed array does not match the
        existing array
        """
        if stacked_error.shape != self.stacked_error.shape:
            raise StackerError(
                "Invalid array when attempting to set the stack error. Shapes "
                f"do not match. Expected {self.stacked_error.shape}. Found "
                f"{stacked_error.shape}")
        self.stacked_error = stacked_error

    def stack(self, spectra):
        """ Stack spectra

        Arguments
        ---------
        spectra: list of Spectrum
        The spectra to stack

        Raise
        -----
        StackerError if function was not overloaded by child class
        """
        raise StackerError("Method 'stack' was not overloaded by child class")
