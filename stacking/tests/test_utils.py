"""This file defines variables needed for different tests"""
from configparser import ConfigParser
import os

from stacking.logging_utils import setup_logger, reset_logger
from stacking.readers.dr16_reader import Dr16Reader
from stacking.readers.dr16_reader import defaults as defaults_dr16_reader
from stacking.spectrum import Spectrum

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["THIS_DIR"] = THIS_DIR

# setup logger
# this must happen at the very beginning of the module
setup_logger()

# initialize reader
config = ConfigParser()
config.read_dict({"reader": {
    "drq catalogue": f"{THIS_DIR}/data/drq_catalogue_plate3655.fits.gz",
    "input directory": f"{THIS_DIR}/data",
}})
for key, value in defaults_dr16_reader.items():
    if key not in config["reader"]:
        config["reader"][key] = str(value)

READER = Dr16Reader(config["reader"])

# read spectra
SPECTRA = READER.read_data()

assert len(READER.catalogue) == 93
assert len(READER.spectra) == 92
assert READER.read_mode == "spplate"
assert len(SPECTRA) == 92
assert all(isinstance(spectrum, Spectrum) for spectrum in SPECTRA)



# reset logger
# this must happen at the very end of the module
reset_logger()

if __name__ == '__main__':
    pass
