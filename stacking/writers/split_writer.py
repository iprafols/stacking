""" This module defines the class SplitWriter to write stack results using splits"""
from astropy.io import fits

from stacking.writer import Writer
from stacking.writer import (  # pylint: disable=unused-import
    defaults, accepted_options, required_options)
from stacking.writers.writer_utils import (get_groups_info_hdu,
                                           get_metadata_hdu, get_primary_hdu,
                                           get_split_stack_hdu)


class SplitWriter(Writer):
    """Class to write the satck results using splits

    Methods
    -------
    (see Writer in stacking/writer.py)
    __init__
    write_results

    Attributes
    ----------
    (see Writer in stacking/writer.py)

    logger: logging.Logger
    Logger object
    """

    def write_results(self, stacker):
        """Write the results

        Arguments
        ---------
        stacker: Stacker
        The used stacker
        """
        filename = self.output_directory + self.output_file

        # primary HDU
        primary_hdu = get_primary_hdu(stacker)

        # metadata spectra
        hdu_metadata = get_metadata_hdu(stacker)

        # groups info
        hdu_splits = get_groups_info_hdu(stacker)

        # fluxes and weights
        hdu = get_split_stack_hdu(stacker)

        hdul = fits.HDUList([
            primary_hdu,
            hdu,
            hdu_splits,
            hdu_metadata,
        ])
        hdul.writeto(filename, overwrite=self.overwrite, checksum=True)
