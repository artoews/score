""" Utility functions for manipulating k-space and image data. """

import numpy as np
import sigpy as sp
from typing import Optional

from sequence import Dim

def embed_kspace(
        ksp_samples: np.ndarray,
        pat: np.ndarray
        ) -> np.ndarray:
    ''' Embed k-space samples into full-size k-space array based on sampling pattern.

    Args:
        ksp_samples: (kx, kyz, 1, c, 1, b)
        pat: (1, ky, kz)
    
    Returns:
        ksp_full: (kx, ky, kz, c, 1, b)
    '''
    nx, _, _, nc, nm, nb = ksp_samples.shape
    assert nm == 1, "Expected singleton dimension but got {}".format(nm)
    ny, nz = pat.shape[1:]
    ksp_full = np.zeros((nx, ny, nz, nc, 1, nb), dtype=np.complex64)
    ksp_full[:, pat[0], :, :, :] = ksp_samples[:, :, 0, :, :, :]
    return ksp_full

def sample_kspace(
        ksp: np.ndarray,
        traj: np.ndarray,
        pat: np.ndarray
        ) -> tuple[np.ndarray, np.ndarray]:
    ''' Vectorize k-space data according to the BART non-Cartesian format.

    Args:
        ksp: (kx, ky, kz, c, 1, b)
        traj: (3, kx, kyz, 1, 1, 1)
        pat: (1, ky, kz)
    
    Returns:
        ksp_samples: (1, kx, kyz, c, 1, b)
        traj_samples: (3, kx, kyz, 1, 1, 1)
    
    '''
    shape = ksp.shape
    ksp = ksp[:, pat[0], ...] # select sampled data and flatten Y-Z
    ksp = ksp[None, :]
    traj = traj[:, :, pat[0], ...]
    traj = np.reshape(traj, (3, shape[0], -1, 1, 1, 1)).astype(np.complex64)
    return ksp, traj

def crop_kspace(
        ksp: np.ndarray,
        traj: np.ndarray,
        ax: int,
        fov_mm: float,
        res_mm: float,
        eps: float = 1e-3
        ) -> tuple[np.ndarray, np.ndarray]:
    ''' Crop k-space to the specified resolution along ax.
    
    Note: a necessary consequence of this operation is that the X & YZ dimensions are collapsed.
    This happens because you are masking out partial segments of readout lines.
    '''
    limit = fov_mm / 2 / res_mm
    mask = np.logical_and(traj[ax] >= -limit * (1 + eps),
                          traj[ax] < limit * (1 + eps)) 
    mask = np.squeeze(mask) # (ky, kz)
    nc, nm, nb = ksp.shape[Dim.C:]
    ksp = ksp[:, mask, ...].reshape((1, -1, 1, nc, nm, nb))
    traj = traj[:, mask].reshape((3, -1, 1, 1, 1, 1))
    return ksp, traj

def interpolate_image(
        im: np.ndarray,
        shape: tuple[int],
        fft_axes: Optional[tuple] = None
        ) -> np.ndarray:
    ''' Returns a sinc-interpolated image to shape. '''
    k = sp.fft(im, axes=fft_axes)
    k = sp.resize(k, shape)
    im = sp.ifft(k, axes=fft_axes)
    return im

def fermi_1d(
        im: np.ndarray,
        dim: int,
        cutoff: Optional[float] = None,
        width: Optional[float] = None
        ) -> tuple[np.ndarray, np.ndarray]:
    ''' Apply a 1D Fermi filter along the specified dimension. '''
    n = im.shape[dim]
    if cutoff is None:
        cutoff = n / 2 * 0.8
    if width is None:
        width = n / 2 * 0.1
    x = np.arange(-n//2, n//2)
    window = 1 / (1 + np.exp((np.abs(x) - cutoff) / width))
    shape = [1] * im.ndim
    shape[dim] = n
    window = np.reshape(window, shape) # reshape for broadcasting
    im = im * window
    return im, window

def fermi_nd(
        im: np.ndarray,
        cutoffs: Optional[list[float]] = None,
        widths: Optional[list[float]] = None,
        dft: bool = False
        ) -> np.ndarray:
    ''' Apply a Fermi filter along all dimensions. '''
    if dft:
        im = sp.fft(im)
    for dim in range(im.ndim):
        cutoff = cutoffs[dim] if cutoffs is not None else None
        width = widths[dim] if widths is not None else None
        im, _ = fermi_1d(im, dim, cutoff=cutoff, width=width)
    if dft:
        im = sp.ifft(im)
    return im