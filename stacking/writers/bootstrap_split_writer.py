""" This module defines the class StandardWriter to write the stack results"""
from astropy.io import fits

from stacking.writer import Writer
from stacking.writer import (  # pylint: disable=unused-import
    defaults, accepted_options, required_options)
from stacking.writers.writer_utils import (get_groups_info_hdu,
                                           get_metadata_hdu, get_primary_hdu,
                                           get_split_stack_hdu)


class BootstrapSplitWriter(Writer):
    """Class to write the satck results

    Methods
    -------
    (see StandardWriter in stacking/writer.py)
    write_results

    Attributes
    ----------
    (see StandardWriter in stacking/writer.py
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
        hdu = get_split_stack_hdu(stacker, write_errors=True)

        # bootstrap HDUs
        bootstrap_hdus = [
            get_split_stack_hdu(bootstrap_stacker,
                                hdu_name=f"BOOTSTRAP_{index}") for index,
            bootstrap_stacker in enumerate(stacker.bootstrap_stackers)
        ]

        hdul = fits.HDUList([primary_hdu, hdu, hdu_splits, hdu_metadata] +
                            bootstrap_hdus)
        hdul.writeto(filename, overwrite=self.overwrite, checksum=True)
