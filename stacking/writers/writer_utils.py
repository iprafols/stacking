""" This module defines the class SplitWriter to write stack results using splits"""
from datetime import datetime
import logging

from astropy.io import fits

from stacking._version import __version__
from stacking.errors import WriterError
from stacking.spectrum import Spectrum

COLUMNS_DESCRIPTION = {
    "IN_STACK": "spectrum included in the stack",
    "LOG_MBH": "log10 of black hole mass",
    "SPECID": "spectrum id",
    "REDSHIFT": "redshift",
    "Z": "redshift",
}

LOGGER = logging.getLogger(__name__)


def get_groups_info_hdu(stacker):
    """Prepare the GROUPS_INFO HDU, including the information about the different
    splits

    Arguments
    ---------
    stacker: Stacker
    The used stacker

    hdu_name: str - Default: True
    HDU name

    write_errors: bool - Default: False
    If True, also write the stack errors. Pass False if they are not
    computed and thus need not be saved

    Return
    ------
    hdu_groups: fits.BinTableHDU
    The HDU
    """
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
    hdu_groups = fits.BinTableHDU.from_columns(cols_splits, name="GROUPS_INFO")
    hdu_groups.header["NGROUPS"] = (stacker.num_groups, "Number of groups")
    for key in hdu_groups.header:
        if key.startswith("TDISP"):
            hdu_groups.header.comments[key] = "display format for column"
        elif key.startswith("TFORM"):
            if hdu_groups.header[key].endswith("A"):
                hdu_groups.header.comments[
                    key] = f"data format of field: str ({hdu_groups.header[key][:-1]} chars)"
            elif hdu_groups.header[key] == "E":
                hdu_groups.header.comments[
                    key] = "data format of field: float (32-bit)"
            elif hdu_groups.header[key] == "J":
                hdu_groups.header.comments[
                    key] = "data format of field: int (32-bit)"
            # this should never enter unless new variables need to be saved
            # with double precision
            else:  # pragma: no cover
                raise WriterError(
                    "Error writing fits file. Cannot assign comment for field "
                    f"{key}. Please review changes in method `write_results` "
                    "or contact 'stacking' developpers.")
        elif key.startswith("TTYPE"):
            if hdu_groups.header[key].startswith("VARIABLE"):
                hdu_groups.header.comments[
                    key] = "variable used to perform the split"
            elif hdu_groups.header[key].startswith("MIN_VALUE"):
                hdu_groups.header.comments[
                    key] = "minimum value to enter the split (included)"
            elif hdu_groups.header[key].startswith("MAX_VALUE"):
                hdu_groups.header.comments[
                    key] = "maximum value to enter the split (excluded)"
            elif hdu_groups.header[key] == "COLNAME":
                hdu_groups.header.comments[
                    key] = "Relevant group column for the split"
            elif hdu_groups.header[key] == "GROUP_NUM":
                hdu_groups.header.comments[key] = "Group number for the split"
            # this should never enter unless new variables need to be saved
            # and are not correctly added
            else:  # pragma: no cover
                raise WriterError(
                    "Error writing fits file. Cannot assign comment for field "
                    f"{key}. Please review changes in method `write_results` "
                    "or contact 'stacking' developpers.")

    return hdu_groups


def get_metadata_hdu(stacker):
    """Prepare the METADATA_SPECTRA HDU, including the metadata of the spectra
    belonging to the different splits

    Arguments
    ---------
    stacker: Stacker
    The used stacker

    hdu_name: str - Default: True
    HDU name

    write_errors: bool - Default: False
    If True, also write the stack errors. Pass False if they are not
    computed and thus need not be saved

    Return
    ------
    hdu_metadata: fits.BinTableHDU
    The HDU
    """
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
        elif dtype in ["bool"]:
            cols_metadata.append(
                fits.Column(name=col,
                            format="L",
                            disp="L1",
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
            elif hdu_metadata.header[key] == "L":
                hdu_metadata.header.comments[
                    key] = "data format of field: boolean"
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
                    f"{hdu_metadata.header[key]}. I will leave it"
                    "empty. If you want it added, add its description to "
                    "variable `COLUMNS_DESCRIPTION` in file `writers/writer_utils.py`"
                    "and rerun.")
                LOGGER.warning(message)
    return hdu_metadata


def get_primary_hdu(stacker):
    """Prepare the primary HDU

    Arguments
    ---------
    stacker: Stacker
    The used stacker

    Return
    ------
    primary_hdu: fits.hdu.image.PrimaryHDU
    The primary HDU
    """
    # primary HDU
    primary_hdu = fits.PrimaryHDU()
    now = datetime.now()
    primary_hdu.header["COMMENT"] = (
        f"Stacked spectrum computed using class {stacker.__class__.__name__}"
        f" of code stacking")
    primary_hdu.header["VERSION"] = (__version__, "Code version")
    primary_hdu.header["DATETIME"] = (now.strftime("%Y-%m-%dT%H:%M:%S"),
                                      "DateTime file created")

    return primary_hdu


def get_simple_stack_hdu(stacker, hdu_name="STACK", write_errors=False):
    """Prepare the STACK HDU, including the stacked fluxes, weights and
    errors

    Arguments
    ---------
    stacker: Stacker
    The used stacker

    hdu_name: str - Default: True
    HDU name

    write_errors: bool - Default: False
    If True, also write the stack errors. Pass False if they are not
    computed and thus need not be saved

    Return
    ------
    hdu: fits.BinTableHDU
    The HDU
    """
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
    if write_errors:
        cols_spectrum += [
            fits.Column(name="STACKED_ERROR",
                        format="E",
                        disp="F7.3",
                        array=stacker.stacked_error),
        ]

    hdu = fits.BinTableHDU.from_columns(cols_spectrum, name=hdu_name)
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
    if write_errors:
        desc.update({
            "TTYPE4": "error of normallized stacked flux",
            "TFORM4": "data format of field: float (32-bit)",
            "TDISP4": "display format for column",
        })
    for key, value in desc.items():
        hdu.header.comments[key] = value

    return hdu


def get_split_stack_hdu(stacker, hdu_name="STACK", write_errors=False):
    """Prepare the STACK HDU, including the stacked fluxes, weights and
    errors for the different splits

    Arguments
    ---------
    stacker: Stacker
    The used stacker

    hdu_name: str - Default: True
    HDU name

    write_errors: bool - Default: False
    If True, also write the stack errors. Pass False if they are not
    computed and thus need not be saved

    Return
    ------
    hdu: fits.BinTableHDU
    The HDU
    """
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
    if write_errors:
        cols_spectra += [
            fits.Column(name="STACKED_ERROR",
                        format=f"{stacker.num_groups}E",
                        disp="F7.3",
                        array=stacker.stacked_error),
        ]
    hdu = fits.BinTableHDU.from_columns(cols_spectra, name=hdu_name)
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
    if write_errors:
        desc.update({
            "TTYPE4": "error of normallized stacked flux arrays",
            "TFORM4": "data format of field: float (32-bit)",
            "TDISP4": "display format for column",
        })
    for key, value in desc.items():
        hdu.header.comments[key] = value
    hdu.header["COMMENT"] = (
        "To access arrays for split n do `data['STACKED_FLUX'][:,n]` and "
        "`data['STACKED_WEIGHT'][:,n]`")

    return hdu
