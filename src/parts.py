# SPDX-License-Identifier: CERN-OHL-S-2.0
# Copyright (c) 2026 gustebeast
# Source location: https://github.com/gustebeast/cat-nip-ball
"""The two printed parts: bottom (male) half and top (female) half.

Each half is a revolved profile (rotationally clean → watertight), then the air
holes are cut, and the THREAD IS CUT LAST AND ALONE — every thread boolean uses
``clean=False`` and the result is never healed (cadkit/THREADS_README.md rules 6
and 7: CadQuery's post-boolean unify and OCCT's ShapeFix hang or crash on the
many-face helix).

Threads come from ``cadkit.threads``; we never re-model a helix here.
"""
from math import atan2, cos, radians, sin

import cadquery as cq
from cadkit.threads import cut_thread, threaded_rod

from .dimensions import (
    R_OUT, R_IN,
    COLLAR_R, COLLAR_H, H_OVERLAP,
    PITCH, THREAD_LENGTH, THREAD_Z0, THREAD_Z1, PLUG_TOP_R,
    THREAD_MAJOR_D, THREAD_MINOR_D, MALE_MAJOR_D, MALE_MINOR_D, THREAD_CLR_D,
    BORE_R, CAVITY_R, CAVITY_Z,
    HOLE_D, N_RING, RING_THETA,
)


def _arc_mid(r, p_start, p_end):
    """Midpoint on the circle of radius r between two points on it — for a
    sign-unambiguous threePointArc (radiusArc picks the wrong arc here)."""
    a0, a1 = atan2(p_start[1], p_start[0]), atan2(p_end[1], p_end[0])
    am = (a0 + a1) / 2.0
    return (r * cos(am), r * sin(am))


def _radial_hole(theta_deg, phi_deg):
    """Air-hole cutter: a cylinder from the sphere centre outward along
    (theta from +z, phi azimuth). Length overshoots the shell."""
    t, p = radians(theta_deg), radians(phi_deg)
    d = cq.Vector(sin(t) * cos(p), sin(t) * sin(p), cos(t))
    return cq.Solid.makeCylinder(HOLE_D / 2, R_OUT + 2.0, cq.Vector(0, 0, 0), d)


def _cut_air_holes(part, pole_theta):
    """Pole hole + one mid-latitude ring. Cut BEFORE the thread (rule 6: every
    boolean on a threaded part is slow)."""
    part = part.cut(_radial_hole(pole_theta, 0))
    ring = pole_theta - RING_THETA if pole_theta else RING_THETA
    for i in range(N_RING):
        part = part.cut(_radial_hole(ring, i * 360.0 / N_RING))
    return part


# ============================================================
# BOTTOM HALF — male: collar, 45° chamfer, threaded skirt
# ============================================================
def _bottom_blank():
    """Smooth male half — the thread is cut from this afterwards."""
    male_crest_r = MALE_MAJOR_D / 2
    outer_mid = _arc_mid(R_OUT, (0, -R_OUT), (R_OUT, 0))
    inner_mid = _arc_mid(R_IN, (CAVITY_R, CAVITY_Z), (0, -R_IN))
    return (
        cq.Workplane("XZ")
        .moveTo(0, -R_OUT)                          # outer bottom pole
        .threePointArc(outer_mid, (R_OUT, 0))      # outer dome to equator
        .lineTo(COLLAR_R, 0)                        # flat rim = EQUATOR_OVERHANG
        .lineTo(COLLAR_R, COLLAR_H)                # smooth collar
        .lineTo(male_crest_r, THREAD_Z0)           # 45° chamfer in to the thread crest
        .lineTo(male_crest_r, H_OVERLAP)           # skirt at crest Ø (thread cut later)
        .lineTo(BORE_R, H_OVERLAP)                 # skirt top in to bore
        .lineTo(BORE_R, 0)                         # down the catnip bore
        .lineTo(CAVITY_R, CAVITY_Z)                # 45° flare out to the cavity
        .threePointArc(inner_mid, (0, -R_IN))      # inner cavity dome
        .lineTo(0, -R_OUT)                         # close along the axis
        .close()
        .revolve(360, (0, 0), (0, 1))
    )


def build_bottom(threads=True, holes=True):
    part = _bottom_blank()
    if holes:
        part = _cut_air_holes(part, 180)
    if threads:
        # Thread LAST and ALONE, from the smooth blank (rules 6 & 7).
        part = cut_thread(part, MALE_MINOR_D, MALE_MAJOR_D, PITCH,
                          THREAD_LENGTH, z=THREAD_Z0)
    return part


# ============================================================
# TOP HALF — female: counterbore, chamfer, threaded socket
# ============================================================
def _top_blank():
    """Smooth female half, with a SOLID plug across the thread band.

    The plug is deliberately un-bored: `threaded_rod` drills the bore AND the
    thread in one cut. Pre-boring it would make the helix cutter overlap an
    existing void, which silently no-ops (THREADS_README rule 4). Once drilled,
    the bore joins the mouth below to the catnip cavity above."""
    mouth_r = COLLAR_R + THREAD_CLR_D / 2               # clears the male collar
    chamfer_end_r = MALE_MAJOR_D / 2 + THREAD_CLR_D / 2  # clears the male chamfer
    outer_mid = _arc_mid(R_OUT, (R_OUT, 0), (0, R_OUT))
    cav_mid = _arc_mid(R_IN, (0, R_IN), (PLUG_TOP_R, THREAD_Z1))
    return (
        cq.Workplane("XZ")
        .moveTo(R_OUT, 0)                               # outer equator
        .threePointArc(outer_mid, (0, R_OUT))          # outer dome to top pole
        .lineTo(0, R_IN)                               # top cap axis
        .threePointArc(cav_mid, (PLUG_TOP_R, THREAD_Z1))  # cavity dome down to the plug
        .lineTo(0, THREAD_Z1)                          # in to the axis — plug top
        .lineTo(0, THREAD_Z0)                          # solid plug (the cutter drills it)
        .lineTo(chamfer_end_r, THREAD_Z0)              # out to the chamfer bottom
        .lineTo(mouth_r, COLLAR_H)                     # 45° chamfer out to the mouth
        .lineTo(mouth_r, 0)                            # mouth, clears the male collar
        .lineTo(R_OUT, 0)                              # rim bottom face out
        .close()
        .revolve(360, (0, 0), (0, 1))
    )


def build_top(threads=True, holes=True):
    part = _top_blank()
    if holes:
        part = _cut_air_holes(part, 0)
    if threads:
        # Cutter at NOMINAL size; clearance lives on the male (rule: reprint the
        # cheap half). clean=False — never unify/heal a threaded part.
        part = part.cut(threaded_rod(THREAD_MINOR_D, THREAD_MAJOR_D, PITCH,
                                     THREAD_LENGTH, z=THREAD_Z0), clean=False)
    return part
