""" This module defines the class MeanStacker to compute the stack
using the mean of the stacked values"""
import logging

from astropy.table import Table
import numpy as np
import pandas as pd

from stacking.errors import StackerError
from stacking.spectrum import Spectrum
from stacking.stacker import Stacker
from stacking.stacker import (  # pylint: disable=unused-import
    defaults, accepted_options, required_options)
from stacking.stackers.split_stacker_utils import (
    assign_group_multiple_cuts,
    assign_group_one_cut,
    extract_split_cut_sets,
    format_split_on,
    format_splits,
    retreive_group_number,
)

VALID_SPLIT_TYPES = [
    # the split will be performed independently in the different variables,
    # thus, a spectrum can enter multiple splits
    "OR",
    # the split will be performed using all the different variables,
    # thus, a spectrum can enter only one splits
    "AND"
]


class SplitStacker(Stacker):
    """Abstract class to compute mulitple stacks splitting on one
    or more properties of the spectra.

    Methods
    -------
    (see Stacker in stacking/stacker.py)
    __init__
    __parse_config
    assing_groups
    read_catalogue
    stack

    Attributes
    ----------
    (see Stacker in stacking/stacker.py)

    logger: logging.Logger
    Logger object

    num_groups: int
    Number of groups the data is split on

    specid_name: str
    Name of the column containing the identifier SPECID

    split_catalogue: pd.DataFrame
    The catalogue to be split

    split_catalogue_name: str
    Filename of the catalogue to be split

    split_on: list of str
    List of column name(s) to be split

    split_type: "OR" or "AND"
    If "OR", then the split will be performed independently in the different
    variables (a spectrum can enter multiple splits). If "AND", the split will
    be performed using all the different variables (a spectrum can enter at most
    one split)

    splits: list of array of float
    List of intervals to perform the splits.
    Intervals are defined as [intervals[n], intervals[n-1]].
    The lower (upper) limit of the interval is included in(excluded of) the interval
    Values outside these intervals will be assinged a -1

    stackers: list of Stacker
    Stacker instances that will contain the stacked spectra for each of the groups
    Must be initialized by the child class
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

        self.specid_name = None
        self.split_catalogue_name = None
        self.split_on = None
        self.split_type = None
        self.splits = []
        self.__parse_config(config)

        # read the catalogue
        self.split_catalogue = self.read_catalogue()

        # add groups
        self.num_groups = None
        self.assing_groups()

        # This needs to be defined in the child class
        self.stackers = []

    def __parse_config(self, config):
        """Parse the configuration options

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        StackerError upon missing required variables
        StackerError if variables are not properly formatted
        StackerError if variables are not coherent
        """
        self.specid_name = config.get("specid name")
        if self.specid_name is None:
            raise StackerError("Missing argument 'specid name' required by "
                               "SplitStacker")

        self.split_catalogue_name = config.get("split catalogue name")
        if self.split_catalogue_name is None:
            raise StackerError(
                "Missing argument 'split catalogue name' required by "
                "SplitStacker")

        split_on = config.get("split on")
        if split_on is None:
            raise StackerError("Missing argument 'split on' required by "
                               "SplitStacker")
        # use any of the following as separators (comma semicolon space)
        self.split_on = format_split_on(split_on)

        self.split_type = config.get("split type")
        if self.split_type is None:
            raise StackerError("Missing argument 'split type' required by "
                               "SplitStacker")
        self.split_type = self.split_type.upper()
        if self.split_type not in VALID_SPLIT_TYPES:
            raise StackerError(
                "Invalid value for argument 'split on' required by SplitStacker. "
                "Expected one of '" + " ".join(VALID_SPLIT_TYPES) +
                f" Found: '{self.split_type}'")

        split_cuts = config.get("split cuts")
        if split_cuts is None:
            raise StackerError("Missing argument 'split cuts' required by "
                               "SplitStacker")
        # the splitting on the different quantities is done using ; plus
        # possibly spaces
        split_cuts_sets = extract_split_cut_sets(split_cuts)
        if len(split_cuts_sets) != len(self.split_on):
            raise StackerError(
                "Inconsistency found in reading the splits. The number of "
                f"splitting variables is {len(self.split_on)}, but I found "
                f"{len(split_cuts_sets)} sets of cuts. Read vaues are\n"
                f"'split on' = '{self.split_on}'\n'split cuts' = '{split_cuts}'. "
                "Splitting variables are delimited by a semicolon (;), a comma"
                "(,) or a white space. Cuts sets should be delimited by the "
                "character ';'. Cut values within a given set should be delimited "
                "by commas and/or whitespaces)")
        self.splits = format_splits(split_cuts_sets)

    def assing_groups(self):
        """Assign groups to the catalogue entries. Store the total number of groups

        If split_type is OR-like, then assign one group number per varible in
        the split. Else, it split_type is AND-like, then assing a single group
        number
        """
        self.num_groups = 0
        if self.split_type == "OR":
            groups = []
            for index, variable in enumerate(self.split_on):
                self.split_catalogue[
                    f"GROUP_{index}"] = self.split_catalogue.apply(
                        assign_group_one_cut,
                        axis=1,
                        args=(variable, self.splits[index], self.num_groups),
                    )
                # keep grouping info
                groups += [[
                    variable, min_value, max_value, f"GROUP_{index}",
                    group_index + self.num_groups
                ] for group_index, (min_value, max_value) in enumerate(
                    zip(self.splits[index][:-1], self.splits[index][1:]))]
                # update num_groups
                self.num_groups += self.splits[index].size - 1

            self.groups_info = pd.DataFrame(data=groups,
                                            columns=[
                                                "VARIABLE", "MIN_VALUE",
                                                "MAX_VALUE", "COLNAME",
                                                "GROUP_NUM"
                                            ])
        elif self.split_type == "AND":
            num_intervals = np.array([
                self.splits[index].size - 1
                for index in range(len(self.split_on))
            ])

            self.split_catalogue["GROUP"] = self.split_catalogue.apply(
                assign_group_multiple_cuts,
                axis=1,
                args=(self.split_on, self.splits, num_intervals),
            )

            self.num_groups = np.prod(num_intervals)

            groups = []
            for group_number in range(self.num_groups):
                aux_groups = [group_number]
                for index, num_intervals_variable in enumerate(num_intervals):
                    variable_index = group_number % num_intervals_variable
                    aux_groups += [
                        self.split_on[index],
                        self.splits[index][variable_index],
                        self.splits[index][variable_index + 1]
                    ]
                    group_number = (group_number -
                                    variable_index) // num_intervals_variable
                groups.append(aux_groups)

            # columns of the data frame
            cols = ["GROUP_NUM"]
            for index in range(len(self.split_on)):
                cols += [
                    f"VARIABLE_{index}", f"MIN_VALUE_{index}",
                    f"MAX_VALUE_{index}"
                ]

            self.groups_info = pd.DataFrame(data=groups, columns=cols)

        # this should never enter unless new split types are not properly added
        else:  # pragma: no cover
            raise StackerError(
                f"Don't know what to do with split type {self.split_type}. "
                "This is one of the supported split types, maybe it "
                "was not properly coded. If you did the change yourself, check "
                "that you added the behaviour of the new mode to method `assing_groups`. "
                "Otherwise contact 'stacking' developpers.")

    def read_catalogue(self):
        """Read the catalogue to do the splits

        Return
        -----
        split_catalogue: pd.DataFrame
        The catalogue to be split

        Raise
        -----
        StackerError if file is not found
        """
        self.logger.progress("Reading catalogue from %s",
                             self.split_catalogue_name)
        try:
            catalogue = Table.read(self.split_catalogue_name, hdu="CATALOG")
        except FileNotFoundError as error:
            raise StackerError("SplitStacker: Could not find catalogue: "
                               f"{self.split_catalogue_name}") from error

        keep_columns = self.split_on + [self.specid_name]

        split_catalogue = catalogue[keep_columns].to_pandas()
        split_catalogue.rename(columns={self.specid_name: "specid"},
                               inplace=True)

        return split_catalogue

    def stack(self, spectra):
        """ Stack spectra

        Arguments
        ---------
        spectra: list of Spectrum
        The spectra to stack

        Raise
        -----
        StackerError if the stackers have not been intialized by the child class
        """
        if len(self.stackers) != self.num_groups:
            raise StackerError(
                f"I expected {self.num_groups} stackers but found "
                f"{len(self.stackers)}. Make sure the member 'stackers' is "
                "properly intialized in the child class")

        self.stacked_flux = np.zeros(
            (self.num_groups, Spectrum.common_wavelength_grid.size),
            dtype=float)
        self.stacked_weight = np.zeros_like(self.stacked_flux)

        for group_number, stacker in enumerate(self.stackers):

            # select the spectra of this particular groups
            if self.split_type == "OR":
                col = self.groups_info[self.groups_info["GROUP_NUM"] ==
                                       group_number]["COLNAME"].values[0]
            elif self.split_type == "AND":
                col = "GROUP"

            # this should never enter unless new split types are not properly added
            else:  # pragma: no cover
                raise StackerError(
                    f"Don't know what to do with split type {self.split_type}. "
                    "This is one of the supported split types, maybe it "
                    "was not properly coded. If you did the change yourself, check "
                    "that you added the behaviour of the new mode to method `stack`. "
                    "Otherwise contact 'stacking' developpers.")

            selected_spectra = [
                spectrum for spectrum in spectra if retreive_group_number(
                    spectrum.specid, self.split_catalogue["specid"].values,
                    self.split_catalogue[col].values) == group_number
            ]

            # run the stack
            stacker.stack(selected_spectra)

            self.stacked_flux[group_number] = stacker.stacked_flux
            self.stacked_weight[group_number] = stacker.stacked_weight
