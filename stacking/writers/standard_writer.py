""" This module defines the class StandardWriter to write the stack results"""
from astropy.io import fits

from stacking.writer import Writer
from stacking.writer import (  # pylint: disable=unused-import
    defaults, accepted_options, required_options)
from stacking.writers.writer_utils import get_primary_hdu, get_simple_stack_hdu


class StandardWriter(Writer):
    """Class to write the satck results

    Methods
    -------
    (see Writer in stacking/writer.py)
    get_stack_hdu
    write_results

    Attributes
    ----------
    (see Writer in stacking/writer.py
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

        # stack HDU
        hdu = get_simple_stack_hdu(stacker)

        hdul = fits.HDUList([primary_hdu, hdu])
        hdul.writeto(filename, overwrite=self.overwrite, checksum=True)
