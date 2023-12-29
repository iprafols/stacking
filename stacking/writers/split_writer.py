""" This module defines the class SplitWriter to write stack results using splits"""
from astropy.io import fits

from stacking.spectrum import Spectrum
from stacking.writer import Writer
from stacking.writer import (  # pylint: disable=unused-import
    defaults, accepted_options, required_options)
from stacking.writers.writer_utils import get_primary_hdu


class SplitWriter(Writer):
    """Class to write the satck results using splits

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
        primary_hdu = get_primary_hdu(stacker)

        # splits info
        cols_splits = []
        for col, dtype in zip(stacker.split_catalogue.columns,
                              stacker.split_catalogue.dtypes):
            if "float" in dtype:
                cols_splits.append(
                    fits.Column(name=col,
                                format="E",
                                disp="F7.3",
                                array=stacker.split_catalogue[col].values))
            elif "int" in dtype:
                cols_splits.append(
                    fits.Column(name=col,
                                format="K",
                                disp="K",
                                array=stacker.split_catalogue[col].values))
            else:
                cols_splits.append(
                    fits.Column(name=col,
                                format="20A",
                                disp="20A",
                                array=stacker.split_catalogue[col].values))
        hdu_splits = fits.BinTableHDU.from_columns(cols_splits,
                                                   name="SPLITS_INFO")

        # fluxes and weights
        cols_spectra = [
            fits.Column(name="WAVELENGTH",
                        format="E",
                        disp="F7.3",
                        array=Spectrum.common_wavelength_grid),
            fits.Column(name="STACKED_FLUX",
                        format=f"{stacker.num_groups}E",
                        disp="F7.3",
                        array=stacker.stacked_flux),
            fits.Column(name="STACKED_WEIGHT",
                        format=f"{stacker.num_groups}E",
                        disp="F7.3",
                        array=stacker.stacked_weight),
        ]
        hdu = fits.BinTableHDU.from_columns(cols_spectra,
                                            name="STACKED_SPECTRA")
        # TODO: add description of columns

        hdul = fits.HDUList([primary_hdu, hdu_splits, hdu])
        hdul.writeto(filename, overwrite=self.overwrite, checksum=True)
