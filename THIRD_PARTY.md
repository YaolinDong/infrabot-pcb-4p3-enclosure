# Sources and tools

The mechanical stack uses dimensions from EmbedFire Challenger V2 and 4.3-inch LCD drawings, LCD panel/assembly drawings, selected switch specifications and measurements of the InfraBot R8 board. Source titles and original SHA-256 values are recorded in each edition’s `parameters.json`. The public R8 board export has its own hash. The vendor drawings, reference board mesh and original measurement files are held separately.

The fit assemblies contain dimensioned envelopes and simplified fasteners made in the edition generators. S8 also places the author’s formed-lead LED2 solid from the R8 project (CERN-OHL-P-2.0). Its restored STEP matches the published file byte for byte. The assemblies contain no vendor or EasyEDA library solids. [Reference inventory](verification/README.md) · [R8 LED2 generator](https://github.com/YaolinDong/infrabot-pcb-4p3/blob/8cc0637cd06d5f09f8d949b2dd739ca1e2a08ede/tools/build_led2_step.py)

## Build-time dependencies

The build uses separately installed tools. Consult their distributions for notices covering bundled components.

| Tool | Use | Upstream license |
|---|---|---|
| CadQuery | Construct solids and assemblies, exchange STEP/STL | Apache-2.0 |
| cadquery-ocp / Open CASCADE Technology | Python bindings / geometric kernel | Apache-2.0 / LGPL-2.1 with OCCT exception |
| NumPy | Mesh and rendering arrays | BSD-3-Clause; distribution also lists 0BSD, MIT, Zlib and CC0-1.0 |
| SciPy | Numerical operations | BSD-3-Clause |
| Numba | Compile rasterization routines | BSD-2-Clause |
| Pillow | Raster images, labels and galleries | MIT-CMU |
| ezdxf | Dimensioned CAD layouts | MIT |
| PyGObject, librsvg, Pycairo, Cairo | System SVG rasterization | LGPL family for PyGObject and librsvg; Pycairo and Cairo offer LGPL/MPL terms |
| DejaVu Sans and Noto Sans CJK | Rasterized labels | Bitstream Vera terms with DejaVu additions; SIL OFL for Noto |

The previews include rendered labels. The repository does not distribute font files, Python distributions, system libraries or vendor source documents.
