""" This module defines the class SplitWriter to write stack results using splits"""
from datetime import datetime

from astropy.io import fits

from stacking._version import __version__

COLUMNS_DESCRIPTION = {
    "IN_STACK": "spectrum included in the stack",
    "LOG_MBH": "log10 of black hole mass",
    "SPECID": "spectrum id",
    "REDSHIFT": "redshift",
    "Z": "redshift",
}


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
