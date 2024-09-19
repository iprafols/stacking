"""Set of functions to automatically display current options in the configuration tutorial"""
import inspect
import glob
import os

from IPython.display import Markdown, display

from stacking.config import accepted_general_options, default_config
from stacking.utils import attribute_from_string, class_from_string

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def file_name_to_class_name(file_name):
    """Get the expected class name from a given file name
    
    Arguments
    ---------
    file_name : str
    The name of the file

    Return
    ------
    class_name : str
    The expected class name
    """
    # Remove the file extension
    base_name = file_name.split("/")[-1].split(".")[0]
    # Split by underscores and capitalize each part
    class_name_parts = [part.capitalize() for part in base_name.split("_")]
    # Join the parts to form the class name
    class_name = "".join(class_name_parts)
    return class_name


def printmd(string):
    """Print a string in Markdown format
    
    Arguments
    ---------
    string : str
    The string to be printed
    """
    display(Markdown(string))


def print_general_options():
    """Collect the general options and print them in a nice Markdown-formatted text"""
    defaults = default_config.get("general")
    for option, description in accepted_general_options.items():
        print_string = f"`{option}`: {description}"
        if option in defaults:
            print_string += f", **Required: no**, **Default: {defaults.get(option)}**"
        else:
            print_string += ", **Required: yes**"
        printmd(print_string)


def print_class_description(class_name, folder):
    """Collect the description of a given class and print it in a nice Markdown-formatted text
    
    Arguments
    ---------
    class_name : str
    The name of the class to be printed

    folder : str
    The folder where the class file is located
    """
    try:
        class_object, _, _, _ = class_from_string(class_name, folder)
    except (AttributeError, ModuleNotFoundError):
        print(
            f"Class '{class_name}' not found. Check that you spelled the class name correctly."
        )
        return

    for item in inspect.getmro(class_object):
        if item.__name__ == "object":
            continue
        printmd(f"### Class {item.__name__}")
        print(item.__doc__)


def print_class_options(class_name, folder):
    """Collect the options of a given class and print them in a nice Markdown-formatted text
    
    Arguments
    ---------
    class_name : str
    The name of the class to be printed

    folder : str
    The folder where the class file is located
    """
    try:
        _, default_args, accepted_options, required_options = class_from_string(
            class_name, folder)
    except (AttributeError, ModuleNotFoundError):
        print(
            f"Class '{class_name}' not found. Check that you spelled the class name correctly."
        )
        return

    printmd(f"### Class {class_name}")
    printmd("#### Options:")
    for option, description in accepted_options.items():
        print_string = f"`{option}`: {description}"
        if option in default_args:
            print_string += f", **Required: no**, **Default: {default_args.get(option)}**"
        elif option in required_options:
            print_string += ", **Required: yes**"
        else:
            print_string += ", **Required: no**"
        printmd(print_string)


def print_classes(folder):
    """Get the current list of available classes and print it
    
    Arguments
    ---------
    folder : str
    The folder where the classes are located
    """
    files = glob.glob(f"{THIS_DIR}/{folder}/*py")
    class_names = [file_name_to_class_name(file) for file in files]
    for class_name in class_names:
        try:
            class_from_string(class_name, folder)
        except (AttributeError, ModuleNotFoundError):
            continue
        # TODO: remove abstact classes
        print(class_name)


def print_selected_writer(stacker_name):
    """Print the writer associated with a given stacker
    
    Arguments
    ---------
    stacker_name : str
    The name of the stacker
    """
    try:
        class_object, _, _, _ = class_from_string(stacker_name, "stackers")
    except (AttributeError, ModuleNotFoundError):
        print(
            f"Class '{stacker_name}' not found. Check that you spelled the class name correctly."
        )
        return

    associated_writer = attribute_from_string("ASSOCIATED_WRITER",
                                              class_object.__module__)
    print(associated_writer)
