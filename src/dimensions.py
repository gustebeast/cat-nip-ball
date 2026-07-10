"""Catnip ball — all shared constants (one source of truth).

A hollow sphere split at the equator into two screw-together halves, with a
hidden, internal, TAPERED (conical) thread so the OUTSIDE stays a perfect
sphere. The taper makes the thread follow the sphere inward, so the socket
wall stays a uniform thickness at any depth (a straight cylindrical socket
thins toward its top as the sphere curves away — that caused an earlier
breach the slicer dropped as "air"). The two equator rims butt at z = 0 — that
is the hard stop and closes the sphere flush.

Printing (both halves dome-up, no supports): top prints on its flat equator
rim; bottom prints skirt-down. The only overhang is a small flat ring at the
bottom's equator (= WALL + clearance wide) where the skirt meets the sphere.

Thread design follows FDM best-practice research (DrLex, BOSL2, CNC Kitchen,
Prusa/Bambu KBs): coarse pitch, ~45° flanks, flats ≥ one extrusion, blunt
thread ends, threads lifted off the bed, ≥3-perimeter wall behind the thread.
Tuned for 3DFuel PCTG on a Bambu X2D (0.4 mm nozzle).
"""
from math import sqrt

# ── Sphere shell ─────────────────────────────────────────────────────────────
SPHERE_OD   = 30.0             # outer diameter (bumped from 25 for room + grip)
R_OUT       = SPHERE_OD / 2    # 15.0
WALL        = 1.4             # shell + socket wall (≈3.5 perimeters at 0.4 nozzle)
R_IN        = R_OUT - WALL    # 13.6 — inner cavity radius (concentric dome)

# ── Tapered thread (single-start, coarse, ~45° flanks) ───────────────────────
# Cones are defined off the outer sphere: at height z the sphere radius is
# sph(z)=√(R_OUT²−z²). Male crest = sph(z) − WALL − CLR; female bore =
# sph(z) − WALL. Both halves' threads ride parallel cones CLR apart.
PITCH       = 3.0             # coarse pitch (research: 2.5–3 mm for printed caps)
THREAD_DEPTH = 0.8           # radial tooth height (engagement = depth − CLR = 0.5)
THREAD_CLR  = 0.3            # radial clearance per side (PCTG on a calibrated X2D)
CREST_FLAT  = 0.5            # flat tip on the female ridge (≥ one extrusion)
GROOVE_FRAC = 0.55          # male groove width / pitch (wider…)
RIDGE_FRAC  = 0.45          # female ridge width / pitch (…so they mesh with play)
THREAD_OVERLAP = 0.2        # how far a cut/ridge digs past its wall (clean boolean)

# Engagement band (threads live here; lifted ≥1 mm off the equator so the
# female threads clear the first-layer elephant's-foot zone). Ends at 6.5 so the
# swept thread + its end-cap tail stay in the thick-wall zone (the sphere
# narrows toward the socket top).
THREAD_Z0   = 1.0
THREAD_Z1   = 6.5            # ~1.8 turns at PITCH 3.0
H_OVERLAP   = 7.0            # skirt height (a bit above the threads)
SOCKET_DEPTH = 7.5           # socket deeper than the skirt → equator rims are the stop

# ── Catnip bore ──────────────────────────────────────────────────────────────
BORE_R      = 9.0            # catnip passage radius (Ø18 opening)
BORE_CAV_Z  = -sqrt(R_IN**2 - BORE_R**2)    # where the bore meets the cavity dome

# ── Air holes ────────────────────────────────────────────────────────────────
HOLE_D      = 3.0
N_RING      = 6             # holes per latitude ring
RING_THETA  = 55.0         # degrees from the pole for each ring

# ── Assembly viz ─────────────────────────────────────────────────────────────
EXPLODE_Z   = 24.0          # top half float height in the exploded assembly.step

# ── Info / invariants ────────────────────────────────────────────────────────
EQUATOR_OVERHANG = WALL + THREAD_CLR          # 1.7 mm flat ring at the bottom equator
_sph = lambda z: sqrt(R_OUT**2 - z**2)

assert WALL > 0 and THREAD_DEPTH > THREAD_CLR, "thread must actually engage"
assert PITCH > CREST_FLAT + 2 * THREAD_DEPTH, "tooth can't exceed the pitch"
assert (GROOVE_FRAC + RIDGE_FRAC) < 2.0, "groove + ridge need axial play"
assert SOCKET_DEPTH > H_OVERLAP, "socket must be deeper than the skirt (rims stop)"
assert BORE_R < _sph(H_OVERLAP) - WALL - THREAD_CLR - THREAD_DEPTH, "skirt needs a wall around the bore"
# Uniform wall everywhere: socket wall = sph(z) − female_bore = WALL by construction.
assert _sph(SOCKET_DEPTH) - WALL > 0, "socket must stay inside the sphere"
