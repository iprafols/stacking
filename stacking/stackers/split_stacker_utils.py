"""This module define utility functions for class SplitStacker"""
import re

import numpy as np
from numba import njit

VALID_SPLIT_TYPES = [
    # the split will be performed independently in the different variables,
    # thus, a spectrum can enter multiple splits
    "OR",
    # the split will be performed using all the different variables,
    # thus, a spectrum can enter only one splits
    "AND"
]


def assign_group_multiple_cuts(row, variables, intervals, num_intervals):
    """Assign a group number based on the value stored in row[variable]

    Arguments
    ---------
    row: pd.Series
    A dataframe row

    variables: list of str
    Name of the variables where cuts are applied

    intervals: list of array of float
    Specified intervals for each variable.
    Intervals are defined as [intervals[n], intervals[n-1]].
    The lower (upper) limit of the interval is included in(excluded of) the interval
    Values outside these intervals will be assinged a -1

    num_intervals: array of int
    Number of intervals for each variable

    Return
    ------
    group_number: int
    The group number. -1 for no group
    """
    variable_indexs = []

    for variable, intervals_variable in zip(variables, intervals):
        variable_index = find_interval_index(row[variable], intervals_variable)
        if variable_index == -1:
            return -1
        variable_indexs.append(variable_index)

    group_number = np.sum([
        variable_index * np.prod(num_intervals[:index])
        for index, variable_index in enumerate(variable_indexs)
    ])

    return group_number


def assign_group_one_cut(row, variable, intervals, offset):
    """Assign a group number based on the value stored in row[variable]

    Arguments
    ---------
    row: pd.Series
    A dataframe row

    variable: str
    Name of the variable where cuts are applied

    intervals: array of float
    Specified intervals. Intervals are defined as [intervals[n], intervals[n-1]]. The
    lower (upper) limit of the interval is included in(excluded of) the interval
    Values outside these intervals will be assinged a -1

    offset: int
    Offset to add to the group number. Must be positive

    Return
    ------
    group_number: int
    The group number. -1 for no group
    """
    index = find_interval_index(row[variable], intervals)
    if index == -1:
        return -1
    return index + offset


@njit
def find_interval_index(value, intervals):
    """Given a set of cuts and a number, find in which interval is the number
    found

    Arguments
    ---------
    value: float
    The value to check

    intervals: array of float
    Specified intervals. Intervals are defined as [intervals[n], intervals[n-1]]. The
    lower (upper) limit of the interval is included in (excluded of) the interval
    Values outside these intervals will be assinged a -1

    Return
    ------
    interva_index: int
    The interval index. -1 if outside the bounds
    """
    if value < intervals[0]:
        return -1

    for index, (min_value,
                max_value) in enumerate(zip(intervals[:-1], intervals[1:])):
        if min_value <= value < max_value:
            return index

    return -1


def extract_split_cut_sets(split_cuts):
    """Format the split_on variable (list of column names to be split)

    Arguments
    ---------
    split_on: str
    The string to format

    Return
    ------
    split_cuts_sets: list of str
    Each item in the list contain the set of splits in a given variable
    """
    return re.split(r"[ \t]*;[ \t]*", split_cuts)


def format_split_on(split_on):
    """Format the split_on variable (list of column names to be split)

    Arguments
    ---------
    split_on: str
    The string to format

    Return
    ------
    formatted_split_on: list of str
    A list of uppercase column names
    """
    return [item.upper() for item in re.split(r"[, ;]+", split_on)]


def format_splits(split_cuts_sets):
    """Format the splits variable (list of intervals to perform the splits.)

    Arguments
    ---------
    split_cuts_sets: list of str
    Each item in the list contain the set of splits in a given variable

    Return
    ------
    splits: list of array of float
    List of intervals to perform the splits. Each array is derived from an item
    from the variable split_on.
    Intervals are defined as [intervals[n], intervals[n-1]].
    The lower (upper) limit of the interval is included in(excluded of) the interval
    Values outside these intervals will be assinged a -1
    """
    splits = [
        np.array([
            float(re.sub(r"[\[\]]*", "", cut))
            for cut in re.split(r"[ \t]*[, ]+[ \t]*", item)
        ],
                 dtype=float)
        for item in split_cuts_sets
    ]
    return splits


@njit
def retreive_group_number(specid, specid_list, groups_list):
    """Retreive the groups a specid belongs to

    Arguments
    ---------
    specid: int
    The specid

    specid_list: array of int
    The list of specids in the catalogue

    groups_list: array of int
    The group number associated to each specid

    Return
    ------
    group_number: int
    The group number associated with the specified specid
    """
    pos = np.where(specid_list == specid)

    return groups_list[pos]
