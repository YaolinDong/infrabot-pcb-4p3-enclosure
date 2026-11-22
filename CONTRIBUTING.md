# Contributing

For fit issues, give the edition (S8 or C3), part filename, board revision, printer and material. Report measured dimensions in millimetres, where contact occurs, the mating component and print orientation. A photograph of the interference helps distinguish a shell dimension from a stack-height difference.

Make changes in the edition’s parameter and generator files. Rebuild the edition in a separate checkout, review interference reports and compare parts and assembly views. Select the intended release assets in `tools/public_manifest.txt`, regenerate the index with `python3 -B tools/catalog_models.py`, then run the checks in the [build guide](docs/build.md). Keep published baselines with their hashes and record any physical fit tests separately from CAD checks.
