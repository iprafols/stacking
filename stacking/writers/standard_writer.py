""" This module defines the class StandardWriter to write the stack results"""
from datetime import datetime

from astropy.io import fits

from stacking._version import __version__
from stacking.spectrum import Spectrum
from stacking.writer import Writer
from stacking.writer import (  # pylint: disable=unused-import
    defaults, accepted_options, required_options)


class StandardWriter(Writer):
    """Class to write the satck results

    Methods
    -------
    (see Writer in stacking/writer.py)

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
        primary_hdu = fits.PrimaryHDU()
        now = datetime.now()
        primary_hdu.header["COMMENT"] = (
            f"Stacked spectrum computed using class {type(stacker)}"
            f" of code stacking")
        primary_hdu.header["VERSION"] = (__version__, "Code version")
        primary_hdu.header["DATETIME"] = (now.strftime("%Y-%m-%dT%H:%M:%S"),
                                          "DateTime file created")

        # norm factors
        cols = [
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
        hdu = fits.BinTableHDU.from_columns(cols, name="STACKED_SPECTRUM")
        # TODO: add description of columns

        hdul = fits.HDUList([primary_hdu, hdu])
        hdul.writeto(filename, overwrite=self.overwrite, checksum=True)
