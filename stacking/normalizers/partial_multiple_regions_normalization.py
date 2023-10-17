""" This module define the class PartialMultipleRegionsNornalization that computes
the normalization factor using multiple regions on a partial sample"""
import logging
import sys

from stacking._version import __version__
from stacking.errors import NormalizerError
from stacking.normalizers.multiple_regions_normalization import (
    MultipleRegionsNormalization, defaults, accepted_options)
from stacking.normalizers.multiple_regions_normalization import (  # pylint: disable=unused-import
    required_options)

from stacking.utils import update_accepted_options, update_default_options

accepted_options = update_accepted_options(accepted_options, [
    "compute correction factors flag",
])
accepted_options = update_accepted_options(accepted_options, [
    "load norm factors from",
],
                                           remove=True)
defaults = update_default_options(defaults, {
    "compute correction factors flag": False,
})


class PartialMultipleRegionsNormalization(MultipleRegionsNormalization):
    """This class is set to compute the normalization factors using multiple
    normalization regions.

    Contrary to the parent class, here we assume a partial sample will be loaded
    Thus, after computing the normalization factors, they will be saved and the
    program will end.

    Methods
    -------
    (see MultipleRegionsNormalization in stacking/normalizers/multiple_regions_normalization.py)
    __init__
    __parse_config
    compute_correction_factors
    compute_norm_factors

    Attributes
    ----------
    (see MultipleRegionsNormalization in stacking/normalizers/multiple_regions_normalization.py)

    logger: logging.Logger
    Logger object

    compute_norm_factors_flag: bool
    If True, conpute
    """

    def __init__(self, config):
        """ Initialize instance """
        super().__init__(config)

        self.logger = logging.getLogger(__name__)

        # load variables from config
        self.compute_correction_factors_flag = None
        self.__parse_config(config)

    def __parse_config(self, config):
        """Parse the configuration options

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        NormalizerError upon missing required variables
        """
        self.compute_correction_factors_flag = config.getboolean(
            "compute correction factors flag")
        if self.compute_correction_factors_flag is None:
            raise NormalizerError(
                "Missing argument 'compute correction factors flag' required by "
                "PartialMultipleRegionsNormalization")

    def compute_correction_factors(self):
        """ Compute the correction factor that relate the differnt intervals

        Raise
        -----
        NormalizerError if any of the correction factor cannot be computed
        """
        if self.compute_correction_factors_flag:
            super().compute_correction_factors()

    def compute_norm_factors(self, spectra):
        """ Compute the normalization factors

        Arguments
        ---------
        spectra: list of Spectrum
        The list of spectra
        """
        # compute nromalization factors
        super().compute_norm_factors(spectra)

        # save results
        self.logger.progress("Saving normalization factors")
        self.save_norm_factors()

        # exit
        self.logger.warning(
            "The normalizer PartialMultipleRegionsNormalization does not include "
            "a complete computation by construction. Exiting...")
        sys.exit(0)
