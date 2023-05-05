#!/usr/bin/env python3
"""Compute the stack of a set of spectra"""
import logging
import time
import argparse

from stacking.stacking_interface import StackingInterface

module_logger = logging.getLogger("picca.delta_extraction")


def main(args):
    """Compute the stack of a set of spectra"""
    start_time = time.time()

    # intitialize StackingInterface instance
    interface = StackingInterface()

    # load configuration
    interface.load_config(args.config_file)

    # read data
    interface.read_data()

    # normalize spectra
    interface.normalize_spectra()

    # stack spectra
    interface.stack_spectra()

    # save results
    interface.write_results()

    end_time = time.time()
    module_logger.info("Total time elapsed: %f seconds", end_time - start_time)
    module_logger.info("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Compute the stack of a set of spectra")

    parser.add_argument(
        'config_file',
        type=str,
        default=None,
        help=('Configuration file. To learn about all the available options '
              'check the configuration tutorial in '
              'tutorials/configuration_tutorial.ipynb'))

    main(parser.parse_args())
