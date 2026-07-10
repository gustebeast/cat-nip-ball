"""Geometric helpers for the catnip ball — pure functions, no module state."""
from __future__ import annotations

from math import sin, cos, radians, sqrt, atan, degrees

import cadquery as cq

from .dimensions import PITCH, HOLE_D, R_OUT


def sphere_r(z: float) -> float:
    """Outer-sphere radius at height z."""
    return sqrt(R_OUT**2 - z**2)


def make_conical_thread(pts, z0: float, z1: float, r0: float, r1: float) -> cq.Workplane:
    """Sweep a thread profile along a single-start CONICAL helix.

    The helix runs at mean radius r0 (at z0) tapering to r1 (at z1); the cone
    angle is derived from that slope. ``pts`` is the cross-section polyline in
    the XZ plane (x = radius, y = axial height) positioned around the helix
    start. Used two ways:
      • male groove cutter — triangle, base on the crest cone, apex at the root
        (cut from the skirt → leaves teeth with flat crests);
      • female ridge — trapezoid, base on the bore cone, flat tip inward
        (unioned onto the socket).
    Returned solid is cut (male) or unioned (female) by the caller.
    """
    height = z1 - z0
    angle = degrees(atan((r1 - r0) / height))      # +→radius grows with z; here r1<r0 → negative
    helix = cq.Wire.makeHelix(PITCH, height, r0, angle=angle).translate((0, 0, z0))
    prof = cq.Workplane("XZ").polyline(pts).close()
    return prof.sweep(cq.Workplane(obj=helix), isFrenet=True)


def radial_hole(theta_deg: float, phi_deg: float) -> cq.Solid:
    """Air-hole cutter: a cylinder from the sphere centre outward along the
    direction (theta from +z, phi azimuth). Length overshoots the shell."""
    t, p = radians(theta_deg), radians(phi_deg)
    d = cq.Vector(sin(t) * cos(p), sin(t) * sin(p), cos(t))
    return cq.Solid.makeCylinder(HOLE_D / 2, R_OUT + 2.0, cq.Vector(0, 0, 0), d)


def heal(wp: cq.Workplane) -> cq.Workplane:
    """OCCT ShapeFix + UnifySameDomain to clean tiny face/edge tolerance
    issues (swept-thread seams) before STEP export, and merge same-surface
    faces. Mirrors the shared Archive/3D convention."""
    from OCP.ShapeFix import ShapeFix_Shape  # type: ignore[import]
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain  # type: ignore[import]
    from OCP.TopAbs import TopAbs_COMPOUND

    shape = wp.val().wrapped
    fixer = ShapeFix_Shape(shape)
    fixer.SetPrecision(1e-4)
    fixer.SetMaxTolerance(1e-3)
    fixer.Perform()
    fixed = fixer.Shape()
    try:
        unifier = ShapeUpgrade_UnifySameDomain(fixed, True, True, True)
        unifier.Build()
        unified = unifier.Shape()
    except Exception:
        unified = fixed
    if unified.ShapeType() == TopAbs_COMPOUND:
        wrapped = cq.Compound(unified)
    else:
        wrapped = cq.Solid(unified)
    return cq.Workplane("XY").add(wrapped)
