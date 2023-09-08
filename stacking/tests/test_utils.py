"""This file defines variables needed for different tests"""
from configparser import ConfigParser
from copy import copy
import os

import numpy as np
import pandas as pd

from stacking.logging_utils import setup_logger, reset_logger
from stacking.readers.dr16_reader import Dr16Reader
from stacking.readers.dr16_reader import defaults as defaults_dr16_reader
from stacking.rebin import Rebin
from stacking.rebin import defaults as defaults_rebin
from stacking.spectrum import Spectrum

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR

# setup logger
# this must happen at the very beginning of the module
setup_logger()

# initialize reader
config = ConfigParser()
config.read_dict({
    "reader": {
        "drq catalogue": f"{THIS_DIR}/data/drq_catalogue_plate3655.fits.gz",
        "input directory": f"{THIS_DIR}/data",
    },
    "rebin": {
        "max wavelength": 4999.1941102499995,
        "min wavelength": 1000,
        "step type": "log",
        "step wavelength": 1e-4,
    }
})
for key, value in defaults_dr16_reader.items():
    if key not in config["reader"]:
        config["reader"][key] = str(value)
for key, value in defaults_rebin.items():
    if key not in config["rebin"]:
        config["rebin"][key] = str(value)

reader = Dr16Reader(config["reader"])

# read spectra
SPECTRA = reader.read_data()

assert len(reader.catalogue) == 93
assert len(reader.spectra) == 92
assert reader.read_mode == "spplate"
assert len(SPECTRA) == 92
for spectrum in SPECTRA:
    assert isinstance(spectrum, Spectrum)
    assert spectrum.flux_common_grid is None
    assert spectrum.ivar_common_grid is None
    assert spectrum.normalized_flux is None

rebin = Rebin(config["rebin"])

# rebin spectra
COMMON_WAVELENGTH_GRID = 10**np.linspace(np.log10(1000),
                                         np.log10(4999.1941102499995), 6989)
REBINNED_SPECTRA = [rebin(copy(spectrum)) for spectrum in SPECTRA]

for spectrum in SPECTRA:
    assert isinstance(spectrum, Spectrum)
    assert spectrum.flux_common_grid is None
    assert spectrum.ivar_common_grid is None
    assert spectrum.normalized_flux is None

assert np.allclose(Spectrum.common_wavelength_grid, COMMON_WAVELENGTH_GRID)
for spectrum in REBINNED_SPECTRA:
    assert isinstance(spectrum, Spectrum)
    assert spectrum.flux_common_grid is not None
    assert spectrum.ivar_common_grid is not None
    assert spectrum.normalized_flux is None

# normalization factors
NORM_FACTORS = pd.read_csv(f"{THIS_DIR}/data/normalization_factors.txt")

# correction factors

CORRECTION_FACTORS = np.array([
    float(line.split(",")[1])
    for line in open(f"{THIS_DIR}/data/correction_factors.txt",
                     encoding="utf-8").readlines()
    if not line.startswith("interval,correction factor")
])

# reset logger
# this must happen at the very end of the module
reset_logger()

if __name__ == '__main__':
    pass
