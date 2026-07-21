# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright (c) 2026 gustebeast
# Source location: https://github.com/gustebeast/cat-nip-ball
"""Catnip ball — all shared constants (one source of truth).

A hollow sphere split at the equator into two screw-together halves. The thread
is INTERNAL and hidden, so the outside stays a perfect sphere; the two equator
rims butt at z=0, which is the hard stop and closes the sphere flush.

Threads come from ``cadkit.threads`` (self-supporting 45° trapezoidal) — we CALL
the library, never re-model a helix. See cadkit/THREADS_README.md.

Joint layout, bottom (male) half, from the equator up:
  z 0 .. COLLAR_H          smooth collar at COLLAR_R (widest part of the skirt)
  COLLAR_H .. THREAD_Z0    45° chamfer in to the thread crest (hidden, self-supporting)
  THREAD_Z0 .. THREAD_Z1   the thread (whole turns)

The collar is what keeps the equator overhang small. The skirt has to be
narrower than the sphere so it can hide inside the socket, and that step is the
one flat ring the bottom half must print over. Putting a full-width collar at
the equator makes that ring only WALL + clearance wide (EQUATOR_OVERHANG); the
45° chamfer then steps in to the necessarily narrower thread without adding a
second overhang.

Printing (both halves dome-up, no supports): top prints on its flat equator rim,
bottom prints skirt-down. Tuned for 3DFuel PCTG on a Bambu X2D (0.4 mm nozzle).

Derived values are intentionally NOT annotated with their numbers in comments —
they drift. Run ``py -3.12 -m src.dimensions`` to print the resolved table.
"""
from math import sqrt


def sphere_r(z):
    """Outer-sphere radius at height z."""
    return sqrt(R_OUT**2 - z**2)


# ── Sphere shell ─────────────────────────────────────────────────────────────
SPHERE_OD   = 30.0            # outer diameter
R_OUT       = SPHERE_OD / 2
WALL        = 1.4             # shell + socket wall (≈3.5 perimeters at a 0.4 nozzle)
R_IN        = R_OUT - WALL    # inner cavity radius (concentric dome)

# ── Thread (cadkit.threads: self-supporting 45°, single-start) ───────────────
# NOMINAL sizes are the female: the cutter is used at nominal and the male is
# shrunk by THREAD_CLR_D, so tuning the fit only ever reprints the bottom half.
# Library limits: the 45° valley (flat + 2·depth) must stay narrower than the
# pitch, and the length must be a whole number of turns. cadkit.threads raises
# if either is violated, so a bad tweak fails loudly at build time.
PITCH          = 2.5          # coarse, so the valley stays well inside the pitch
THREAD_MAJOR_D = 20.4         # nominal crest Ø (= the female bore at the crest)
THREAD_MINOR_D = 19.2         # nominal root Ø
THREAD_CLR_D   = 0.6          # diametral clearance, taken off the MALE (0.3/side)
THREAD_TURNS   = 2
THREAD_LENGTH  = PITCH * THREAD_TURNS

MALE_MAJOR_D = THREAD_MAJOR_D - THREAD_CLR_D
MALE_MINOR_D = THREAD_MINOR_D - THREAD_CLR_D
THREAD_DEPTH = (THREAD_MAJOR_D - THREAD_MINOR_D) / 2

# ── Joint layout ─────────────────────────────────────────────────────────────
COLLAR_R    = R_OUT - WALL - THREAD_CLR_D / 2   # widest skirt radius
COLLAR_H    = 0.8            # collar height; also lifts the thread off the rim
_CHAMFER    = COLLAR_R - MALE_MAJOR_D / 2       # 45°, so Δz == Δr
THREAD_Z0   = COLLAR_H + _CHAMFER
THREAD_Z1   = THREAD_Z0 + THREAD_LENGTH
H_OVERLAP   = THREAD_Z1                          # skirt top = thread top

# The female socket is a SOLID plug across the thread band that the threaded_rod
# cutter drills out. It must NOT be pre-bored: a helix cutter overlapping an
# already-cut void silently no-ops (THREADS_README rule 4). Above the plug the
# cavity resumes, so the drilled bore opens straight into the catnip space.
PLUG_TOP_R  = sqrt(R_IN**2 - THREAD_Z1**2)      # cavity radius where the plug ends

# ── Catnip bore + cavity transition ──────────────────────────────────────────
# The bore only needs to be narrow where it runs through the threaded skirt
# (z 0..H_OVERLAP). Below the equator it opens out to the full R_IN cavity, or
# the dome would be several mm of solid plastic instead of a WALL-thick shell.
# The opening is a 45° cone (dz == dr) so it stays self-supporting when the
# bottom half prints skirt-down, and it lands exactly on the cavity sphere.
BORE_R      = MALE_MINOR_D / 2 - WALL       # leaves WALL behind the thread root
_FLARE      = (-BORE_R + sqrt(2 * R_IN**2 - BORE_R**2)) / 2   # 45° leg
CAVITY_R    = BORE_R + _FLARE               # where the flare meets the cavity dome
CAVITY_Z    = -_FLARE

# ── Air holes ────────────────────────────────────────────────────────────────
HOLE_D      = 3.0
N_RING      = 6              # holes per latitude ring
RING_THETA  = 55.0           # degrees from the pole for each ring

# ── Assembly viz ─────────────────────────────────────────────────────────────
EXPLODE_Z   = 24.0           # top-half float height in the exploded assembly.step

# ── Invariants — a bad tweak should fail here, not on the printer ────────────
EQUATOR_OVERHANG = R_OUT - COLLAR_R   # flat ring the bottom half prints over

assert THREAD_DEPTH < PITCH / 2, "45° thread needs depth < pitch/2"
assert 0 < BORE_R < MALE_MINOR_D / 2, "bore must leave wall behind the thread root"
assert sphere_r(THREAD_Z1) - THREAD_MAJOR_D / 2 >= WALL, "socket would breach the shell"
assert PLUG_TOP_R > THREAD_MAJOR_D / 2 - 0.3, "drilled bore must open into the cavity"
assert COLLAR_R + THREAD_CLR_D / 2 < sphere_r(COLLAR_H), "collar must fit inside the shell"


if __name__ == "__main__":
    print(f"sphere            dia {SPHERE_OD:.1f} mm, wall {WALL:.1f} mm")
    print(f"thread (nominal)  dia {THREAD_MAJOR_D:.1f}/{THREAD_MINOR_D:.1f}"
          f"  pitch {PITCH:.1f}  depth {THREAD_DEPTH:.1f}  {THREAD_TURNS} turns")
    print(f"thread (male)     dia {MALE_MAJOR_D:.1f}/{MALE_MINOR_D:.1f}"
          f"  clearance {THREAD_CLR_D:.1f} diametral ({THREAD_CLR_D/2:.2f}/side)")
    print(f"joint             collar dia {COLLAR_R*2:.1f} to z{COLLAR_H:.1f}, "
          f"chamfer to z{THREAD_Z0:.1f}, thread z{THREAD_Z0:.1f}-{THREAD_Z1:.1f}")
    print(f"catnip opening    dia {BORE_R*2:.1f} mm")
    print(f"equator overhang  {EQUATOR_OVERHANG:.2f} mm (the only unsupported ring)")
    print(f"socket wall       {sphere_r(THREAD_Z1) - THREAD_MAJOR_D/2:.2f} mm at its thinnest")
