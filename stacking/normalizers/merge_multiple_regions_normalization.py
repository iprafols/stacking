""" This module define the class MergeMultipleRegionsNornalization that merge
the results of multiple runs of partial samples"""
import logging
import sys

import pandas as pd

from stacking._version import __version__
from stacking.errors import NormalizerError
from stacking.normalizers.multiple_regions_normalization import (
    MultipleRegionsNormalization, defaults, accepted_options, required_options)
from stacking.normalizers.multiple_regions_normalization_utils import (
    save_correction_factors_ascii, save_norm_factors_ascii,
    save_norm_factors_fits, select_final_normalisation_factor)
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)

accepted_options = update_accepted_options(accepted_options,
                                           ["folders list", "save on list"])
accepted_options = update_accepted_options(accepted_options, [
    "load norm factors from",
],
                                           remove=True)
defaults = update_default_options(defaults, {
    "save on list": True,
})
required_options = update_required_options(required_options, [
    "folders list",
])


class MergeMultipleRegionsNormalization(MultipleRegionsNormalization):
    """This class is set to compute the normalization factors using multiple
    normalization regions.

    Contrary to the parent class, here we assume we have a set of partial runs.
    They are merged and the correction factors are computed.
    Thus, after computing the normalization factors, they will be saved and the
    program will end.

    To be implemented:
    Optionally combine with normalization factors loaded from previous runs

    Methods
    -------
    (see MultipleRegionsNormalization in stacking/normalizers/multiple_regions_normalization.py)
    __init__
    __parse_config
    compute_norm_factors

    Attributes
    ----------
    (see MultipleRegionsNormalization in stacking/normalizers/multiple_regions_normalization.py)

    logger: logging.Logger
    Logger object

    """

    def __init__(self, config):
        """ Initialize instance """
        super().__init__(config)

        self.logger = logging.getLogger(__name__)

        # load variables from config
        self.folders_list = []
        self.save_on_list = None
        self.__parse_config(config)

        # variable to keep the nromalization factors of each of the loaded files
        self.norm_factors_list = None

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
        folders_list = config.get("folders list")
        if folders_list is None:
            raise NormalizerError("Missing argument 'folders list' required by "
                                  "MergeMultipleRegionsNormalization")
        self.folders_list = folders_list.split()

        self.save_on_list = config.getboolean("save on list")
        if self.save_on_list is None:
            raise NormalizerError("Missing argument 'save on list' required by "
                                  "MergeMultipleRegionsNormalization")

    def compute_norm_factors(self, spectra):
        """Load and merge the different normalization factors

        Arguments
        ---------
        spectra: None

        """
        if spectra is not None:
            raise NormalizerError(
                "MergeMultipleRegionsNormalization expects the argument 'spectra' "
                "to be 'None'. This means you probably called this class from "
                "'run_stacking.py' and it should be called only with "
                "'merge_norm_factors_partial_runs.py'. Please double check your "
                "configuration or contact stacking developers if the problem "
                "persists")

        self.norm_factors_list = [
            self.load_norm_factors(folder)[0] for folder in self.folders_list
        ]
        # compute nromalization factors
        self.norm_factors = pd.concat(self.norm_factors_list)

        # compute correction factors
        self.compute_correction_factors()

        # select final normalisation factor
        self.select_final_normalisation_factor()

        # save results
        self.save_norm_factors()

        # exit
        self.logger.warning(
            "The normalizer PartialMultipleRegionsNormalization does not include "
            "a complete computation by construction. Exiting...")
        sys.exit(0)

    def save_norm_factors(self):
        """ Save the normalisation factors for future reference """
        if self.save_on_list:
            self.logger.progress("Saving normalization factors on input list")
            for log_directory, norm_factors in zip(self.folders_list,
                                                   self.norm_factors_list):
                filename = f"{log_directory}normalization_factors.{self.save_format}"

                # save as ascii file
                if self.save_format in ["csv", "txt"]:
                    # norm factors
                    save_norm_factors_ascii(filename, norm_factors)

                    # correction_factors
                    filename = f"{log_directory}correction_factors.{self.save_format}"
                    save_correction_factors_ascii(filename,
                                                  self.correction_factors)

                # save as fits file
                elif self.save_format in ["fits", "fits.gz"]:
                    save_norm_factors_fits(filename, norm_factors,
                                           self.intervals,
                                           self.correction_factors)

                # this should never enter unless new saving formats are not properly added
                else:  # pragma: no cover
                    raise NormalizerError(
                        f"Don't know what to do with save format {self.save_format}. "
                        "This is one of the supported saving formats, maybe it "
                        "was not properly coded. If you did the change yourself, check "
                        "that you added the behaviour of the new mode to method "
                        "`save_norm_factors`. Otherwise contact 'stacking' developpers."
                    )

        self.logger.progress("Saving normalization factors")
        super().save_norm_factors()

    def select_final_normalisation_factor(self):
        """Select the final normalization factors"""
        if self.save_on_list:
            for item in self.norm_factors_list:
                item[["norm factor", "norm S/N",
                      "chosen interval"]] = item.apply(
                          select_final_normalisation_factor,
                          axis=1,
                          args=(self.correction_factors,),
                          result_type='expand',
                      )
        super().select_final_normalisation_factor()
