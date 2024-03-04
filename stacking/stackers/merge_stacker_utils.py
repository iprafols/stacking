""" This module defines the abstract class MergeStacker to compute the stack
using different partial runs"""
from astropy.io import fits
from astropy.table import Table
import numpy as np

from stacking.errors import StackerError
from stacking.spectrum import Spectrum


def load_stacks(stack_list):
    """ Load stacks from previous runs

    Arguments
    ---------
    stack_list: list of str
    Fits files containing the stacks. All files should have the same wavelength
    grid

    Return
    ------
    stacks: list of (array of float, array of float)
    List of stacks. Each item contains a tuple with the flux and weight arrays

    Raise
    -----
    StackerError if the wavelength arrays of the different files are not equal
    """
    stacks = []

    for file in stack_list:
        hdul = fits.open(file)

        # disabling pylint no-members as they are false positives here
        wavelength = hdul["STACK"].data["WAVELENGTH"]  # pylint: disable=no-member
        flux = hdul["STACK"].data["STACKED_FLUX"]  # pylint: disable=no-member
        weight = hdul["STACK"].data["STACKED_WEIGHT"]  # pylint: disable=no-member

        hdul.close()

        # check wavelength grid
        if Spectrum.common_wavelength_grid is None:
            Spectrum.set_common_wavelength_grid(wavelength)
        elif Spectrum.common_wavelength_grid.size != wavelength.size:
            raise StackerError(
                "Error loading stacked spectra. Expecting the stacks to have the "
                "same wavelengths, but found wavelength grids of different sizes "
                f"({Spectrum.common_wavelength_grid.size} and {wavelength.size})"
            )
        elif not np.allclose(Spectrum.common_wavelength_grid, wavelength):
            error_message = (
                "Error loading stacked spectra. Expecting the stacks to have the "
                "same wavelengths, but found differnt wavelength grids:\n"
                "wave1 wave2 areclose\n")
            for item1, item2 in zip(Spectrum.common_wavelength_grid,
                                    wavelength):
                error_message += f"{item1} {item2} {np.isclose(item1, item2)}\n"

            raise StackerError(error_message)

        # add to list
        stacks.append((flux, weight))

    return stacks


def load_splits_info(stack_list):
    """ Load split info from previous runs

    Arguments
    ---------
    stack_list: list of str
    Fits files containing the stacks. All files should have the same wavelength
    grid

    Return
    ------
    groups_info: pd.DataFrame
    DataFrame containing the group information

    num_groups: int
    Number of groups the data is split on

    split_catalogue: pd.DataFrame
    The catalogue to be split

    Raise
    -----
    StackerError if
    """
    groups_info = None
    num_groups = None
    split_catalogue = None

    for file in stack_list:
        # read data from file
        groups_info_file = Table.read(file, hdu="GROUPS_INFO").to_pandas()
        split_catalogue_file = Table.read(file,
                                          hdu="METADATA_SPECTRA").to_pandas()
        hdul = fits.open(file)
        # disabling pylint no-members as they are false positives here
        num_groups_file = hdul["GROUPS_INFO"].header["NGROUPS"]  # pylint: disable=no-member
        hdul.close()

        # now check that files are compatible
        if groups_info is None:
            groups_info = groups_info_file
            num_groups = num_groups_file
            split_catalogue = split_catalogue_file
        else:
            if num_groups != num_groups_file:
                raise StackerError(
                    "Error loading splits info. I expected all the files to have "
                    "the same number of groups but found different values: "
                    f"{num_groups} and {num_groups_file}")
            if not groups_info.equals(groups_info_file):
                raise StackerError(
                    "Error loading splits info. I expected all the files to have "
                    "the same splits, but found different configurations. \n"
                    f"Info 1:\n{groups_info.to_string()}\nInfo 2:\n"
                    f"{groups_info_file.to_string()}")
            # All columns except for IN_STACK should be the same
            cols = [col for col in split_catalogue.columns if col != "IN_STACK"]
            if not split_catalogue[cols].equals(split_catalogue_file[cols]):  # pylint: disable=unsubscriptable-object
                raise StackerError(
                    "Error loading splits info. I expected all the files to have "
                    "the same spliting catalogue, but found different configurations. \n"
                    f"Info 1:\n{split_catalogue.to_string()}\nInfo 2:\n"
                    f"{split_catalogue_file.to_string()}")
            # update column IN_STACK
            split_catalogue["IN_STACK"] = split_catalogue[  # pylint: disable=unsubscriptable-object,unsupported-assignment-operation
                "IN_STACK"] | split_catalogue_file["IN_STACK"]

    return groups_info, num_groups, split_catalogue
