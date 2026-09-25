"""Make Figure 4 for paper.

"""

import argparse
import matplotlib.pyplot as plt
import numpy as np

from os import path, makedirs

from params import *
from plot import remove_ticks
from results import draw_table_grid, color_panels

p = argparse.ArgumentParser(description='Make conceptual k-space diagram figure')
p.add_argument('save_dir', type=str, help='path where figure is saved')

p.add_argument('-n', '--n_lines', type=int, default=8, help='number of sampling lines')
p.add_argument('-s', '--shear', type=float, default=0.3, help='vertical shear of sampling lines per unit kz (off-diagonal cells)')
p.add_argument('-p', '--plot', action='store_true', help='show plots')

# axes extent (k-space, arbitrary units).
KMAX_KX = 1.5
KMAX_KZ = 1.0
# sampling extent (half-widths spanned by the sampling lines), centered at origin
SAMPLE_HALF_KX = 1.25
SAMPLE_HALF_KZ = 0.5
# prescribed k-space region (solid box): just bigger than the sampling extent so
# the outermost sampling lines sit just inside the box
BOX_MARGIN_KX = 0.03
BOX_MARGIN_KZ = 0.08
BOX_HALF_KX = SAMPLE_HALF_KX + BOX_MARGIN_KX
BOX_HALF_KZ = SAMPLE_HALF_KZ + BOX_MARGIN_KZ


def draw_kspace_axes(ax, color='black', lw=0.5, fontsize=MEDIUM_SIZE):
    ''' Draw the kx (horizontal) and kz (vertical) axes symmetric about the origin. '''
    line_kw = dict(color=color, lw=lw)
    ax.plot([-KMAX_KX, KMAX_KX], [0, 0], **line_kw)   # kx axis (symmetric)
    ax.plot([0, 0], [-KMAX_KZ, KMAX_KZ], **line_kw)   # kz axis (symmetric)
    arrow_kw = dict(arrowstyle='->', color=color, lw=lw, shrinkA=0, shrinkB=0)
    ax.annotate('', xy=(KMAX_KX, 0), xytext=(0.9 * KMAX_KX, 0), arrowprops=arrow_kw)   # kx arrowhead
    ax.annotate('', xy=(0, KMAX_KZ), xytext=(0, 0.9 * KMAX_KZ), arrowprops=arrow_kw)   # kz arrowhead
    # labels sit just beyond each arrow tip, in the direction the arrow points
    ax.text(KMAX_KX + 0.12 * KMAX_KX, 0, '$k_x$', ha='left', va='center',
            color=color, fontsize=fontsize)
    ax.text(0, KMAX_KZ + 0.12 * KMAX_KZ, '$k_z$', ha='center', va='bottom',
            color=color, fontsize=fontsize)


def draw_sampling_lines(ax, n_lines, shear=0.0, color='black', lw=1.2,
                        fontsize=MEDIUM_SIZE):
    ''' Draw sheared sampling lines with uniform spacing, spanning the cell in kx. '''
    kz_centers = np.linspace(-SAMPLE_HALF_KZ, SAMPLE_HALF_KZ, n_lines)
    kx_extent = np.array([-SAMPLE_HALF_KX, SAMPLE_HALF_KX])  # sampling extent, just inside the box
    for kz0 in kz_centers:
        kz = kz0 + shear * kx_extent  # kz shear about the origin
        ax.plot(kx_extent, kz, color=color, lw=lw, linestyle=(0, (1, 1.5)), zorder=5)  # dotted, on top

    if shear != 0.0:
        draw_shear_angle(ax, shear, color=color, fontsize=fontsize)


def draw_shear_angle(ax, shear, color='black', fontsize=MEDIUM_SIZE):
    ''' Mark the shear angle theta between a sheared sampling line and the horizontal. '''
    theta = np.arctan(shear)  # signed angle of the sheared line from horizontal
    # kz of the relevant (outermost) sampling line at kx=0, where the vertex sits
    if shear > 0:
        kz0 = -SAMPLE_HALF_KZ   # bottom sampling line
    else:
        kz0 = SAMPLE_HALF_KZ    # top sampling line
    r = 0.66 * SAMPLE_HALF_KX   # arc radius in kx units
    kx0 = -0.1 * SAMPLE_HALF_KX  # shift the arc vertex slightly left
    # the sheared line at kx0 sits at kz0 + shear*kx0; start there, then nudge the
    # vertex vertically toward the horizontal box edge
    kz_nudge = np.sign(kz0) * 0.02  # toward the box edge (away from origin)
    kz_v = kz0 + shear * kx0 + kz_nudge
    # arc from horizontal (0) up/down to the sheared line angle
    t = np.linspace(0, theta, 50)
    ax.plot(kx0 + r * np.cos(t), kz_v + r * np.sin(t), color=color, lw=0.5, zorder=6)
    # theta label just outside the arc, at its angular midpoint, nudged right
    label_r = 0.66 * SAMPLE_HALF_KX
    label_dx = 0.18 * SAMPLE_HALF_KX 
    label_dy = -np.sign(kz0) * 0.02
    ax.text(kx0 + label_dx + label_r * np.cos(0.5 * theta),
            kz_v + label_dy + label_r * np.sin(0.5 * theta),
            r'$\theta$', color=color, fontsize=fontsize,
            ha='center', va='center', zorder=6)


def draw_shading(ax, shear=0.0, color='tab:blue', sigma=0.64, n=200):
    ''' Fill the cell (axes extent) with a blue Gaussian shading. '''
    kx = np.linspace(-KMAX_KX, KMAX_KX, n)
    kz = np.linspace(-KMAX_KZ, KMAX_KZ, n)
    KX, KZ = np.meshgrid(kx, kz)
    intensity = np.exp(-((KZ - shear * KX) / sigma) ** 2)  # Gaussian in (sheared) kz
    ax.imshow(intensity, extent=[-KMAX_KX, KMAX_KX, -KMAX_KZ, KMAX_KZ],
              origin='lower', cmap=_alpha_cmap(color), aspect='auto',
              interpolation='bilinear', zorder=1)


def _alpha_cmap(color):
    ''' Colormap with constant hue, ramping alpha. '''
    from matplotlib.colors import LinearSegmentedColormap, to_rgb
    r, g, b = to_rgb(color)
    return LinearSegmentedColormap.from_list(
        '_alpha', [(r, g, b, 0.0), (r, g, b, 0.7)])


def draw_prescribed_box(ax, color='gray', lw=2):
    ''' Draw prescribed k-space region as a solid-edge box centered at origin '''
    ax.plot([-BOX_HALF_KX, BOX_HALF_KX, BOX_HALF_KX, -BOX_HALF_KX, -BOX_HALF_KX],
            [-BOX_HALF_KZ, -BOX_HALF_KZ, BOX_HALF_KZ, BOX_HALF_KZ, -BOX_HALF_KZ],
            color=color, lw=lw, solid_joinstyle='miter', zorder=2)


def plot_kspace_cell(ax, shear, n_lines, shading_shear=0.0):
    # symmetric limits so the k-space origin sits at the center of every cell,
    # keeping the column titles / row labels aligned without manual padding
    ax.set_xlim(-1.3 * KMAX_KX, 1.3 * KMAX_KX)
    ax.set_ylim(-1.45 * KMAX_KZ, 1.45 * KMAX_KZ)
    ax.set_aspect('equal')
    ax.set_facecolor('none')  # let the gray figure background show through
    remove_ticks(ax)
    for spine in ax.spines.values():
        spine.set_visible(False)
    draw_shading(ax, shear=shading_shear)
    draw_sampling_lines(ax, n_lines, shear=shear)
    draw_prescribed_box(ax)
    draw_kspace_axes(ax)


def plot_kspace_table(subfig, n_lines, shear, gridspec_kw, title_size=LARGE_SIZE,
                      conventional_label_y=0.04):
    ''' Plot the 2x2 table of conceptual k-space diagrams. '''
    axes = subfig.subplots(2, 2, gridspec_kw=gridspec_kw)
    shears = [[0.0, -shear],
              [shear, 0.0]]
    # shading is unsheared in the left column; in the right column it is sheared to
    # match that cell's sampling-line shear (top-right negative, bottom-left positive)
    shading_shears = [[0.0, -shear],
                      [0.0, -shear]]
    for i in range(2):
        for j in range(2):
            plot_kspace_cell(axes[i, j], shears[i][j], n_lines,
                             shading_shear=shading_shears[i][j])

    # row and column headers, matching the results figures (5-7)
    axes[0, 0].set_ylabel(r'$G_z$-Off' + '\nAcquisition', fontsize=title_size, labelpad=24,
                          rotation=0, ha='center', va='center', multialignment='center')
    axes[1, 0].set_ylabel(r'$G_z$-On' + '\nAcquisition', fontsize=title_size, labelpad=24,
                          rotation=0, ha='center', va='center', multialignment='center')
    axes[0, 0].set_title('Unsheared View', fontsize=title_size, pad=16)
    axes[0, 1].set_title('Sheared View', fontsize=title_size, pad=16)

    # diagonal cells are the conventional acquisitions
    for ax, conventional_label in zip((axes[0, 0], axes[1, 1]), ('(Conventional)', '(Conventional VAT)')):
        ax.text(0.5, conventional_label_y, conventional_label, transform=ax.transAxes,
                ha='center', va='bottom', color='black', fontsize=MEDIUM_SIZE)

    # interior table dividers, reinforcing the spanning headers; extend the lines
    # past the 2x2 block so they read as full table rules
    draw_table_grid(subfig, axes, overhang=0.05)

    fig = subfig.get_figure()
    fig.canvas.draw()  # finalize layout so the divider midpoints are known
    inv = subfig.transSubfigure.inverted()

    def img_box(ax):
        return inv.transform_bbox(ax.get_window_extent())

    # labelled arrow (matching figure 2) sitting just above the vertical divider,
    # pointing left-to-right (unsheared -> sheared)
    title = axes[0, 0].title
    y_arrow = inv.transform(title.get_window_extent())[:, 1].mean()
    box = [[img_box(axes[i, j]) for j in range(2)] for i in range(2)]
    x_mid = 0.5 * (box[0][0].x1 + box[0][1].x0)
    subfig.text(x_mid, y_arrow, 'Shear $-k_z$\n(Eq. 11)',
                ha='center', va='center', ma='center', size=MEDIUM_SIZE, clip_on=False,
                bbox=dict(boxstyle='rarrow, pad=0.25', fc='cyan', ec='black', lw=1.5))
    return axes


if __name__ == '__main__':

    args = p.parse_args()
    makedirs(args.save_dir, exist_ok=True)

    fig = plt.figure(figsize=(FIG_WIDTH[2], FIG_WIDTH[2] * 0.6))
    subfig = fig.subfigures(1, 1)
    gridspec_kw = {'left': 0.12, 'right': 0.96, 'bottom': 0.02, 'top': 0.86,
                   'wspace': 0.03, 'hspace': 0.03}
    plot_kspace_table(subfig, args.n_lines, args.shear, gridspec_kw)
    color_panels([subfig])

    plt.savefig(path.join(args.save_dir, 'figure4.png'), dpi=DPI)
    plt.savefig(path.join(args.save_dir, 'figure4.pdf'), dpi=DPI)

    if args.plot:
        plt.show()
