""" This module defines the abstract class MergeStacker to compute the stack
using different partial runs"""
import os

from stacking.errors import StackerError
from stacking.stacker import Stacker, accepted_options, required_options
from stacking.stacker import (  # pylint: disable=unused-import
    defaults)
from stacking.stackers.merge_stacker_utils import load_stacks
from stacking.utils import update_accepted_options, update_required_options

accepted_options = update_accepted_options(accepted_options, ["stack list"])
required_options = update_required_options(required_options, ["stack list"])

ASSOCIATED_WRITER = "StandardWriter"


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

    stack_list: list of str
    List of files containing the individual stacks to be merged

    stacks: list of (array of float, array of float)
    Individual stacks to be merged
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
        self.__parse_config(config)

        self.stacks = load_stacks(self.stack_list)

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
