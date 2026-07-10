"""The two printed parts: bottom (male) half and top (female) half.

Both halves are a revolved profile (rotationally clean → watertight); then the
tapered thread is cut (male groove) or added (female ridge) along a conical
helix, and the air holes are cut. The outside is a true sphere on both halves —
they meet flush at the equator. See dimensions.py for the joint rationale.
"""
from math import atan2, cos, sin, sqrt

import cadquery as cq

from .dimensions import (
    R_OUT, R_IN, WALL,
    H_OVERLAP, SOCKET_DEPTH,
    THREAD_DEPTH, THREAD_CLR, CREST_FLAT, PITCH,
    GROOVE_FRAC, RIDGE_FRAC, THREAD_OVERLAP,
    THREAD_Z0, THREAD_Z1, BORE_R, BORE_CAV_Z,
    N_RING, RING_THETA,
)
from .helpers import make_conical_thread, radial_hole, sphere_r

# ── Thread cones (radius as a function of height z) ──────────────────────────
def _MC(z): return sphere_r(z) - WALL - THREAD_CLR      # male crest
def _MR(z): return _MC(z) - THREAD_DEPTH                # male root
def _FB(z): return sphere_r(z) - WALL                   # female bore
def _FCR(z): return _MR(z) + THREAD_CLR                 # female ridge tip
def _RIN_S(z): return sqrt(R_IN**2 - z**2)              # concentric inner-dome radius


def _arc_mid(r, p_start, p_end):
    """Midpoint on the circle of radius r between two points on it — for a
    sign-unambiguous threePointArc."""
    a0, a1 = atan2(p_start[1], p_start[0]), atan2(p_end[1], p_end[0])
    am = (a0 + a1) / 2.0
    return (r * cos(am), r * sin(am))


# ============================================================
# BOTTOM HALF — male: tapered, grooved threaded skirt
# ============================================================
def _bottom_profile():
    outer_mid = _arc_mid(R_OUT, (0, -R_OUT), (R_OUT, 0))
    inner_mid = _arc_mid(R_IN, (BORE_R, BORE_CAV_Z), (0, -R_IN))
    return (
        cq.Workplane("XZ")
        .moveTo(0, -R_OUT)                              # outer bottom pole
        .threePointArc(outer_mid, (R_OUT, 0))          # outer dome to equator
        .lineTo(_MC(0), 0)                              # flat rim (the WALL+CLR overhang)
        .lineTo(_MC(H_OVERLAP), H_OVERLAP - 0.8)       # tapered skirt (crest cone)
        .lineTo(_MC(H_OVERLAP) - 0.8, H_OVERLAP)       # 45° lead-in chamfer on the skirt tip
        .lineTo(BORE_R, H_OVERLAP)                     # skirt top in to bore
        .lineTo(BORE_R, BORE_CAV_Z)                    # down the catnip bore
        .threePointArc(inner_mid, (0, -R_IN))          # inner cavity dome
        .lineTo(0, -R_OUT)                             # close along the axis
        .close()
        .revolve(360, (0, 0), (0, 1))
    )


def _male_groove():
    bw = GROOVE_FRAC * PITCH
    pts = [(_MC(THREAD_Z0) + THREAD_OVERLAP, THREAD_Z0 - bw / 2),
           (_MR(THREAD_Z0), THREAD_Z0),
           (_MC(THREAD_Z0) + THREAD_OVERLAP, THREAD_Z0 + bw / 2)]
    r0 = (_MC(THREAD_Z0) + _MR(THREAD_Z0)) / 2
    r1 = (_MC(THREAD_Z1) + _MR(THREAD_Z1)) / 2
    return make_conical_thread(pts, THREAD_Z0, THREAD_Z1, r0, r1)


def build_bottom(threads=True, holes=True):
    part = _bottom_profile()
    if threads:
        part = part.cut(_male_groove())
    if holes:
        part = part.cut(radial_hole(180, 0))                       # bottom pole
        for i in range(N_RING):
            part = part.cut(radial_hole(180 - RING_THETA, i * 360.0 / N_RING))
    return part


# ============================================================
# TOP HALF — female: tapered, ridged socket
# ============================================================
def _top_profile():
    outer_mid = _arc_mid(R_OUT, (R_OUT, 0), (0, R_OUT))
    cav_mid = _arc_mid(R_IN, (0, R_IN), (_RIN_S(SOCKET_DEPTH), SOCKET_DEPTH))
    return (
        cq.Workplane("XZ")
        .moveTo(R_OUT, 0)                               # outer equator
        .threePointArc(outer_mid, (0, R_OUT))          # outer dome to top pole
        .lineTo(0, R_IN)                               # top cap axis
        .threePointArc(cav_mid, (_RIN_S(SOCKET_DEPTH), SOCKET_DEPTH))  # cavity dome
        .lineTo(_FB(SOCKET_DEPTH), SOCKET_DEPTH)        # small ledge out to socket
        .lineTo(_FB(0), 0)                              # tapered socket (bore cone) to equator
        .lineTo(R_OUT, 0)                              # rim bottom face out
        .close()
        .revolve(360, (0, 0), (0, 1))
    )


def _female_ridge():
    bw = RIDGE_FRAC * PITCH
    cf = CREST_FLAT
    pts = [(_FB(THREAD_Z0) + THREAD_OVERLAP, THREAD_Z0 - bw / 2),
           (_FCR(THREAD_Z0), THREAD_Z0 - cf / 2),
           (_FCR(THREAD_Z0), THREAD_Z0 + cf / 2),
           (_FB(THREAD_Z0) + THREAD_OVERLAP, THREAD_Z0 + bw / 2)]
    r0 = (_FB(THREAD_Z0) + _FCR(THREAD_Z0)) / 2
    r1 = (_FB(THREAD_Z1) + _FCR(THREAD_Z1)) / 2
    return make_conical_thread(pts, THREAD_Z0, THREAD_Z1, r0, r1)


# Min wall the thread features are allowed to leave to the outer surface. The
# female ridge's swept end-cap can poke toward the narrowing sphere; trimming it
# against a guard sphere guarantees ≥ this wall (2 perimeters) everywhere.
_GUARD_WALL = 0.8


def build_top(threads=True, holes=True):
    part = _top_profile()
    if threads:
        guard = cq.Workplane("XY").sphere(R_OUT - _GUARD_WALL)
        part = part.union(_female_ridge().intersect(guard))
    if holes:
        part = part.cut(radial_hole(0, 0))                         # top pole
        for i in range(N_RING):
            part = part.cut(radial_hole(RING_THETA, i * 360.0 / N_RING))
    return part
