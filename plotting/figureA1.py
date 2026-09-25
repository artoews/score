"""Make Figure A1 for paper.

"""
import argparse

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from os import path, makedirs

from params import *
from plot import color_panels, label_panels, label_encode_dirs

ASPECT = 1.6 # figure aspect ratio (height/width)
SHEAR_S = -0.5 # shear slope s in x' = x + s*z. Negative so positive-z (the bump) shears toward -x.
SIGMA = 0.45 # Gaussian half-width sigma in z = exp(-(x/SIGMA)**2)
X_HALF = 1.0 # Gaussian curve's plotted x half-span.
N_SAMPLES = 12 # Number of equal-x-spaced sample dots (spins) on the curve 
SAMPLE_DX = 2 * X_HALF / 7 # Sample dot spacing
Z_BOTTOM = -0.3; Z_TOP = 1.15 # Vertical frame limits
X_FRAME = 1.7 # Half-extent of the x axis. Larger than X_HALF so the Gaussian sits centered with headroom and the sheared bump isn't clipped.
Z_START = -0.15; Z_END=1.0 # z-range the projection through-lines span
LINE_LW_SCALE = 0.6; DASH = (4, 3) # Dashed-line dash pattern (on, off) in points, for the projection through-lines.
LINE_COLOR = "gray" # Projection through-line color
TICK_HALF = 0.105; TICK_LW = mpl.rcParams["axes.linewidth"] * 1.5 # Tick formatting on z=0 axis at each original spin x-position
SPIN_SIZE = mpl.rcParams["lines.markersize"]; SPIN_EDGE_LW = 0.6; FADE_ALPHA = 0.3 # spin (sample-dot) marker formatting
HIGHLIGHT_INDEX = 6 # Index of highlighted spin
TRIANGLE_LW_SCALE = 0.6; TRIANGLE_COLOR = "red"; TRIANGLE_LABEL_SIZE = MEDIUM_SIZE # Shear triangle formatting
THETA_ARC_RADIUS = 0.2; THETA_LABEL_OFFSET = 0.06 # Triangle arc label

PANEL_TITLES = ("Excited Slice Profile",
                "In-Plane Displacement, Normal Projection",
                "In-Plane Displacement, Tilted Projection")


def _gaussian(x):
    """Curve coordinate z = exp(-(x/SIGMA)**2): the bump opens toward +z."""
    return np.exp(-((x / SIGMA) ** 2))


def _curve():
    """Dense (x, z) of the Gaussian slice profile for a smooth curve."""
    x = np.linspace(-X_HALF, X_HALF, 400)
    return x, _gaussian(x)


def _samples():
    """Equal-spaced sample pairs on gaussian curve """
    x = (np.arange(N_SAMPLES) - (N_SAMPLES - 1) / 2) * SAMPLE_DX
    return x, _gaussian(x)


def _frame(ax):
    """Apply the shared equal-aspect frame + solid z=0 reference line """
    ax.set_xlim(-X_FRAME, X_FRAME)  # x horizontal
    ax.set_ylim(Z_BOTTOM, Z_TOP)    # z vertical
    ax.set_aspect("equal")
    ax.axhline(0.0, color="black", lw=mpl.rcParams["axes.linewidth"], zorder=1)
    _axis_ticks(ax)
    ax.set_axis_off()


def _axis_ticks(ax):
    """Draw short tick marks straddling the origin """
    sx, _ = _samples()
    for x in sx:
        ax.plot([x, x], [-TICK_HALF, TICK_HALF], color="black",
                lw=TICK_LW, zorder=1, solid_capstyle="butt")


def _through_lines(ax, xs, zs, slope):
    """Draw a `slope` through-line across each sample dot.
    
    Each line spans the shared z-range [Z_START, Z_END]. A sample sits at (x_dot, z_dot).
    The line has slope dx/dz = slope and passes through the dot: x(z) = x_dot + slope * (z - z_dot).
    """
    line_lw = mpl.rcParams["lines.linewidth"] * LINE_LW_SCALE
    for x, z in zip(xs, zs):
        x_start = x + slope * (Z_START - z)
        x_end = x + slope * (Z_END - z)
        ax.plot([x_start, x_end], [Z_START, Z_END], color=LINE_COLOR,
                lw=line_lw, linestyle=(0, DASH), zorder=2)


def _spins(ax, xs, zs, alpha=1.0):
    """Plot the sample-dot spins at (xs, zs): cardinal discs with a thin black outline."""
    ax.plot(xs, zs, "o", color="tab:blue", markersize=SPIN_SIZE,
            markeredgecolor="black", markeredgewidth=SPIN_EDGE_LW,
            alpha=alpha, zorder=4)


def _projected_spins(ax, xs, zs, slope):
    """Plot each spin's projection onto z=0 along a `slope` through-line -- where the
    line x(z) = x + slope*(z_target - z) meets z_target=0, i.e. x - slope*z.
    """
    x_projected = xs - slope * zs
    _spins(ax, x_projected, np.zeros_like(x_projected))


def _shear_triangle(ax, x_dot, z_dot, slope):
    """Draw coordinate triangle for the highlighted spin at (x_dot, z_dot). """
    x_cross = x_dot - slope * z_dot
    lw = mpl.rcParams["lines.linewidth"] * TRIANGLE_LW_SCALE
    triangle_zorder = 5 # draw on top of everything else
    ax.plot([x_cross, x_cross], [0.0, z_dot], color=TRIANGLE_COLOR, lw=lw, zorder=triangle_zorder) # vertical leg
    ax.plot([x_cross, x_dot], [z_dot, z_dot], color=TRIANGLE_COLOR, lw=lw, zorder=triangle_zorder) # horizontal leg

    # Delta z label
    ax.text(x_cross + THETA_LABEL_OFFSET, 0.75 * z_dot, r"$\Delta z_i \propto f_i$",
            color=TRIANGLE_COLOR, ha="left", va="center", size=TRIANGLE_LABEL_SIZE,
            zorder=triangle_zorder)
    # Delta x label
    x_left, x_right = min(x_dot, x_cross), max(x_dot, x_cross)
    ax.text(x_left + 0.25 * (x_right - x_left), z_dot + THETA_LABEL_OFFSET,
            r"$\Delta x_i \propto f_i$", color=TRIANGLE_COLOR, ha="left", va="bottom",
            size=TRIANGLE_LABEL_SIZE, zorder=triangle_zorder)

    # Arc for view angle theta
    theta = np.arctan(abs(slope)) # view angle
    sign = 1.0 if x_dot >= x_cross else -1.0
    start_angle = np.pi / 2
    end_angle = np.pi / 2 - sign * theta
    t = np.linspace(start_angle, end_angle, 50)
    arc_x = x_cross + THETA_ARC_RADIUS * np.cos(t)
    arc_z = 0.0 + THETA_ARC_RADIUS * np.sin(t)
    ax.plot(arc_x, arc_z, color=TRIANGLE_COLOR, lw=lw, zorder=triangle_zorder)

    # Theta label
    mid_angle = (start_angle + end_angle) / 2
    original_r = THETA_ARC_RADIUS - 0.5 * THETA_LABEL_OFFSET
    original_x = x_cross + original_r * np.cos(mid_angle)
    original_z = 0.0 + original_r * np.sin(mid_angle)
    centroid_x = (x_cross + x_cross + x_dot) / 3
    centroid_z = (0.0 + z_dot + z_dot) / 3
    halfway_x = (original_x + centroid_x) / 2
    halfway_z = (original_z + centroid_z) / 2
    label_x = (halfway_x + original_x) / 2
    label_z = (halfway_z + original_z) / 2
    ax.text(label_x, label_z, r"$\theta$", color=TRIANGLE_COLOR, ha="center",
            va="center", size=TRIANGLE_LABEL_SIZE, zorder=triangle_zorder)


def _glyph(ax):
    """Draw the z-up/x-right orientation glyph in the top-left quadrant of the panel """
    glyph_offset = 0.08
    glyph_length = 0.2
    fig = ax.get_figure()
    bbox = ax.get_window_extent()
    x_per_inch = (ax.get_xlim()[1] - ax.get_xlim()[0]) / bbox.width * fig.dpi
    z_per_inch = (ax.get_ylim()[1] - ax.get_ylim()[0]) / bbox.height * fig.dpi

    sx, _ = _samples()
    x_midpoint = (sx[0] + sx[1]) / 2
    x_anchor = x_midpoint - glyph_offset * x_per_inch

    vertex_z_drop = (glyph_length + 2 * glyph_offset) * z_per_inch  # Z_TOP -> vertex, in data units
    vertex_z_at_top = Z_TOP - vertex_z_drop
    target_vertex_z = vertex_z_at_top / 2  # halfway down to z=0
    y_anchor = target_vertex_z + vertex_z_drop

    label_encode_dirs(ax, x_label="x", y_label="z", loc="top-left-plot",
                      offset=glyph_offset, length=glyph_length, color="black",
                      x_anchor=x_anchor, y_anchor=y_anchor, size=MEDIUM_SIZE)


def _panel_slice(ax, show_lines):
    """Excited slice: Gaussian curve + sample dots, with optional vertical through-lines """
    cx, cz = _curve()
    ax.plot(cx, cz, color="tab:blue", zorder=3)
    sx, sz = _samples()
    if show_lines:
        _through_lines(ax, sx, sz, slope=0.0)
    _spins(ax, sx, sz)
    _frame(ax)
    _glyph(ax)


def _panel_sheared(ax, s, slope, show_lines, show_triangle=False, show_projected=False):
    """Readout displacement: the curve + dots sheared by x' = x + s*z, with optional
    through-lines of `slope` (0 for the displaced projection, s for the VAT one).
    """
    cx, cz = _curve()
    ax.plot(cx + s * cz, cz, color="tab:blue", zorder=3)
    sx, sz = _samples()
    sx_sheared = sx + s * sz
    if show_lines:
        _through_lines(ax, sx_sheared, sz, slope)
    _spins(ax, sx_sheared, sz, alpha=FADE_ALPHA if show_projected else 1.0)
    if show_projected:
        _projected_spins(ax, sx_sheared, sz, slope)
    if show_triangle:
        x_dot, z_dot = sx_sheared[HIGHLIGHT_INDEX], sz[HIGHLIGHT_INDEX]
        _shear_triangle(ax, x_dot, z_dot, slope)
    _frame(ax)
    _glyph(ax)


def build(s=SHEAR_S, show_lines=True, show_triangle=True, show_projected=True):
    """Render the VAT figure as 3 panels stacked vertically """
    fig = plt.figure(figsize=(FIG_WIDTH[0], FIG_WIDTH[0] * ASPECT))
    subfigs = fig.subfigures(3, 1, hspace=0.05)

    panel_axes = []
    for subfig, title in zip(subfigs, PANEL_TITLES):
        ax = subfig.subplots(1, 1, gridspec_kw={"left": 0.025, "right": 0.975,
                                                 "top": 0.80, "bottom": 0.05})
        subfig.suptitle(title, y=0.93, fontsize=LARGE_SIZE)
        panel_axes.append(ax)

    _panel_slice(panel_axes[0], show_lines=show_lines)
    _panel_sheared(panel_axes[1], s, slope=0.0, show_lines=show_lines,
                    show_projected=show_projected)
    _panel_sheared(panel_axes[2], s, slope=s, show_lines=show_lines,
                    show_triangle=show_triangle, show_projected=show_projected)

    color_panels(subfigs)
    label_panels(subfigs)
    return fig


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("save_dir", type=str, help="path where figure is saved")
    p.add_argument("--no-lines", dest="show_lines", action="store_false",
                   help="hide the projection through-lines")
    p.add_argument("--s", type=float, default=SHEAR_S,
                   help="shear slope s in x' = x + s*z (negative shears +z toward -x)")
    p.add_argument("--no-triangle", dest="show_triangle", action="store_false",
                   help="hide the red shear-triangle annotations on panel C")
    p.add_argument("--no-projected", dest="show_projected", action="store_false",
                   help="hide the z=0 projected spins (and don't fade the "
                        "true-position spins)")
    p.add_argument("-p", "--plot", action="store_true", help="show plots")
    a = p.parse_args(argv)
    makedirs(a.save_dir, exist_ok=True)

    fig = build(s=a.s, show_lines=a.show_lines, show_triangle=a.show_triangle,
                show_projected=a.show_projected)
    plt.savefig(path.join(a.save_dir, "figureA1.png"), dpi=DPI)
    plt.savefig(path.join(a.save_dir, "figureA1.pdf"), dpi=DPI)

    if a.plot:
        plt.show()


if __name__ == "__main__":
    main()
