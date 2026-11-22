# Rebuild and check an enclosure

The downloadable STL and STEP files are ready to use. Rebuild in a separate checkout: the generators replace CAD exports and previews in their edition directory.

## Check a downloaded release

Use Python 3.11 or later. Both commands require only the standard library.

```sh
python3 -B tools/verify.py
python3 -B -m unittest discover -s tests -v
```

The release check for maintainers is described in [CONTRIBUTING](../CONTRIBUTING.md).

## CAD environment

Tested on Linux with Python 3.12, CadQuery 2.8.0, cadquery-ocp 7.9.3.1.1, NumPy 2.5.4, Pillow 13.0.0, Numba 0.68.1, SciPy 1.18.1 and ezdxf 1.4.5. Both editions have the same requirements. The gallery uses DejaVu Sans and Noto Sans CJK. C3 also uses the distribution’s Python GI, librsvg and Cairo for the dimension sheet. Install the following Ubuntu system packages and use a Python 3.12 interpreter with venv support.

```sh
sudo apt-get install python3-venv python3-gi python3-gi-cairo python3-cairo gir1.2-rsvg-2.0 fonts-dejavu-core fonts-noto-cjk libgl1
python3.12 -m venv .venv
.venv/bin/python -m pip install -r simple/source/requirements.txt
.venv/bin/python -B tools/build.py simple --allow-missing-external
.venv/bin/python -B tools/build.py deluxe --allow-missing-external
```

An existing environment with the same dependencies can run both build commands using its Python. The build writes `.work/build.log`, `fit-check.json` and `verification.json` under the selected edition. S8 restores the 13 hash-checked STEP inputs in `simple/reference/` and writes a comparison with its S7 baseline. Further previews are generated locally. Physical fit requires measurements of an assembled unit.

## External measurements

`--allow-missing-external` allows the geometry and rendering checks to run while named, unprovided measurement sources are reported as missing. All distributed references and every supplied source must pass their checks. For a complete original-input audit, set `ENCLOSURE_SOURCE_MAP` to an external JSON object mapping source keys from `parameters.json` to original files. Relative filenames resolve next to that map. The optional `PCB_WORKSPACE` names a checkout of the published R8 board; it verifies the separately recorded public reference hashes. Its sanitized PCB export cannot satisfy the original native PCB hash.

With all original sources supplied, omit `--allow-missing-external`. Add `--package` to produce an edition ZIP with checked assets and reports. Use `--check-only` to repeat geometry verification after a build. To compare two model trees (all 13 meshes), run `python3 -B tools/compare_meshes.py ORIGINAL_CHECKOUT REBUILT_CHECKOUT`. The release index verifies the original download bytes; newly generated STEP headers or triangle ordering can differ.
