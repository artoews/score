import numpy as np
import matplotlib.pyplot as plt
from string import ascii_uppercase
import matplotlib.transforms as mtransforms
import matplotlib.patheffects as pe

from params import *

def color_panels(subfigs):
    """ Shade the background of each subfigure. """
    for panel in subfigs:
         panel.set_facecolor('0.9')

def label_panels(subfigs, trans_x=0.035, trans_y=-0.13):
    """ Annotate each subfigure with a letter. """
    labels = ('({})'.format(letter) for letter in ascii_uppercase[:len(subfigs)])
    for label, subfig in zip(labels, subfigs):
        trans = mtransforms.ScaledTranslation(trans_x, trans_y, subfig.dpi_scale_trans)
        plt.text(0, 1, label, transform=subfig.transSubfigure + trans)
    
def remove_ticks(ax):
    """ Remove ticks from x and y axes. """
    if type(ax) is np.ndarray:
        for a in ax.flat: 
            remove_ticks(a)
    else:
        ax.set_xticks([])
        ax.set_yticks([])

def label_slice_pos(ax, dir, slc1, slc2, height=0.05, left=True, right=False, inside=True, label=None, color='white'):
    """ Annotate the position of one slice (slc1) in the plot of a another slice (slc2). Slices must be in different planes. """
    if slc2[dir].start is not None:
        pos = slc1[dir] - slc2[dir].start
    else:
        pos = slc1[dir]
    if inside:
        if right:
            ax.plot([1, 1-height], [pos, pos], color=color, linewidth=1, linestyle='solid', transform=ax.get_yaxis_transform())
        if left:
            ax.plot([0, height], [pos, pos], color=color, linewidth=1, linestyle='solid', transform=ax.get_yaxis_transform())
            if label is not None:
                ax.annotate(label, (slc1[0].stop - slc1[0].start-7, pos), ha='center', va='bottom', color='black', fontsize=SMALL_SIZE)
    else:
        ax.set_yticks([pos])
        ax.set_yticklabels([""])
        ax.tick_params(axis="y", left=left, right=right)
    return pos

def label_encode_dirs(ax, offset=0.05, length=0.15, color='black', x_label='y', y_label='x', loc='top-left', buffer_text=False, size=SMALL_SIZE, x_anchor=None, y_anchor=None):
    """ Add coordinate axes to corner of plot. `x_anchor`/`y_anchor`, if given, override
    the x/y data coordinate the glyph is anchored to (only supported by loc='top-left-
    plot'); use them to place the glyph's vertex at an arbitrary data position instead of
    the plot's top-left corner. """
    if buffer_text:
        buffer = [pe.withStroke(linewidth=0.7, foreground="white")]
    else:
        buffer = None
    if loc == 'top-left':
        connectionstyle="angle,angleA=180,angleB=-90,rad=0"
        x1, y1 = offset, -offset - length
        x2, y2 = offset + length, -offset
        y_verticalalignment = 'top'
        x_horizontalalignment = 'left'
        transform = ax.get_figure().dpi_scale_trans + mtransforms.ScaledTranslation(0, 0, ax.transData)
    elif loc == 'bottom-right':
        connectionstyle="angle,angleA=180,angleB=-90,rad=0"
        xlim = np.max(ax.get_xlim())
        ylim = np.max(ax.get_ylim())
        x1, y1 = -offset, offset + length
        x2, y2 = -offset - length, offset
        y_verticalalignment = 'bottom'
        x_horizontalalignment = 'right'
        transform = ax.get_figure().dpi_scale_trans + mtransforms.ScaledTranslation(xlim, ylim, ax.transData)
    elif loc == 'bottom-left-imshow':
        connectionstyle="angle,angleA=180,angleB=-90,rad=0"
        xlim = np.min(ax.get_xlim())
        ylim = np.max(ax.get_ylim())
        x1, y1 = offset, offset + length
        x2, y2 = offset + length, offset
        y_verticalalignment = 'bottom'
        x_horizontalalignment = 'left'
        transform = ax.get_figure().dpi_scale_trans + mtransforms.ScaledTranslation(xlim, ylim, ax.transData)
    elif loc == 'bottom-left-plot':
        connectionstyle="angle,angleA=180,angleB=-90,rad=0"
        xlim = np.min(ax.get_xlim())
        ylim = np.min(ax.get_ylim())
        x1, y1 = offset, offset + length
        x2, y2 = offset + length, offset
        y_verticalalignment = 'bottom'
        x_horizontalalignment = 'left'
        transform = ax.get_figure().dpi_scale_trans + mtransforms.ScaledTranslation(xlim, ylim, ax.transData)
    elif loc == 'top-left-plot':
        # Same up (y) / right (x) arms as bottom-left-plot -- just anchored `length +
        # offset` (inches) below the top of the plot's y-range instead of at the bottom,
        # so the whole glyph sits just inside the top-left corner with z still pointing up.
        connectionstyle="angle,angleA=180,angleB=-90,rad=0"
        xlim = np.min(ax.get_xlim()) if x_anchor is None else x_anchor
        ylim = np.max(ax.get_ylim()) if y_anchor is None else y_anchor
        x1, y1 = offset, offset + length
        x2, y2 = offset + length, offset
        y_verticalalignment = 'bottom'
        x_horizontalalignment = 'left'
        transform = (ax.get_figure().dpi_scale_trans
                    + mtransforms.ScaledTranslation(0, -length - offset, ax.get_figure().dpi_scale_trans)
                    + mtransforms.ScaledTranslation(xlim, ylim, ax.transData))
    ax.text(x1, y1, y_label, verticalalignment=y_verticalalignment, horizontalalignment='center', size=size, weight='extra bold', color=color, path_effects=buffer, transform=transform)
    ax.text(x2, y2, x_label, verticalalignment='center', horizontalalignment=x_horizontalalignment, size=size, weight='extra bold', color=color, path_effects=buffer, transform=transform)
    ax.annotate("",
                xy=(x1, y1), xycoords=transform,
                xytext=(x2, y2), textcoords=transform,
                arrowprops=dict(arrowstyle="<->", color=color,
                                shrinkA=0, shrinkB=0,
                                patchA=None, patchB=None,
                                connectionstyle=connectionstyle,
                                ),
                )