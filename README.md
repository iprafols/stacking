# stacking
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
If you are a developer, or want the most recent version of stacking, you can download and install manually:
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

If you are at working at NERSC, we recommend to keep everything clean by adding a function like this in your bashrc:
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
This is cleaner than directly adding the commands to the bashrc file, and avoids potential issues with the transition to Perlmutter.


## For Developers
Before submitting a PR please make sure to:
1. Check the tutorials. Update them if necessary (typically the tutorial `configuration_tutorial.ipynb` will need to be updated.
2. For every file you have modified run
   ```
   yapf --style google file.py -i
   ```
   to ensure the coding styles are maintained.
3. Consider using pylint to help in the debug process. From the repo folder run
   ```
   pylint stacking bin
   ```
   or run the script `pylint_check.sh` under `dev_tools` from the root directory:
   ```
   ./dev_tools/pylint_check.sh
   ```
4. Consider running tests locally before pushing to the repo. From the repo folder run
   ```
   pytest
   ```
