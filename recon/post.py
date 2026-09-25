''' Image post-processing operations to follow reconstruction by recon.py. '''
import argparse
import cfl
import numpy as np
import sigpy as sp
from os import path

from sequence import Seq, Dim
from utils import interpolate_image, fermi_nd

def atleast_nd(
        x: np.ndarray,
        ndim: int
        ) -> np.ndarray:
    """ Adds trailing singleton dimensions until x.ndim == ndim. """
    if x.ndim > ndim:
        raise ValueError("Array already has more than {} dimensions".format(ndim))
    return x.reshape(x.shape + (1,) * (ndim - x.ndim))

def correct_geometry(
        im: np.ndarray,
        corners: tuple,
        gradient_model: str='HRMW',
        fovScalingParams: dict={'FrequencyPixelScaling': 1.0, 'PhasePixelScaling': 1.0}
        ) -> np.ndarray:
    """ Apply gradient non-linearity correction to one spectral bin (one image volume). Requires proprietary SDK from GE. """
    from GERecon import Gradwarp
    init_shape = im.shape
    pad_shape = (np.max(init_shape[:Dim.Z]),) * 2 + init_shape[Dim.Z:] # for padding x-y image to a square shape
    im = sp.resize(np.abs(im), pad_shape).astype(np.float32) # pre-processing for GE functions
    gradwarp = Gradwarp()
    im_xyz = im.squeeze()
    im_xyz = gradwarp.Execute3D(im_xyz, tuple(corners), fovScalingParams=fovScalingParams, gradient=gradient_model)
    im[:, :, :, 0, 0, 0] = im_xyz
    im = sp.resize(im, init_shape[:Dim.C] + im.shape[Dim.C:])
    return im

def interpolate_z(
        im: np.ndarray,
        seq: Seq
        ) -> np.ndarray:
    """ Interpolate slice dimension to match readout (x) dimension. """
    new_z_shape = int(im.shape[Dim.Z] * seq.xyz_resolution_mm[Dim.Z] / seq.xyz_resolution_mm[Dim.X])
    new_shape = im.shape[:Dim.Z] + (new_z_shape,) + im.shape[Dim.Z+1:]
    im = interpolate_image(im, new_shape, fft_axes=(Dim.Z,))
    return im

def interpolate_xy(
        im: np.ndarray,
        factor: int=2
        ) -> np.ndarray:
    """ Interpolate x & y dimensions. """
    new_shape = (im.shape[Dim.X] * factor, im.shape[Dim.Y] * factor) + im.shape[Dim.Z:]
    im = interpolate_image(im, new_shape, fft_axes=(Dim.X, Dim.Y))
    return im

p = argparse.ArgumentParser(description="Image post-processing to follow recon.py")
p.add_argument("root", type=str, help="Directory where outputs from recon.py were saved.")
p.add_argument("--iso", action="store_true", help="Interpolate final image volumes to isotropic resolution (in x-z).")
p.add_argument("--up", action="store_true", help="2x upsampling applied to x&y dimensions of output images.")
p.add_argument("--window", action="store_true", help="Apply Fermi window to DFT data before interpolation.")
p.add_argument("--no_ge", action="store_true", help="Use if GE's proprietary SDK is not installed. Skips gradient non-linearity correction.")

if __name__ == '__main__':

    args = p.parse_args()
    seq = Seq.from_yaml(path.join(args.root, 'seq.yml'))

    image_files = []
    post_image_files = []
    for view in ('unsheared', 'sheared'):
        for option in ('bin', 'msi'):
            image_file = path.join(args.root, view, option, 'im')
            post_file = path.join(args.root, view, option, 'im_post')
            image_files.append(image_file)
            post_image_files.append(post_file)

    def process(im):
        im = fermi_nd(im, dft=True) if args.window else im
        im = interpolate_z(im, seq) if args.iso else im
        im = interpolate_xy(im) if args.up else im
        im = atleast_nd(im, 6)
        if not args.no_ge:
            im = correct_geometry(im, tuple(seq.corners))
        im = np.flip(im, axis=Dim.X)
        return im

    for file, post_file in zip(image_files, post_image_files):
        im = cfl.readcfl(file)
        im = im[:, :, :, :, :1] # use first espirit map-derived image
        if im.ndim > Dim.B:
            # process one bin at a time to limit peak memory during interpolation/correction
            bins = [process(im[..., b:b+1]) for b in range(im.shape[Dim.B])]
            im = np.concatenate(bins, axis=Dim.B)
        else:
            im = process(im)
        cfl.writecfl(post_file, im)
