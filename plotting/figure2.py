"""Make Figure 2 for paper.

"""
import argparse
import matplotlib.pyplot as plt
import numpy as np

from os import path, makedirs

from params import *
from plot import color_panels, label_panels


def make_gaussian(num_points, fov, peak=4, std=3):
    ''' Sample a Gaussian function over a grid of points. '''
    x = np.linspace(-fov//2, fov//2, num_points)
    z = np.linspace(-fov//2, fov//2, num_points)
    X, Z = np.meshgrid(x, z)
    F = peak * np.exp(-(X**2 + Z**2) / (2 * std**2))
    return X, Z, F

def draw_hash_lines(ax, angle, xlim, xticks, yticks):
    ''' Draw hash lines tilted by an angle with respect to the y axis.'''
    lw = 0.5
    color = 'gray'
    slope = 100 if angle == 0 else 1 / np.tan(angle)
    for offset in xticks:
        ax.plot(
            [xlim[0], xlim[1]],
            [(xlim[0] - offset) * slope, (xlim[1]-offset) * slope],
            color=color, linestyle='-', linewidth=lw, zorder=0
        )
    for y in yticks:
        ax.axhline(y, color=color, linestyle='-', linewidth=lw, zorder=0)

def plot_xzf_true(ax, XZF, XZF_hr, ticks, cmap=CMAP['freq'], marker_size=10):
    ''' Make scatter and surface plots of the true spin distribution in x-z-f space.'''

    # basic setup
    X, Z, F = XZF
    X_hr, Z_hr, F_hr = XZF_hr
    ax.set_box_aspect([1, 1, 1.3])
    ax.view_init(elev=14, azim=67, roll=-1)
    ax.set_facecolor('0.9')
    plt.subplots_adjust()

    # plot 3D scatter
    scat = ax.scatter(X, Z, F, c=F, s=marker_size, cmap=cmap)
    scat.set_clim(0, np.max(F_hr))
    cbar = fig.colorbar(scat, ax=ax, orientation='horizontal', fraction=0.03, pad=0.13, aspect=18)

    # plot f-projection of 3D scatter to x-z plane
    ax.scatter(X, Z, c=F, zdir='z', zs=-1.6, s=marker_size/5, cmap=cmap)  # xz projection

    # plot 3D surface
    ax.plot_surface(X_hr, Z_hr, F_hr, cmap=cmap, alpha=0.5)

    # add annotations
    cbar.set_label('frequency f [kHz]')
    ax.set_xticks(ticks['x'])
    ax.set_yticks(ticks['z'])
    ax.set_zticks(ticks['f'])
    ax.set_xlabel('in-plane x [mm]', labelpad=-8)
    ax.set_ylabel('slice z [mm]', labelpad=-8)
    ax.set_zlabel('frequency f [kHz]', labelpad=-5)
    ax.tick_params(axis='x', pad=-5)
    ax.tick_params(axis='y', pad=-5)
    ax.tick_params(axis='z', pad=-2)

def plot_xf_true_unsheared(axes, X, F, Xd, shear_angle, ticks, limits, cmap=CMAP['freq'], marker_size=10):
    ''' Make scatter plots of the true and unsheared views in x-f space. '''
    titles = ['True Object', 'In-Plane\nDisplacement\n(x-f shear)']
    for ax, title, X_data in zip(axes, titles, [X, Xd]):
        ax.scatter(X_data, F, c=F, s=marker_size, cmap=cmap)
        ax.set_xlabel('x [mm]')
        ax.set_xticks(ticks['x'])
        ax.set_yticks(ticks['f'])
        ax.set_xlim(limits['x'])
        ax.set_ylim(limits['f'])
        ax.set_title(title)
    axes[0].set_ylabel('f [kHz]')
    draw_hash_lines(axes[0], 0, limits['x'], ticks['x'], ticks['f'])
    draw_hash_lines(axes[1], shear_angle, limits['x'], ticks['x'], ticks['f'])

def plot_zf_true_selection(ax, Z, F, mask, ticks, limits, cmap=CMAP['freq'], marker_size=10):
    ''' Make scatter plot of the true view in z-f space with slice selection. '''
    ax.scatter(Z, F, c=F, s=marker_size, cmap=cmap, alpha=0.2)
    ax.scatter(Z[mask], F[mask], c=F[mask], s=marker_size, cmap=cmap, edgecolors='k', linewidths=1)
    ax.plot([0, zs+1], [zs * gz, -gz], color='k', linewidth=1, linestyle='-', zorder=0) # draw slice plane
    ax.set_xlabel('z [mm]')
    # ax.set_ylabel('f [kHz]')
    ax.set_ylabel('f [kHz]')
    ax.set_xticks(ticks['z'])
    ax.set_yticks(ticks['f'])
    ax.set_xlim(limits['z'])
    ax.set_ylim(limits['f'])
    ax.set_title('Slice Selection\n(z-f correlation)')
    # draw_hash_lines(ax, 0, limits['z'], ticks['z'], ticks['f'])

def plot_xz_true_unsheared(axes, X, Z, F, Xd, mask, ticks, limits, cmap=CMAP['freq'], marker_size=10):
    ''' Make scatter plots of the true and unsheared views in x-z space. '''
    titles = ['True Object', 'In-Plane\nDisplacement\n(x-z shear)']
    for ax, title, X_data in zip(axes, titles, [X, Xd]):
        ax.scatter(X_data, Z, c=F, s=marker_size, cmap=cmap, alpha=0.2)
        ax.scatter(X_data[mask], Z[mask], c=F[mask], s=marker_size, cmap=cmap, edgecolors='k', linewidths=1)
        ax.set_xlabel('x [mm]')
        ax.set_xticks(ticks['x'])
        ax.set_yticks(ticks['z'])
        ax.set_xlim(limits['x'])
        ax.set_ylim(limits['z'])
        ax.set_title(title)
        ax.set_aspect('equal')
    axes[0].set_ylabel('z [mm]', labelpad=0)
    # ax.plot([X.min(), X.max()], [zs, zs], color='k', linewidth=1, linestyle='-', zorder=0) # draw slice plane

def plot_xz_sheared(ax, Xs, Z, F, mask, ticks, limits, cmap=CMAP['freq'], marker_size=10):
    ''' Make scatter plot of the sheared view in x-z space. '''
    ax.scatter(Xs, Z, c=F, s=marker_size, cmap=cmap, alpha=0.2)
    ax.scatter(Xs[mask], Z[mask], c=F[mask], s=marker_size, cmap=cmap, edgecolors='k', linewidths=1)
    # ax.plot([X.min(), X.max()], [zs, zs], color='k', linewidth=1, linestyle='-', zorder=0) # draw slice plane
    ax.set_xlabel('x [mm]')
    ax.set_ylabel('z [mm]', labelpad=0)
    ax.set_xticks(ticks['x'])
    ax.set_yticks(ticks['z'])
    ax.set_xlim(limits['x'])
    ax.set_ylim(limits['z'])
    ax.set_aspect('equal')
    ax.set_title('Shear Correction\n(reverse x-z shear)')

p = argparse.ArgumentParser(description='Make figure 2')
p.add_argument('save_dir', type=str, help='path where figure is saved')
p.add_argument('-p', '--plot', action='store_true', help='show plots')

if __name__ == '__main__':

    args = p.parse_args()
    makedirs(args.save_dir, exist_ok=True)
    
    # Simulate example data

    n = 16 # grid size
    zs = 5 # slice plane
    gx = 1 # kHz/pixel
    gz = 1 # kHz/pixel
    rfbw = 0.2 # kHz

    X, Z, F = make_gaussian(n + 1, n)
    X_hr, Z_hr, F_hr = make_gaussian(10*n + 1, n) # high-res version for panel a surface plot only
    Xd = X + F / gx # eq. [1] in paper
    Xs = Xd + (Z - zs) * gz / gx # eq. [7] in paper
    shear_angle = np.arctan(gz / gx)  # radians
    thin_slice_mask = (np.abs(F + gz * (Z - zs)) <= rfbw)

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

    fig = plt.figure(figsize=(FIG_WIDTH[2], FIG_WIDTH[2]*0.65))
    subfigs_A_BCDE = fig.subfigures(1, 2, width_ratios=[1.1, 2], wspace=0.01, hspace=0)
    subfig_A = subfigs_A_BCDE[0]
    subfigs_BCDE = subfigs_A_BCDE[1].subfigures(2, 2, height_ratios=[1, 0.8], width_ratios=[1.7, 1], hspace=0.02, wspace=0.02)
    subfig_B = subfigs_BCDE[0, 0]
    subfig_C = subfigs_BCDE[0, 1]
    subfig_D = subfigs_BCDE[1, 0]
    subfig_E = subfigs_BCDE[1, 1]
    
    # Make each subfigure A-E

    ax = subfig_A.subplots(1, 1,
                           subplot_kw=dict(projection='3d'),
                           gridspec_kw={'left': 0, 'right': 1, 'bottom': 0.12, 'top': 1})
    plot_xzf_true(ax, (X, Z, F), (X_hr, Z_hr, F_hr), ticks)
    subfig_A.suptitle('Example Spin Distribution\nWith Gaussian Off-Resonance')

    axes = subfig_B.subplots(1, 2,
                             sharey=True,
                             gridspec_kw={'wspace': 0.1, 'bottom': 0.21, 'top': 0.8, 'left': 0.15, 'right': 0.95})
    plot_xf_true_unsheared(axes, X, F, Xd, shear_angle, ticks, limits)

    ax = subfig_C.subplots(1, 1,
                           gridspec_kw={'bottom': 0.21, 'top': 0.8, 'left': 0.25, 'right': 0.92})
    plot_zf_true_selection(ax, Z, F, thin_slice_mask, ticks, limits)
    
    axes = subfig_D.subplots(1, 2,
                             sharey=True,
                             gridspec_kw={'wspace': 0.1, 'left': 0.15, 'right': 0.95, 'bottom': 0.06, 'top': 0.9})
    plot_xz_true_unsheared(axes, X, Z, F, Xd, thin_slice_mask, ticks, limits)
    
    ax = subfig_E.subplots(1, 1,
                           gridspec_kw={'bottom': 0.21, 'top': 0.75, 'left': 0.25, 'right': 0.92})
    plot_xz_sheared(ax, Xs, Z, F, thin_slice_mask, ticks, limits)
    
    # Label and color panels

    color_panels([subfig_A, subfig_B, subfig_C, subfig_D, subfig_E])
    label_panels([subfig_A, subfig_B, subfig_C, subfig_D, subfig_E])

    # Produce figure

    plt.savefig(path.join(args.save_dir, 'figure2.png'), dpi=DPI)
    plt.savefig(path.join(args.save_dir, 'figure2.pdf'), dpi=DPI)
    if args.plot:
        plt.show()
