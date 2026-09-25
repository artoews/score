"""Per-figure defaults and annotations for use by make_results_figure.py and figure1.py.

"""

from os import path

REPO_ROOT = path.join(path.dirname(path.abspath(__file__)), '..')

CONFIGS = {

    1: dict(
        case_dir='phantom-scan',
        photo_dir='phantom-photos',
        roi=[30, 85, 6, 345, 260, 70],
        z_pos=41,
        y_pos=240,
        bin=12,
        up=2,
        vmax_pct=99.5,
        inplane_vmax=[1.5, 1.5], # [bin_row, msi_row]
        reformat_vmax=[1.5, 1.5], # [bin_row, msi_row]
        # Coordinates are ABSOLUTE upsampled image pixels:
        # 'x' is the horizontal (image-y) anchor,
        # 'y' is the vertical (image-x) anchor (top-left corner, for boxes)
        annotations=[
            {'type': 'text', 'x': 338, 'y': 568, 's': '0.8', 'color': {'bin': ['cyan', 'red', 'red'], 'msi': ['cyan', 'red', 'red']}},
            {'type': 'text', 'x': 338, 'y': 600, 's': '1.0', 'color': {'bin': ['cyan', 'red', 'red'], 'msi': ['cyan', 'red', 'red']}},
            {'type': 'text', 'x': 338, 'y': 632, 's': '1.2', 'color': {'bin': ['cyan', 'cyan', 'cyan'], 'msi': ['cyan', 'red', 'red']}},
            {'type': 'text', 'x': 338, 'y': 664, 's': '1.4', 'color': {'bin': ['cyan', 'cyan', 'cyan'], 'msi': ['cyan', 'cyan', 'cyan']}},
            {'type': 'box', 'x': 395, 'y': 360, 'w': 110, 'h': 70, 'color': ['red', 'cyan', 'cyan'], 'linestyle': 'dashed'},
            {'type': 'box', 'x': 512, 'y': 360, 'w': 110, 'h': 70, 'color': ['cyan', 'red', 'red'], 'linestyle': 'solid'},
        ],
    ),

    5: dict(
        case_dir='phantom-scan',
        flip=False,
        fov=[410, 344, 72],
        roi=[30, 85, 6, 345, 260, 70],
        z_pos=41,
        y_pos=240,
        bin=12,
        up=2,
        bin_scale=1.7,
        inplane_vmax=1.5,
        reformat_vmax=1.5,
        vmax_pct=99.5,
        norm_scale=4,
        width_ratios=[3, 1],
        fig_height_scale=0.95,
        annotations=[
            {'type': 'text', 'x': 345, 'y': 570, 's': '0.8', 'color': ['cyan', 'red', 'red', 'red'], 'fontweight': 'bold'},
            {'type': 'text', 'x': 345, 'y': 600, 's': '1.0', 'color': ['cyan', 'red', 'red', 'red'], 'fontweight': 'bold'},
            {'type': 'text', 'x': 345, 'y': 630, 's': '1.2', 'color': ['cyan', 'red', 'cyan', 'red'], 'fontweight': 'bold'},
            {'type': 'text', 'x': 345, 'y': 660, 's': '1.4', 'color': ['cyan', 'cyan', 'cyan', 'cyan'], 'fontweight': 'bold'},
            {'type': 'box', 'x': 395, 'y': 360, 'w': 110, 'h': 70, 'color': ['red', 'cyan', 'red', 'cyan'], 'linestyle': 'dashed'},
            {'type': 'box', 'x': 512, 'y': 360, 'w': 110, 'h': 70, 'color': ['cyan', 'red', 'cyan', 'red'], 'linestyle': 'solid'},
        ],
    ),

    6: dict(
        case_dir='spine-scan',
        flip=True,
        fov=[410, 267.46, 72],
        roi=[150, 75, 6, 250, 200, 76],
        z_pos=45,
        y_pos=171,
        bin=12,
        up=2,
        bin_scale=2,
        inplane_vmax=1,
        reformat_vmax=1,
        vmax_pct=None,
        norm_scale=4,
        width_ratios=[2.5, 1],
        fig_height_scale=0.85,
        annotations=[
            {'type': 'box', 'x': 315, 'y': 570, 'w': 80, 'h': 90, 'color': ['red', 'cyan', 'red', 'cyan'], 'linestyle': 'dashed'},
            {'type': 'box', 'x': 305, 'y': 475, 'w': 80, 'h': 90, 'color': ['cyan', 'red', 'cyan', 'red'], 'linestyle': 'solid'},
        ],
    ),

    7: dict(
        case_dir='hip-scan',
        flip=False,
        fov=[410, 410, 72],
        roi=[60, 170, 300, 250],
        z_pos=38,
        y_pos=163,
        bin=10,
        up=2,
        bin_scale=2,
        inplane_vmax=1,
        reformat_vmax=1,
        vmax_pct=None,
        norm_scale=5,
        width_ratios=[2.8, 1],
        fig_height_scale=0.8,
        annotations=[
            {'type': 'box', 'x': 620, 'y': 415, 'w': 155, 'h': 150, 'color': ['red', 'cyan', 'red', 'cyan'], 'linestyle': 'dashed'},
            {'type': 'box', 'x': 425, 'y': 140, 'w': 155, 'h': 60, 'color': ['cyan', 'red', 'cyan', 'red'], 'linestyle': 'solid'},
        ],
    ),

}
