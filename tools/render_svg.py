#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""Render generated dimension sheets using system librsvg/cairo."""
import sys,gi,cairo
from pathlib import Path
gi.require_version('Rsvg','2.0')
from gi.repository import Rsvg
for arg in sys.argv[1:]:
    p=Path(arg);h=Rsvg.Handle.new_from_file(str(p));dim=h.get_dimensions();s=cairo.ImageSurface(cairo.FORMAT_ARGB32,dim.width,dim.height);h.render_cairo(cairo.Context(s));s.write_to_png(str(p.with_suffix('.png')))
