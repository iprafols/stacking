"""This module define several functions and variables used throughout the
package"""
import importlib
import re

from stacking.errors import StackingError


def attribute_from_string(attribute_name, module_name):
    """Return an attribute from a module.

    Arguments
    ---------
    atrtibute_name: str
    Name of the attribute to load

    module_name: str
    Name of the module containing the attribute

    Return
    ------
    attribute: object
    The loaded attribute

    Raise
    -----
    ImportError if module cannot be loaded
    AttributeError if atrtibute cannot be found
    """
    # load module
    module_object = importlib.import_module(module_name)
    # get the atrtibute
    atrtibute = getattr(module_object, attribute_name)

    return atrtibute


def class_from_string(class_name, modules_folder):
    """Return a class from a string.

    The class must be saved in a module
    using the standard notation: module name must be the same name as the class but
    lowercase and with and underscore.

    For example class 'MyClass' should be in module {modules_folder}.my_class

    Arguments
    ---------
    class_name: str
    Name of the class to load

    modules_folder: str
    Default folder to search for modules when module_name is None

    Return
    ------
    class_object: Class
    The loaded class

    deafult_args: dict
    A dictionary with the default options (empty for no default options)

    accepted_options: list str
    A list with the names of the accepted options

    required_options: list of str
    A list with the names of the required options

    Raise
    -----
    ImportError if module cannot be loaded
    AttributeError if class cannot be found
    """
    module_name = re.sub('(?<!^)(?=[A-Z])', '_', class_name).lower()
    module_name = f"stacking.{modules_folder}.{module_name.lower()}"

    # load module
    module_object = importlib.import_module(module_name)
    # get the class
    class_object = getattr(module_object, class_name)
    # get the dictionary with the default arguments
    try:
        default_args = getattr(module_object, "defaults")
    except AttributeError:
        default_args = {}
    # get the list with the valid options
    try:
        accepted_options = getattr(module_object, "accepted_options")
    except AttributeError:
        accepted_options = []
    # get the list with the required options
    try:
        required_options = getattr(module_object, "required_options")
    except AttributeError:
        required_options = []
    return class_object, default_args, accepted_options, required_options


def update_accepted_options(accepted_options, new_options, remove=False):
    """Update the content of the list of accepted options

    Arguments
    ---------
    accepted_options: list of string
    The current accepted options

    new_options: list of string
    The new options

    remove: bool - Default: False
    If True, then remove the elements of new_options from accepted_options.
    If False, then add new_options to accepted_options

    Return
    ------
    accepted_options: list of string
    The updated accepted options
    """
    if remove:
        accepted_options = accepted_options.copy()
        for item in new_options:
            if item in accepted_options:
                accepted_options.remove(item)
    else:
        accepted_options = sorted(list(set(accepted_options + new_options)))

    return accepted_options


def update_default_options(default_options, new_options, force_overwrite=False):
    """Update the content of the list of accepted options

    Arguments
    ---------
    default_options: dict
    The current default options

    new_options: dict
    The new options

    force_overwrite: bool - default: False
    If different values for a specific key are given the code raises an error
    complaining about conflicting default values. If `force_overwrite` is True,
    keep the value from new_options instead. This should be used with caution
    and only to overwrite default values from parent classes.

    Return
    ------
    default_options: dict
    The updated default options
    """
    default_options = default_options.copy()
    for key, value in new_options.items():
        if key in default_options:
            default_value = default_options.get(key)
            if type(default_value) is not type(value):
                raise StackingError(
                    f"Incompatible defaults are being added. Key {key} "
                    "found to have values with different type: "
                    f"{type(default_value)} and {type(value)}. "
                    "Revise your recent changes or contact stacking developpers."
                )
            if default_value != value and not force_overwrite:
                raise StackingError(
                    f"Incompatible defaults are being added. Key {key} "
                    f"found to have two default values: '{value}' and '{default_value}' "
                    "Please revise your recent changes. If you really want to "
                    "overwrite the default values of a parent class, then pass "
                    "`force_overload=True`. If you are unsure what this message "
                    "means contact stacking developpers.")
        else:
            default_options[key] = value

    return default_options
