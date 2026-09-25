""" Support functions for plotting results figures (5-7)
"""

import cfl
import matplotlib.lines as mlines
import matplotlib.patches as patches
import numpy as np

from os import path

from params import *
from plot import label_encode_dirs, remove_ticks, color_panels, label_panels

def read_cfl_bin(name, bin):
    ''' Read a single bin from a cfl without loading the other bins.
    
    Last (slowest-varying) dimension is the bin axis. cfl data is column-major, so each
    bin occupies one contiguous chunk; we seek to it and read only that chunk.
    Returns the spatial volume with the (singleton) bin axis dropped.
    '''
    with open(name + ".hdr", "rt") as h:
        h.readline()  # skip '# Dimensions'
        dims = [int(i) for i in h.readline().split()]
    n = int(np.prod(dims))
    dims = dims[:np.searchsorted(np.cumprod(dims), n) + 1]  # drop trailing singletons
    nbins = dims[-1]
    if not 0 <= bin < nbins:
        raise IndexError(f'bin {bin} out of range for last dimension of size {nbins} in {name}')
    spatial_dims = dims[:-1]
    chunk = int(np.prod(spatial_dims))  # voxels per bin
    itemsize = np.dtype(np.complex64).itemsize
    with open(name + ".cfl", "rb") as d:
        d.seek(bin * chunk * itemsize)
        a = np.fromfile(d, dtype=np.complex64, count=chunk)
    return a.reshape(spatial_dims, order='F')

def load_score_data(data_dir, seq_name, stack=True, bin=None):
    ''' Load the four SCORE options for a given sequence.
    
    If bin is given, read only that bin from the last (bin) dimension of each cfl,
    avoiding the cost of loading all bins (e.g. seq_name='bin' data has 24 bins and
    is ~25x larger than a single bin).
    '''
    image_paths = []
    for gz in ['gz-off', 'gz-on']:
        for view in ['unsheared', 'sheared']:
            image_path = path.join(data_dir, gz, view, seq_name, 'im_post')
            image_paths.append(image_path)
    if bin is None:
        images = [cfl.readcfl(p) for p in image_paths]
    else:
        images = [read_cfl_bin(p, bin) for p in image_paths]
    if stack:
         images = np.stack(images, axis=0)
    return images

def plot_score_images(axes, images, cmap=CMAP['image'], aspect='equal', title_size=LARGE_SIZE, draw_labels=True, vmax=1, vmax_pct=None):
    ''' Plot the four SCORE options in image space.

    If vmax_pct is given, each panel is normalized to its OWN vmax_pct percentile
    before display (so every panel uses its full dynamic range, matching figure4's
    concat_row); vmax is then the display clip point on that normalized image
    (figure4 uses 1.5). Otherwise the images are shown as-is with the shared vmax.
    '''
    for ax, im in zip(axes.flat, images):
        mag = np.abs(im)
        if vmax_pct is not None:
            mag = mag / np.percentile(mag, vmax_pct)
        ax.imshow(mag, cmap=cmap, vmin=0, vmax=vmax)
        ax.set_aspect(aspect)
        remove_ticks(ax)
    if draw_labels:
        # vertical row labels (rotation=90), offset well left into the gutter so
        # they read as spanning the whole row rather than just the top/bottom panel
        axes[0, 0].set_ylabel(r'$G_z$-Off' + '\nAcquisition', fontsize=title_size, labelpad=15,
                              rotation=90, ha='center', va='center', multialignment='center')
        axes[1, 0].set_ylabel(r'$G_z$-On' + '\nAcquisition', fontsize=title_size, labelpad=15,
                              rotation=90, ha='center', va='center', multialignment='center')
        # column titles offset well above so they read as spanning the whole column
        axes[0, 0].set_title('Unsheared View', fontsize=title_size, pad=15)
        axes[0, 1].set_title('Sheared View', fontsize=title_size, pad=15)

def get_slice_from_rect(rect):
    ''' Build (x, y) slices from a roi.
    
    Accepts a 4-value rect (x_start, y_start, x_size, y_size) or
    a 6-value box (x_start, y_start, z_start, x_size, y_size, z_size).
    '''
    if len(rect) == 6:
        return (slice(rect[0], rect[0] + rect[3]), slice(rect[1], rect[1] + rect[4]))
    return (slice(rect[0], rect[0] + rect[2]), slice(rect[1], rect[1] + rect[3]))

def draw_reference_line(ax, x, color='white', linewidth=0.5, linestyle=(0, (6, 14))):
    ''' Draw a thin vertical reference line '''
    ax.axvline(x, color=color, linewidth=linewidth, linestyle=linestyle)

def draw_table_grid(subfig, axes, color='black', linewidth=2, gap=0.015,
                    overhang=0.0):
    ''' Draw the two interior table dividers for a 2x2 block of axes
    
    Positions come from the rendered IMAGE extents (not the axes cell), so the dividers
    track the images even though set_aspect shrinks each axes within its gridspec cell.
    Forces a draw so positions are final; call after the axes are created.
    '''
    fig = subfig.get_figure()
    fig.canvas.draw()  # finalize layout so image window extents are correct
    inv = subfig.transSubfigure.inverted()

    def img_box(ax):
        # tight bbox of the displayed image in subfigure-fraction coords
        bb = ax.images[0].get_window_extent() if ax.images else ax.get_window_extent()
        return inv.transform_bbox(bb)

    box = [[img_box(axes[i, j]) for j in range(2)] for i in range(2)]
    x_left = min(box[0][0].x0, box[1][0].x0) - gap
    x_right = max(box[0][1].x1, box[1][1].x1) + gap
    y_bottom = min(box[1][0].y0, box[1][1].y0) - gap
    y_top = max(box[0][0].y1, box[0][1].y1) + gap
    x_mid = 0.5 * (box[0][0].x1 + box[0][1].x0)  # between the two columns
    y_mid = 0.5 * (box[1][0].y1 + box[0][0].y0)  # between the two rows
    line_kw = dict(color=color, linewidth=linewidth, transform=subfig.transSubfigure,
                   clip_on=False, zorder=5)
    subfig.add_artist(mlines.Line2D([x_mid, x_mid], [y_bottom - overhang, y_top + overhang], **line_kw))  # column divider
    subfig.add_artist(mlines.Line2D([x_left - overhang, x_right + overhang], [y_mid, y_mid], **line_kw))  # row divider

def draw_annotations(ax, annotations, roi, fontsize=SMALL_SIZE, types=None, panel=None):
    ''' Draw annotation overlays on an in-plane image axis.
    
    Annotation coordinates are ABSOLUTE image pixels (roi-independent); the roi offset
    is subtracted here on the fly to map into the cropped axis, so the same list works
    for any roi.

    Each annotation is a dict:
      {'type': 'text', 'x':, 'y':, 's':, 'color': (default 'white'), 'ha', 'va'}
      {'type': 'box',  'x':, 'y':, 'w':, 'h':, 'color': (default 'red'),
                       'linewidth': (default 1), 'linestyle': (default 'solid')}

    An annotation's `'color'` may be a single color (used on all panels) or a sequence of
    four colors (one per panel).
    '''
    if not annotations:
        return
    x0, y0 = roi[1], roi[0]  # absolute->local offset for (matplotlib-x, matplotlib-y)

    def pick_color(a, default):
        color = a.get('color', default)
        # a length-4 sequence of non-numbers is a per-panel color list (vs an RGBA tuple)
        if (panel is not None and not isinstance(color, str) and len(color) == 4
                and not all(isinstance(c, (int, float)) for c in color)):
            return color[panel]
        return color

    for a in annotations:
        if types is not None and a['type'] not in types:
            continue
        if a['type'] == 'text':
            ax.text(a['x'] - x0, a['y'] - y0, a['s'], color=pick_color(a, 'white'),
                    ha=a.get('ha', 'left'), va=a.get('va', 'center'),
                    fontsize=a.get('fontsize', fontsize),
                    fontweight=a.get('fontweight', 'normal'))
        elif a['type'] == 'box':
            ax.add_patch(patches.Rectangle(
                (a['x'] - x0, a['y'] - y0), a['w'], a['h'],
                fill=False, edgecolor=pick_color(a, 'red'),
                linewidth=a.get('linewidth', 1),
                linestyle=a.get('linestyle', 'solid')))

def plot_results_two_panel(subfigs, image, roi, z, y, res, gridspec_kw, draw_panels=True, annotations=None, conventional_label_y=0.04, reformat_vmax=1, reformat_vmax_pct=None, inplane_vmax=1, inplane_vmax_pct=None):
    ''' Plot two planes for a results image (in-plane and reformat).'''

    if isinstance(gridspec_kw, dict):
        gridspec_kw = (gridspec_kw, gridspec_kw)
    gks_A, gks_B = gridspec_kw

    # roi may be a 4-value rect (crops x, y) or a 6-value box (also crops z in
    # the reformat panel): (x_start, y_start, z_start, x_size, y_size, z_size).
    z_slc = slice(roi[2], roi[2] + roi[5]) if len(roi) == 6 else slice(None)
    z_offset = roi[2] if len(roi) == 6 else 0
    roi_slc = (slice(None),) + get_slice_from_rect(roi) + (slice(z, z + 1),)
    x_size = roi[3] if len(roi) == 6 else roi[2]
    reformat_slc = (slice(None), slice(roi[0], roi[0] + x_size), slice(y, y + 1), z_slc)

    # (A) in-plane image
    axes = subfigs[0].subplots(2, 2, gridspec_kw=gks_A)
    im = image[roi_slc]
    plot_score_images(axes, im, aspect=res[0]/res[1], vmax=inplane_vmax, vmax_pct=inplane_vmax_pct)
    for panel, ax in enumerate(axes.flat):
        # draw_reference_line(ax, y - roi[1]) # marks where the reformat slice cuts
        draw_annotations(ax, annotations, roi, panel=panel) # width labels + boxes (per-panel colors)
    label_encode_dirs(axes[0, 0], loc='top-left', x_label='y', y_label='x', offset=0.07, color='white', size=MEDIUM_SIZE)
    # label the top-left and bottom-right panels as the conventional acquisitions
    axes[0, 0].text(0.5, conventional_label_y, '(Conventional)', transform=axes[0, 0].transAxes,
                    ha='center', va='bottom', color='white', fontsize=MEDIUM_SIZE)
    axes[1, 1].text(0.5, conventional_label_y, '(Conventional VAT)', transform=axes[1, 1].transAxes,
                    ha='center', va='bottom', color='white', fontsize=MEDIUM_SIZE)
    # subfigs[0].text(0.5, 0.958, "In-plane", ha='center', fontsize=MEDIUM_SIZE)
    axes_A = axes

    # (B) slice reformat (row/col labels shown only on panel A; the offset Standard/VAT
    # and Unsheared/Sheared headers there read as spanning the whole row/column)
    axes = subfigs[1].subplots(2, 2, gridspec_kw=gks_B)
    im = np.squeeze(image[reformat_slc])
    plot_score_images(axes, im, aspect=res[0]/res[2], draw_labels=False, vmax=reformat_vmax, vmax_pct=reformat_vmax_pct)
    # for ax in axes.flat:
        # draw_reference_line(ax, z - z_offset) # marks where the in-plane slice cuts
    label_encode_dirs(axes[0, 0], loc='top-left', x_label='z', y_label='x', offset=0.07, color='white', size=MEDIUM_SIZE)
    subfigs[1].text(0.5, 0.965, "Reformat", ha='center', fontsize=LARGE_SIZE)

    # the two interior dividers split each 2x2 block, reinforcing the spanning headers
    draw_table_grid(subfigs[0], axes_A)
    draw_table_grid(subfigs[1], axes)

    if draw_panels:
        color_panels(subfigs.ravel())
        label_panels(subfigs.ravel())
