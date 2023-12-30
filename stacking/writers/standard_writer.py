""" This module defines the class StandardWriter to write the stack results"""
from astropy.io import fits

from stacking.spectrum import Spectrum
from stacking.writer import Writer
from stacking.writer import (  # pylint: disable=unused-import
    defaults, accepted_options, required_options)
from stacking.writers.writer_utils import get_primary_hdu


class StandardWriter(Writer):
    """Class to write the satck results

    Methods
    -------
    (see Writer in stacking/writer.py)
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

        # fluxes and weights
        cols_spectrum = [
            fits.Column(name="WAVELENGTH",
                        format="E",
                        disp="F7.3",
                        array=Spectrum.common_wavelength_grid),
            fits.Column(name="STACKED_FLUX",
                        format="E",
                        disp="F7.3",
                        array=stacker.stacked_flux),
            fits.Column(name="STACKED_WEIGHT",
                        format="E",
                        disp="F7.3",
                        array=stacker.stacked_weight),
        ]
        hdu = fits.BinTableHDU.from_columns(cols_spectrum, name="STACK")
        desc = {
            "TTYPE1": "wavelength array",
            "TFORM1": "data format of field: float (32-bit)",
            "TDISP1": "display format for column",
            "TTYPE2": "normalized stacked flux",
            "TFORM2": "data format of field: float (32-bit)",
            "TDISP2": "display format for column",
            "TTYPE3": "total weight in stack flux",
            "TFORM3": "data format of field: float (32-bit)",
            "TDISP3": "display format for column",
        }
        for key, value in desc.items():
            hdu.header.comments[key] = value

        hdul = fits.HDUList([primary_hdu, hdu])
        hdul.writeto(filename, overwrite=self.overwrite, checksum=True)
