"""Make Figure 5, 6, or 7 for paper.

All outputs are saved with prefix figure{N}_.
"""

import argparse
import matplotlib.pyplot as plt
import numpy as np

from os import path, makedirs

from params import *
from results import load_score_data, plot_results_two_panel
from data_config import CONFIGS

p = argparse.ArgumentParser(description='Make results figures for in vivo data')
p.add_argument('figure', type=int, choices=[5, 6, 7], help='which figure to make')
p.add_argument('data_dir', type=str, help='path to root of "score-data" directory')
p.add_argument('save_dir', type=str, help='path where figure is saved')
p.add_argument('-p', '--plot', action='store_true', help='show plots')
p.add_argument('--no_bin', action='store_true', help='skip the single-bin figure (msi only) for faster figure development')

if __name__ == '__main__':

    args = p.parse_args()
    makedirs(args.save_dir, exist_ok=True)

    # get plotting parameters from config
    config = CONFIGS[args.figure]
    case_dir = path.join(args.data_dir, config['case_dir'])
    fov = config['fov']
    roi = config['roi']
    up = config['up']
    bin_ = config['bin']
    bin_scale = config['bin_scale']
    inplane_vmax = config['inplane_vmax']
    reformat_vmax = config['reformat_vmax']
    vmax_pct = config['vmax_pct']
    y_pos = config['y_pos']
    z_pos = config['z_pos']
    flip = config['flip']
    annotations = config['annotations']
    width_ratios = config['width_ratios']
    fig_height_scale = config['fig_height_scale']
    norm_scale = config['norm_scale']

    images_3dmsi = load_score_data(case_dir, 'msi')
    if not args.no_bin:
        # read only the bin we display
        images_3dbin = load_score_data(case_dir, 'bin', bin=bin_)
        images_3dbin = np.squeeze(images_3dbin)
    shape = images_3dmsi[0].shape
    res = tuple(fov[i] / shape[i] for i in range(3))

    # adjust slices to account for in-plane upsampling. Only x/y are scaled;
    # z (roi start/size and z_pos) is in raw coordinates.
    if len(roi) == 6:
        roi = np.array(roi) * np.array([up, up, 1, up, up, 1])
    else:
        roi = np.array(roi) * up
    y_pos = y_pos * up

    # normalize image intensities
    norm = norm_scale * np.median(np.abs(images_3dmsi[:, :, y_pos, :]))
    images_3dmsi = images_3dmsi / norm

    names = ['msi']
    images = [images_3dmsi]
    if not args.no_bin:
        images_3dbin = images_3dbin / norm * bin_scale
        names.insert(0, 'bin')
        images.insert(0, images_3dbin)
    if flip:
        images = [np.flip(im, axis=1) for im in images]

    for i in range(len(images)):

        fig = plt.figure(figsize=(FIG_WIDTH[2], FIG_WIDTH[2] * fig_height_scale))
        subfigs = fig.subfigures(1, 2, width_ratios=width_ratios, wspace=0.02)
        # panel A reserves a larger left margin for the offset row labels; panel B has none
        gridspec_kw_A = {'left': 0.1, 'right': 0.95, 'bottom': 0.04, 'top': 0.93, 'wspace': 0.1, 'hspace': 0.1}
        gridspec_kw_B = {'left': 0.05, 'right': 0.95, 'bottom': 0.04, 'top': 0.93, 'wspace': 0.1, 'hspace': 0.1}
        plot_results_two_panel(subfigs, images[i], roi, z_pos, y_pos, res, (gridspec_kw_A, gridspec_kw_B), annotations=annotations,
                               inplane_vmax=inplane_vmax, inplane_vmax_pct=vmax_pct,
                               reformat_vmax=reformat_vmax, reformat_vmax_pct=vmax_pct)
        name_suffix = '' if names[i] == 'msi' else f'_{names[i]}'
        plt.savefig(path.join(args.save_dir, f'figure{args.figure}{name_suffix}.png'), dpi=DPI)
        plt.savefig(path.join(args.save_dir, f'figure{args.figure}{name_suffix}.pdf'), dpi=DPI)

    if args.plot:
        plt.show()
