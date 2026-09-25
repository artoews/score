"""Make Figure 3 for paper.

"""
import argparse
import matplotlib.pyplot as plt
import numpy as np
import sigpy as sp

from os import path, makedirs

from params import *
from plot import label_encode_dirs, color_panels, label_panels
from figure2 import make_gaussian


def dft(X, Z, grid_size, dft_size, mask):
    ''' Compute the DFT of normalized points (X, Z) with uniform intensity. '''
    im = np.zeros((grid_size, grid_size))
    X = X[mask].flatten()
    Z = Z[mask].flatten()
    for x, z in zip(X, Z):
        xi = np.round(x * grid_size) + grid_size // 2 - 1
        zi = np.round(z * grid_size) + grid_size // 2 - 1
        im[int(zi), int(xi)] += 1
    k = sp.fft(im)
    k = sp.resize(k, (dft_size, dft_size))
    return k

def draw_vertical_lines(ax, num_lines, center, spacing, solid=False):
    ''' Draw vertical grid lines. '''
    kwargs = {'linewidth': 0.75, 'color': 'cyan', 'zorder': 0}
    for x in center + (np.arange(num_lines) - num_lines//2) * spacing:
        if solid:
            ax.axvline(x, linestyle='-', **kwargs)
        else:
            ax.axvline(x, linestyle='--', **kwargs)

def draw_horizontal_lines(ax, num_lines, center, spacing, solid=False):
    ''' Draw horizontal grid lines. '''
    kwargs = {'linewidth': 0.75, 'color': 'cyan', 'zorder': 0}
    for y in center + (np.arange(num_lines) - num_lines//2) * spacing:
        if solid:
            ax.axhline(y, linestyle='-', **kwargs)
        else:
            ax.axhline(y, linestyle='--', **kwargs)

def draw_shear_lines(ax, num_lines, xlim, x0, y0, angle, spacing):
    ''' Draw lines tilted by an angle with respect to the y axis.'''
    kwargs = {'linewidth': 0.75, 'color': 'cyan', 'zorder': 0}
    slope = 1 / np.tan(angle)
    b0 = y0 - slope * x0
    for b in b0 + (np.arange(num_lines) - num_lines//2) * spacing:
        ax.plot([xlim[0], xlim[1]], [slope * xlim[0] + b, slope * xlim[1] + b], linestyle='--', **kwargs)

def plot_xz(ax, Xd, Z, F, mask, limits, zs, title, cmap=CMAP['freq'], marker_size=10, title_pad=12):
    ''' Make scatter plot of x-z plane with frequency color coding. '''
    ax.scatter(Xd[mask], Z[mask], c=F[mask], cmap=cmap, s=marker_size, edgecolors='k', linewidths=1)
    ax.set_xlim(limits['x'])
    ax.set_ylim(limits['z'])
    ax.set_aspect('equal')
    ax.set_title(title, pad=title_pad)
    ax.set_xticks([])
    ax.set_yticks([zs])
    ax.set_yticklabels(['$z_s$'])
    label_encode_dirs(ax, x_label='x', y_label='z', loc='bottom-left-plot', offset=0.08) 

def plot_kxkz(ax, k, title, cmap=CMAP['image'], title_pad=12):
    ''' Make plot of the DFT in kx-kz space. '''
    max_val = np.max(np.abs(k))
    ax.imshow(np.abs(k), cmap=cmap, vmin=max_val*0.2, vmax=max_val*0.8)
    ax.invert_yaxis()
    ax.set_xlim([-0.5, k.shape[1]-0.5])
    ax.set_ylim([-0.5, k.shape[0]-0.5])
    ax.set_title(title, pad=title_pad)
    ax.set_yticks([])
    ax.set_xticks([k.shape[1] // 2])
    ax.set_xticklabels([0])
    label_encode_dirs(ax, x_label='$k_x$', y_label='$k_z$', loc='bottom-left-plot', offset=0.12, color='white')

p = argparse.ArgumentParser(description='Make figure 3')
p.add_argument('save_dir', type=str, help='path where figure is saved')
p.add_argument('-p', '--plot', action='store_true', help='show plots')

if __name__ == '__main__':

    args = p.parse_args()
    makedirs(args.save_dir, exist_ok=True)
    
    # Simulate example data

    n = 16 # grid size
    zs = 5 # slice plane
    gx = 1 # kHz/pixel
    gz = 1  # kHz/pixel
    rfbw = 0.2 # kHz

    X, Z, F = make_gaussian(n + 1, n)
    Xd = X + F / gx # eq. [1] in paper
    Xs = Xd + (Z - zs) * gz / gx # eq. [7] in paper
    shear_angle = np.arctan(gz / gx)  # radians
    thin_slice_mask = (np.abs(F + gz * (Z - zs)) <= rfbw)

    # Compute DFT

    grid_size = 10 * n
    dft_size = 32
    K = dft(X/(n+1), Z/(n+1), grid_size, dft_size, thin_slice_mask)
    Kd = dft(Xd/(n+1), Z/(n+1), grid_size, dft_size, thin_slice_mask)
    Ks = dft(Xs/(n+1), Z/(n+1), grid_size, dft_size, thin_slice_mask)

    # Set common plot parameters

    ticks = {'x': [-zs, 0, zs],
             'z': [-zs, 0, zs],
             'f': np.arange(0, 5, 1)
             }
    limits = {'x': [X.min()-0.5, X.max()+0.5],
              'z': [Z.min()-0.5, Z.max()+0.5],
              'f': [F.min()-0.5, F.max()+0.5]
              }
        
    # Create subfigure layout

    fig = plt.figure(figsize=(FIG_WIDTH[0], FIG_WIDTH[0] * 1.25))
    subfigs = fig.subfigures(2, 1, height_ratios=[1, 1], hspace=0.02)
    subfig_A = subfigs[0]
    subfig_B = subfigs[1]

    # Make each subfigure A (Image) and B (DFT)

    axes_A = subfig_A.subplots(1, 2,
                               gridspec_kw={'left': 0.08, 'right': 0.96, 'bottom': 0.03, 'top': 0.8, 'wspace': 0.25})
    axes_B = subfig_B.subplots(1, 2,
                               gridspec_kw={'left': 0.08, 'right': 0.96, 'bottom': 0.03, 'top': 0.8, 'wspace': 0.25})

    ax = axes_A[0]
    plot_xz(ax, Xd, Z, F, thin_slice_mask, limits, zs, 'Unsheared View\n(Image)')
    draw_horizontal_lines(ax, 1, 5, 4, solid=True)
    draw_vertical_lines(ax, 3, 0, 4)

    ax = axes_A[1]
    plot_xz(ax, Xs, Z, F, thin_slice_mask, limits, zs, 'Sheared View\n(Image)')
    draw_horizontal_lines(ax, 1, 5, 4, solid=True)
    draw_shear_lines(ax, 3, limits['x'], 0, zs, shear_angle, 4)

    ax = axes_B[0]
    plot_kxkz(ax, Kd, 'Unsheared View\n(DFT)')
    draw_vertical_lines(ax, 1, dft_size//2, 4, solid=True)
    draw_horizontal_lines(ax, 3, dft_size//2, 15)

    ax = axes_B[1]
    plot_kxkz(ax, Ks, 'Sheared View\n(DFT)')
    draw_vertical_lines(ax, 1, dft_size//2, 4, solid=True)
    draw_shear_lines(ax, 3, [0, dft_size], dft_size//2, dft_size//2, np.pi/2+shear_angle, 15)

    # Draw labelled arrows between panels

    # Center both arrows on the gap midpoint between the left and right panels (a common
    # figure x) so they line up as a vertical column; each arrow stays vertically aligned
    # with its own row's title.
    left_edge = fig.transFigure.inverted().transform(axes_A[0].transAxes.transform((1.0, 0.5)))[0]
    right_edge = fig.transFigure.inverted().transform(axes_A[1].transAxes.transform((0.0, 0.5)))[0]
    x_fig = (left_edge + right_edge) / 2
    fig.canvas.draw()  # render so title positions are available
    for ax, arrow_label in zip((axes_A[0], axes_B[0]), ('Shear ' + r'$+x$' + '\n(Eq. 7)',  'Shear ' + r'$-k_z$' + '\n(Eq. 11)')):
        title_bb = fig.transFigure.inverted().transform(ax.title.get_window_extent())
        y_fig = (title_bb[0][1] + title_bb[1][1]) / 2
        fig.text(x_fig, y_fig, arrow_label, ha="center", va="center", size=SMALL_SIZE,
                    bbox=dict(boxstyle="rarrow, pad=0.3", fc="cyan", ec="black", lw=1))

    # Label and color panels

    color_panels([subfig_A, subfig_B])
    label_panels([subfig_A, subfig_B])

    # Produce figure

    plt.savefig(path.join(args.save_dir, 'figure3.png'), dpi=DPI)
    plt.savefig(path.join(args.save_dir, 'figure3.pdf'), dpi=DPI)
    if args.plot:
        plt.show()