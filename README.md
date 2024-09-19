# stacking
![Python Package](https://github.com/iprafols/stacking/actions/workflows/pytest.yml/badge.svg?branch=main)
[![Coverage Status](https://coveralls.io/repos/github/iprafols/stacking/badge.svg?branch=main)](https://coveralls.io/github/iprafols/stacking?branch=main)
![Pylint](https://github.com/iprafols/stacking/actions/workflows/pylint.yml/badge.svg?branch=main)

Package to perform spectral stacking

## Installation
It is recommended to use a clean environment:
```
conda create -n my_stacking_env python==version
conda activate my_stacking_env
```
If you already have an environment, you just need to activate it.
After you have the environment, you can install stacking with:
```
pip install stacking
```
If you are a developer or want the most recent version of stacking, you can download and install it manually:
```
git clone https://github.com/iprafols/stacking.git
cd stacking
pip install -e .
```
Optionally, you can add the path to stacking to your bashrc:
```
export STACKING_BASE=<path to your stacking repo>
```
Or you can add `stacking/` to your `PYTHONPATH`. Both of these are optional and stacking will work without them.

If you are working at NERSC, we recommend keeping everything clean by adding a function like this in your bashrc:
```
stacking_env () {
    module load python
    conda activate my_stacking_env
}
```
Whenever you need stacking just write:
```
stacking_env
```
This is cleaner than directly adding the commands to the bashrc file and avoids potential issues with the transition to Perlmutter.


## For Developers
Before submitting a PR please make sure to:
1. Consider running the development tools locally before pushing to the repo. These include yapf formatting and linting checks:
    ```
    ./dev_tools/yapf_formatting.sh
    ./dev_tools/pylint_check.sh
    ```
3. Consider running tests locally before pushing to the repo. From the repo folder run
   ```
   pytest
   ```
