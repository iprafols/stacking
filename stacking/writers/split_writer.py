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

        # metadata spectra
        cols_metadata = []
        for col, dtype in zip(stacker.split_catalogue.columns,
                              stacker.split_catalogue.dtypes):
            if dtype in ["float32", "float64"]:
                cols_metadata.append(
                    fits.Column(name=col,
                                format="E",
                                disp="F7.3",
                                array=stacker.split_catalogue[col].values))
            elif dtype in ["int32", "int64"]:
                cols_metadata.append(
                    fits.Column(name=col,
                                format="K",
                                disp="I10",
                                array=stacker.split_catalogue[col].values))
            else:
                cols_metadata.append(
                    fits.Column(name=col,
                                format="20A",
                                disp="A20",
                                array=stacker.split_catalogue[col].values))
        hdu_metadata = fits.BinTableHDU.from_columns(cols_metadata,
                                                     name="METADATA_SPECTRA")
        # TODO: add description of columns

        # groups info
        cols_splits = []
        for col, dtype in zip(stacker.groups_info.columns,
                              stacker.groups_info.dtypes):
            if dtype in ["float32", "float64"]:
                cols_splits.append(
                    fits.Column(name=col,
                                format="E",
                                disp="F7.3",
                                array=stacker.groups_info[col].values))
            elif dtype in ["int32", "int64"]:
                cols_splits.append(
                    fits.Column(name=col,
                                format="K",
                                disp="I10",
                                array=stacker.groups_info[col].values))
            else:
                cols_splits.append(
                    fits.Column(name=col,
                                format="20A",
                                disp="A20",
                                array=stacker.groups_info[col].values))
        hdu_splits = fits.BinTableHDU.from_columns(cols_splits,
                                                   name="GROUPS_INFO")
        hdu_splits.header["NGROUPS"] = stacker.num_groups
        # TODO: add description of columns

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
        hdu = fits.BinTableHDU.from_columns(cols_spectra, name="STACK")
        # TODO: add description of columns

        hdul = fits.HDUList([
            primary_hdu,
            hdu,
            hdu_splits,
            hdu_metadata,
        ])
        hdul.writeto(filename, overwrite=self.overwrite, checksum=True)
