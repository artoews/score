"""Make Figure 1 for paper.

"""
import argparse
import matplotlib.pyplot as plt
import numpy as np

from matplotlib.patches import Rectangle
from PIL import Image, ImageOps
from os import path, makedirs

from params import *
from plot import remove_ticks, color_panels, label_panels, label_encode_dirs
from data_config import CONFIGS


# Photographs for subfigure A and their crop boxes (left, right, top, bottom)
PHOTOS = [
    ('phantom-photo-1.jpg', (0.03, 0.95, 0.3, 0.9)),
    ('phantom-photo-2.jpg', (0.04, 0.96, 0.3, 0.92)),
    ('phantom-photo-3.jpg', (0.05, 0.95, 0.12, 0.9)),
]

# Column definitions: (label, scan subdir, view)
COLUMNS = [
    ('Metal Implant\nVAT-Off', 'gz-off', 'unsheared'),
    ('Metal Implant\nVAT-On', 'gz-on', 'sheared'),
    ('(Shape Reference)\nPlastic Replica\nVAT-On', 'gz-on-plastic-replica', 'sheared'),
]

SEP_PX = 3  # width of the black separator between concatenated columns

# Resolution-block annotations (text labels + boxes), hand-tuned per figure
ANNOTATIONS = CONFIGS[1]['annotations']
LINE_PAIR_LABELS = [a for a in ANNOTATIONS if a['type'] == 'text']
LINE_PAIR_BOXES = [a for a in ANNOTATIONS if a['type'] == 'box']

# FOV crop box
UP = CONFIGS[1]['up']
_ROI = CONFIGS[1]['roi'] # [x_start, y_start, z_start, x_size, y_size, z_size]
ROI = {
    'x': (_ROI[0] * UP, (_ROI[0] + _ROI[3]) * UP),
    'y': (_ROI[1] * UP, (_ROI[1] + _ROI[4]) * UP),
    'z': (_ROI[2], _ROI[2] + _ROI[5]),  # z is not upsampled
}


def read_dims(name):
    """ Read the cfl dimensions from the .hdr file. """
    with open(name + '.hdr', 'rt') as h:
        h.readline()  # skip
        dims = [int(i) for i in h.readline().split()]
    return dims


def load_cfl_slice(name, slc, plane='axial', bin=None):
    """ Load a single 2D slice (and optionally a single bin) from CFL.

    Avoids reading the entire (huge) file into memory. Data is stored column-major
    with dims (x, y, z, 1, 1, bin). 'axial' fixes z (x-y plane); 'sagittal' fixes y
    (x-z plane). In both cases the returned array has x as its first axis.
    """
    b = bin if bin is not None else 0
    (x0, x1), (y0, y1), (z0, z1) = ROI['x'], ROI['y'], ROI['z']
    dims = read_dims(name)
    mm = np.memmap(name + '.cfl', dtype=np.complex64, mode='r',
                   shape=tuple(dims), order='F')
    if plane == 'axial':
        im = np.array(mm[x0:x1, y0:y1, slc, 0, 0, b])
    elif plane == 'sagittal':
        im = np.array(mm[x0:x1, slc, z0:z1, 0, 0, b])
    else:
        raise ValueError(f'unknown plane: {plane}')
    del mm
    return im


def crop_photo(img, box):
    """ Crop an image array given a (left, right, top, bottom) box in fractions. """
    h, w = img.shape[:2]
    left, right, top, bottom = box
    return img[int(top * h):int(bottom * h), int(left * w):int(right * w)]


def load_cropped_photos(dir):
    """ Load, EXIF-orient, and crop each photo. Returns the cropped image arrays. """
    crops = []
    for fname, box in PHOTOS:
        img = np.asarray(ImageOps.exif_transpose(Image.open(path.join(dir, fname))))
        crops.append(crop_photo(img, box))
    return crops


def plot_photos(axes, crops):
    """ Plot the cropped phantom photographs. """
    for ax, crop in zip(axes.flat, crops):
        ax.imshow(crop)
        ax.set_aspect('equal')
        remove_ticks(ax)


def draw_line_pair_labels(ax, n_images, row_key, draw_boxes=False):
    """ Draw the line-pair width labels on every column of a concatenated axial row.
    
    If draw_boxes, the LINE_PAIR_BOXES are drawn on every column too.
    """
    x0 = ROI['y'][0]                      # absolute image-y -> local horizontal
    y0 = ROI['x'][0]                      # absolute image-x -> local vertical
    col_w = ROI['y'][1] - ROI['y'][0]     # width of one column in the concatenation
    for col in range(n_images):
        col_shift = col * (col_w + SEP_PX)
        for a in LINE_PAIR_LABELS:
            ax.text(a['x'] - x0 + col_shift, a['y'] - y0, a['s'], color=a['color'][row_key][col],
                    ha='left', va='center', fontsize=SMALLER_SIZE, fontweight='bold')
        if not draw_boxes:
            continue
        for b in LINE_PAIR_BOXES:
            ax.add_patch(Rectangle(
                (b['x'] - x0 + col_shift, b['y'] - y0), b['w'], b['h'],
                fill=False, edgecolor=b['color'][col], linewidth=1,
                linestyle=b['linestyle']))



def concat_row(images, sep_px=SEP_PX, vmax_pct=None):
    """ Concatenate a row's images horizontally.
    
    A thin black gap separates the columns. If vmax_pct is given, each column is normalized to its
    OWN vmax_pct percentile before concatenation, so every column uses its full dynamic range.
    """
    sep = np.zeros((images[0].shape[0], sep_px))
    parts = []
    for i, im in enumerate(images):
        if i:
            parts.append(sep)
        col = np.abs(im)
        if vmax_pct is not None:
            col = col / np.percentile(col, vmax_pct)
        parts.append(col)
    return np.concatenate(parts, axis=1)


def plot_slices(axes, bin_images, msi_images, h_label, row_labels=True, col_titles=True,
                vmax_scale=(1.0, 1.0), annotate=False, cmap=CMAP['image'], vmax_pct=CONFIGS[1]['vmax_pct']):
    """ Plot the phantom slices as two rows, each a single image formed by concatenating the three columns
    horizontally.

    Each column is normalized to its own vmax_pct percentile so every column uses its full dynamic range
    and reads at comparable brightness; without this the lower-signal plastic replica renders dark against
    the brighter metal columns. The trade-off is that absolute brightness is no longer comparable across
    columns.
    """
    for ax, images, scale, row_key in ((axes[0], bin_images, vmax_scale[0], 'bin'),
                                       (axes[1], msi_images, vmax_scale[1], 'msi')):
        row = concat_row(images, vmax_pct=vmax_pct)
        ax.imshow(row, cmap=cmap, vmin=0, vmax=scale)
        ax.set_aspect('equal')
        remove_ticks(ax)
        if annotate:
            # boxes only on the msi (All Spectral Bins) row, not the single-bin row
            draw_line_pair_labels(ax, len(images), row_key, draw_boxes=(row_key == 'msi'))
        # column titles centered over each column of the concatenated row
        if images is bin_images and col_titles:
            offset = 0
            for (label, _, _), im in zip(COLUMNS, images):
                w = im.shape[1]
                ax.text(offset + w / 2, 1.02, label, transform=ax.get_xaxis_transform(),
                        ha='center', va='bottom')
                offset += w + SEP_PX
    if row_labels:
        axes[0].set_ylabel('One Spectral Bin')
        axes[1].set_ylabel('All Spectral Bins')
    # direction glyph in the first column of both rows
    for ax in axes:
        label_encode_dirs(ax, loc='bottom-left-imshow', x_label=h_label, y_label='x',
                          offset=0.05, color='white')


p = argparse.ArgumentParser(description='Make figure 1')
p.add_argument('data_dir', type=str, help='path to root of "score-data" directory')
p.add_argument('save_dir', type=str, help='path where figure is saved')
p.add_argument('-s', '--slice', type=int, default=None,
               help='z slice index, selects the axial x-y plane in B (defaults to config value)')
p.add_argument('--sag_slice', type=int, default=None,
               help='y slice index, selects the sagittal x-z reformat in C (defaults to config value)')
p.add_argument('-b', '--bin', type=int, default=None,
               help="bin index for single-bin data (defaults to config value)")
p.add_argument('--inplane_vmax', type=float, nargs=2, default=CONFIGS[1]['inplane_vmax'],
               help='vmax (display clip) for B rows (center-bin, all-bins); <1 brightens, >1 darkens')
p.add_argument('--reformat_vmax', type=float, nargs=2, default=CONFIGS[1]['reformat_vmax'],
               help='vmax (display clip) for C rows (center-bin, all-bins); <1 brightens, >1 darkens')
p.add_argument('-p', '--plot', action='store_true', help='show plots')

if __name__ == '__main__':

    args = p.parse_args()
    makedirs(args.save_dir, exist_ok=True)
    case_dir = path.join(args.data_dir, CONFIGS[1]['case_dir'])
    photo_dir = path.join(args.data_dir, CONFIGS[1]['photo_dir'])

    # Resolve slice and bin defaults

    ref = path.join(case_dir, COLUMNS[0][1], COLUMNS[0][2], 'bin', 'im_post')
    dims = read_dims(ref)
    slc = args.slice if args.slice is not None else CONFIGS[1]['z_pos']
    sag = args.sag_slice if args.sag_slice is not None else CONFIGS[1]['y_pos'] * UP
    bin = args.bin if args.bin is not None else CONFIGS[1]['bin']

    # Load data: for B (axial x-y) and C (sagittal x-z), one single-bin image (top row) and
    # one combined msi slice (bottom row) per column.

    bin_axi, msi_axi, bin_sag, msi_sag = [], [], [], []
    for label, scan, view in COLUMNS:
        base = path.join(case_dir, scan, view)
        bin_path = path.join(base, 'bin', 'im_post')
        msi = path.join(base, 'msi', 'im_post')
        bin_axi.append(load_cfl_slice(bin_path, slc, plane='axial', bin=bin))
        msi_axi.append(load_cfl_slice(msi, slc, plane='axial'))
        bin_sag.append(load_cfl_slice(bin_path, sag, plane='sagittal', bin=bin))
        msi_sag.append(load_cfl_slice(msi, sag, plane='sagittal'))

    # Create subfigure layout

    fig = plt.figure(figsize=(FIG_WIDTH[2], FIG_WIDTH[2] * 0.6))
    subfigs = fig.subfigures(1, 3, width_ratios=[0.4, 1.0, 0.2], wspace=0.02)
    subfig_A, subfig_B, subfig_C = subfigs

    # Subfigure A: photographs stacked vertically with no vertical gap.

    crops = load_cropped_photos(photo_dir)
    height_ratios = [c.shape[0] / c.shape[1] for c in crops]
    axes_A = subfig_A.subplots(len(PHOTOS), 1,
                               gridspec_kw={'left': 0.05, 'right': 0.95, 'bottom': 0.03,
                                            'top': 0.9, 'hspace': 0.0,
                                            'height_ratios': height_ratios})
    plot_photos(axes_A, crops)
    subfig_A.text(0.5, 0.92, 'Hip Implant\nin Gyroid Lattice', ha='center', va='bottom',
                  multialignment='center')

    # Subfigure B: 2x3 grid of axial (x-y) slices

    axes_B = subfig_B.subplots(2, 1,
                               gridspec_kw={'left': 0.05, 'right': 0.98, 'bottom': 0.03,
                                            'top': 0.9, 'hspace': 0.08})
    plot_slices(axes_B, bin_axi, msi_axi, h_label='y', vmax_scale=args.inplane_vmax, annotate=True)

    # Subfigure C: 2x3 grid of sagittal (x-z) reformats

    axes_C = subfig_C.subplots(2, 1,
                               gridspec_kw={'left': 0.02, 'right': 0.98, 'bottom': 0.03,
                                            'top': 0.9, 'hspace': 0.08})
    plot_slices(axes_C, bin_sag, msi_sag, h_label='z', row_labels=False, col_titles=False, vmax_scale=args.reformat_vmax)
    subfig_C.text(0.5, 0.92, 'Reformat', ha='center', va='bottom')

    # Label and color panels

    color_panels([subfig_A, subfig_B, subfig_C])
    label_panels([subfig_A, subfig_B, subfig_C])

    # Produce figure

    plt.savefig(path.join(args.save_dir, 'figure1.png'), dpi=DPI)
    plt.savefig(path.join(args.save_dir, 'figure1.pdf'), dpi=DPI)
    if args.plot:
        plt.show()
