#!/usr/bin/env python

import glob
import git

from setuptools import find_namespace_packages, setup
from pathlib import Path

scripts = sorted(glob.glob('bin/*py'))

description = (f"Package for stacking spectra\n"
               f"commit hash: {git.Repo('.').head.object.hexsha}")
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

exec(open('stacking/_version.py').read())
version = __version__

setup(name="stacking",
    version = version,
    description = description,
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = "https://github.com/iprafols/stacking",
    author = "Ignasi Pérez-Ràfols",
    author_email = "iprafols@gmail.com",
    package_dir = {'': '.'},
    install_requires = ["numpy", "numba", "pandas", "astropy", "fitsio"],
    scripts = scripts
    )
