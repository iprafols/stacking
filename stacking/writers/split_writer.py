""" This module defines the class SplitWriter to write stack results using splits"""
import logging

from astropy.io import fits

from stacking.errors import WriterError
from stacking.spectrum import Spectrum
from stacking.writer import Writer
from stacking.writer import (  # pylint: disable=unused-import
    defaults, accepted_options, required_options)
from stacking.writers.writer_utils import get_primary_hdu, COLUMNS_DESCRIPTION


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

    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class
        """
        self.logger = logging.getLogger(__name__)
        super().__init__(config)

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
                                format="J",
                                disp="I10",
                                array=stacker.split_catalogue[col].values))
            # this should never enter unless new splits types are added
            # (e.g. using characters)
            else:  # pragma: no cover
                raise WriterError(
                    f"Don't know what to do with type {dtype}. "
                    "I was expecting splits to be either 'float' or 'int'."
                    "If you changed this yourself, check that you added the "
                    "new behaviour to method `write_results`. "
                    "Otherwise contact 'stacking' developpers.")
        hdu_metadata = fits.BinTableHDU.from_columns(cols_metadata,
                                                     name="METADATA_SPECTRA")
        for key in hdu_metadata.header:
            if key.startswith("TDISP"):
                hdu_metadata.header.comments[key] = "display format for column"
            elif key.startswith("TFORM"):
                if hdu_metadata.header[key] == "E":
                    hdu_metadata.header.comments[
                        key] = "data format of field: float (32-bit)"
                elif hdu_metadata.header[key] == "J":
                    hdu_metadata.header.comments[
                        key] = "data format of field: int (32-bit)"
                # this should never enter unless new variables need to be saved
                # with double precision
                else:  # pragma: no cover
                    raise WriterError(
                        "Error writing fits file. Cannot assign comment for field "
                        f"{key}. Please review changes in method `write_results` "
                        "or contact 'stacking' developpers.")
            elif key.startswith("TTYPE"):
                if hdu_metadata.header[key].startswith("GROUP"):
                    hdu_metadata.header.comments[key] = "group number"
                elif hdu_metadata.header[key] in COLUMNS_DESCRIPTION:
                    hdu_metadata.header.comments[key] = COLUMNS_DESCRIPTION.get(
                        hdu_metadata.header[key])
                else:
                    message = (
                        "I don't know which comment to add to field "
                        f"{hdu_metadata.header.comments[key]}. I will leave it"
                        "empty. If you want it added, add its description to "
                        "variable `COLUMNS_DESCRIPTION` in file `writers/writer_utils.py`"
                        "and rerun.")
                    self.logger.warning(message)

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
                                format="J",
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
        hdu_splits.header["NGROUPS"] = (stacker.num_groups, "Number of groups")
        for key in hdu_splits.header:
            if key.startswith("TDISP"):
                hdu_splits.header.comments[key] = "display format for column"
            elif key.startswith("TFORM"):
                if hdu_splits.header[key].endswith("A"):
                    hdu_splits.header.comments[
                        key] = f"data format of field: str ({hdu_splits.header[key][:-1]} chars)"
                elif hdu_splits.header[key] == "E":
                    hdu_splits.header.comments[
                        key] = "data format of field: float (32-bit)"
                elif hdu_splits.header[key] == "J":
                    hdu_splits.header.comments[
                        key] = "data format of field: int (32-bit)"
                # this should never enter unless new variables need to be saved
                # with double precision
                else:  # pragma: no cover
                    raise WriterError(
                        "Error writing fits file. Cannot assign comment for field "
                        f"{key}. Please review changes in method `write_results` "
                        "or contact 'stacking' developpers.")
            elif key.startswith("TTYPE"):
                if hdu_splits.header[key].startswith("VARIABLE"):
                    hdu_splits.header.comments[
                        key] = "variable used to perform the split"
                elif hdu_splits.header[key].startswith("MIN_VALUE"):
                    hdu_splits.header.comments[
                        key] = "minimum value to enter the split (included)"
                elif hdu_splits.header[key].startswith("MAX_VALUE"):
                    hdu_splits.header.comments[
                        key] = "maximum value to enter the split (excluded)"
                elif hdu_splits.header[key] == "COLNAME":
                    hdu_splits.header.comments[
                        key] = "Relevant group column for the split"
                elif hdu_splits.header[key] == "GROUP_NUM":
                    hdu_splits.header.comments[
                        key] = "Group number for the split"
                # this should never enter unless new variables need to be saved
                # and are not correctly added
                else:  # pragma: no cover
                    raise WriterError(
                        "Error writing fits file. Cannot assign comment for field "
                        f"{key}. Please review changes in method `write_results` "
                        "or contact 'stacking' developpers.")

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
        desc = {
            "TTYPE1":
                "wavelength array",
            "TFORM1":
                "data format of field: float (32-bit)",
            "TDISP1":
                "display format for column",
            "TTYPE2":
                "normalized stacked flux arrays",
            "TFORM2":
                f"data format of field: {stacker.num_groups} * float (32-bit)",
            "TDISP2":
                "display format for column",
            "TTYPE3":
                "total weight in stack flux arrays",
            "TFORM3":
                f"data format of field: {stacker.num_groups} * float (32-bit)",
            "TDISP3":
                "display format for column",
        }
        for key, value in desc.items():
            hdu.header.comments[key] = value
        hdu.header["COMMENT"] = (
            "To access arrays for split n do `data['STACKED_FLUX'][:,n]` and "
            "`data['STACKED_WEIGHT'][:,n]`")

        hdul = fits.HDUList([
            primary_hdu,
            hdu,
            hdu_splits,
            hdu_metadata,
        ])
        hdul.writeto(filename, overwrite=self.overwrite, checksum=True)
