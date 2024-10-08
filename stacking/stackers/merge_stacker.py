""" This module defines the abstract class MergeStacker to compute the stack
using different partial runs"""
import os

from stacking.errors import StackerError
from stacking.stacker import Stacker, accepted_options, defaults, required_options
from stacking.stackers.merge_stacker_utils import load_stacks
from stacking.utils import (update_accepted_options, update_default_options,
                            update_required_options)

accepted_options = update_accepted_options(
    accepted_options,
    {
        # option: description
        "hdu name": (
            "Name of the HDU to containing the spectra to load. Should be a valid "
            "HDU in each of the files in stack_list. **Type: str**"),
        "stack list":
            "List of files containing the individual stacks to be merged. **Type: str**",
    })
defaults = update_default_options(defaults, {
    "hdu name": "STACK",
})
required_options = update_required_options(required_options, ["stack list"])


class MergeStacker(Stacker):
    """Abstract class to compute the satck using different partial runs

    Methods
    -------
    (see Stacker in stacking/stacker.py)
    __init__
    __parse_config

    Attributes
    ----------
    (see Stacker in stacking/stacker.py)

    hdu_name: str
    Name of the HDU to containing the spectra to load. Should be a valid HDU in each of 
    the files in stack_list

    stack_list: list of str
    List of files containing the individual stacks to be merged

    stacks: list of (array of float, array of float)
    Individual stacks to be merged. Each item contains a tuple with the flux
    and weight arrays
    """

    def __init__(self, config):
        """Initialize class instance

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        StackerError if the selected reading mode is not supported
        """
        super().__init__(config)

        self.stack_list = None
        self.hdu_name = None
        self.__parse_config(config)

        self.stacks = load_stacks(self.stack_list, hdu_name=self.hdu_name)

    def __parse_config(self, config):
        """Parse the configuration options

        Arguments
        ---------
        config: configparser.SectionProxy
        Parsed options to initialize class

        Raise
        -----
        StackerError upon missing required variables
        StackerError if the stacking files are missing
        StackerError if the stacking files are not fits files
        """
        self.hdu_name = config.get("hdu name")
        if self.hdu_name is None:
            raise StackerError("Missing argument 'hdu name' required by "
                               "MergeStacker")

        stack_list = config.get("stack list")
        if stack_list is None:
            raise StackerError("Missing argument 'stack list' required by "
                               "MergeStacker")
        self.stack_list = stack_list.split()
        for stack_file in self.stack_list:
            if not os.path.exists(stack_file):
                raise StackerError(
                    f"Could not find file '{stack_file}' required by "
                    "MergeStacker")
            if not (stack_file.endswith(".fits") or
                    stack_file.endswith(".fits.gz")):
                raise StackerError(
                    f"MergeStacker: Expected a fits file, found {stack_file}")
