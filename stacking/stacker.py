""" Basic structure for stackers """
import logging
import numpy as np

from stacking.errors import StackerError
from stacking.spectrum import Spectrum

required_options = []


class Stacker:
    """Abstract class to define the normalizer skeleton

    Methods
    -------
    __init__
    __parser
    stack

    Attributes
    ----------
    logger: logging.Logger
    Logger object

    stack_result: spectrum or list of Spectrum
    The resulting stack
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

        # load variables from config
        self.num_processors = None
        self.__parse_config(config)

        # initialize results
        self.stacked_flux = np.zeros(Spectrum.common_wavelength_grid.size)
        self.stacked_total_weight = np.zeros(
            Spectrum.common_wavelength_grid.size)

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
        self.num_processors = config.getint("num processors")
        if self.num_processors is None:
            raise StackerError("Missing argument 'num processors' required by "
                               "Stacker")

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
        raise StackerError("Method 'stack' was not overloaded by child class")
