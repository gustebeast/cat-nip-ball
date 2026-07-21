# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright (c) 2026 gustebeast
# Source location: https://github.com/gustebeast/cat-nip-ball
"""Catnip ball — main build script.

Run from the repo root:
  py -3.12 -m src.build              # build both halves + assembly
  py -3.12 -m src.build --part NAME  # build only one part
  py -3.12 -m src.build --list       # list available part names

Writes one STEP per printed half (the slicer imports these) plus an exploded,
coloured assembly.step that the shared FreeCAD viewer opens. The assembly
carries a floating 3-D build number.
"""
import argparse
import pathlib
import sys

import cadquery as cq

# Vendored shared toolkit (cadkit subtree) — a plain package import; the build
# always runs via -m from the project root, so no sys.path hack is needed.
from cadkit.cq_colors import color
from cadkit.freecad import show
from cadkit.step_export import export_step

from .parts import build_bottom, build_top
from .dimensions import R_OUT, EXPLODE_Z

# Anchor every output to the project folder, regardless of where the build was
# launched from (see cadkit/AGENTS.md).
OUT = pathlib.Path(__file__).resolve().parent.parent

# ── Phase toggles ────────────────────────────────────────────────────────────
THREADS = True
HOLES   = True

# ── Palette (catnip green top, warm "treat" amber bottom) ────────────────────
COLOR = {
    "catnip_ball_top":    "#6Fae54",   # leaf green
    "catnip_ball_bottom": "#E0973C",   # warm amber
    "build_counter":      "#F0A878",   # salmon accent
}

# NOT heal()ed: never ShapeFix/unify a threaded part (cadkit/THREADS_README.md
# rule 7 — it hangs or crashes on the many-face helix; the raw solid exports and
# slices fine).
bottom = build_bottom(threads=THREADS, holes=HOLES)
top    = build_top(threads=THREADS, holes=HOLES)

# Map of part name → (workplane, output filename, optional note).
PARTS = {
    "catnip_ball_bottom": (bottom, "catnip_ball_bottom.step",
                           "male half - threaded skirt; drop the catnip in here"),
    "catnip_ball_top":    (top,    "catnip_ball_top.step",
                           "female half - threaded socket; screws down onto the bottom"),
}


def _export(name):
    obj, path, note = PARTS[name]
    export_step(obj, str(OUT / path))
    suffix = f"  ({note})" if note else ""
    print(f"Wrote {path}{suffix}")


def collect_components():
    """Placed parts at their as-built (SEATED) positions, for the overlap gate
    (tools/check_overlaps.py). Not the exploded assembly.step layout — the two
    halves are seated so the threaded joint is checked at its real fit."""
    return [("catnip_ball_bottom", bottom), ("catnip_ball_top", top)]


# ── Build counter — a 3-D number floating above the assembly, bumped every
# full build; tools/build_counter.txt is gitignored, starts at 1 if missing.
_COUNTER = pathlib.Path(__file__).resolve().parent.parent / "tools" / "build_counter.txt"


def _bump_build_counter() -> int:
    try:
        n = int(_COUNTER.read_text().strip()) + 1
    except (OSError, ValueError):
        n = 1
    try:
        _COUNTER.parent.mkdir(parents=True, exist_ok=True)
        _COUNTER.write_text(f"{n}\n")
    except OSError:
        pass
    return n


def _build_counter_model(n: int):
    """Upright number floating above the assembly. None if the text engine
    hiccups — a font failure must never break the build."""
    try:
        return cq.Workplane("XZ").center(0, R_OUT + EXPLODE_Z + 14).text(str(n), 8, 2)
    except Exception:
        return None


def _export_assembly():
    build_n = _bump_build_counter()
    assembly = (
        cq.Assembly(name="catnip_ball")
        .add(bottom, name="catnip_ball_bottom", color=color(COLOR["catnip_ball_bottom"]))
        # Top half floated EXPLODE_Z above so the joint/threads are visible.
        .add(top.translate((0, 0, EXPLODE_Z)), name="catnip_ball_top",
             color=color(COLOR["catnip_ball_top"]))
    )
    counter = _build_counter_model(build_n)
    if counter is not None:
        assembly.add(counter, name="build_counter", color=color(COLOR["build_counter"]))
    assembly.save(str(OUT / "assembly.step"), mode="default")
    print(f"Wrote assembly.step  [build #{build_n}]", flush=True)
    show(str(OUT / "assembly.step"))


def main() -> None:
    p = argparse.ArgumentParser(prog="src.build", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--part", help="Build only this part (skips assembly).")
    p.add_argument("--list", action="store_true", help="List part names and exit.")
    args = p.parse_args()

    if args.list:
        print("assembly")
        for name in PARTS:
            print(name)
        return

    if args.part:
        if args.part == "assembly":
            _export_assembly()
            return
        if args.part not in PARTS:
            print(f"unknown part: {args.part!r}. Use --list to see options.", file=sys.stderr)
            sys.exit(2)
        _export(args.part)
        return

    for name in PARTS:
        _export(name)
    _export_assembly()


if __name__ == "__main__":
    main()
