''' Image reconstruction using SCORE. '''
import argparse
import cfl
import numpy as np
import subprocess
from bart import bart
from enum import IntEnum
from os import path, makedirs
from time import time

import utils
from sequence import Seq, Dim

class View(IntEnum):
    UNSHEARED = 0
    SHEARED = 1

def get_view(
        ksp: np.ndarray,
        seq: Seq,
        view: View,
        premod=True
        ) -> tuple[np.ndarray, np.ndarray]:
    """ Get k-space data for a SCORE view. """
    fov_mm = seq.field_of_view_mm(ksp.shape)
    traj = seq.trajectory(ksp.shape)
    z_centers_mm = np.array(seq.z_centers_mm)
    if seq.sampling == 'gz_on' and premod:
        ksp, _ = correct(ksp, traj, z_centers_mm, fov_mm, -seq.shear_factor)
    if view == View.SHEARED:
        ksp, traj = correct(ksp, traj, z_centers_mm, fov_mm, seq.shear_factor)
    return ksp, traj

def correct(
        ksp: np.ndarray,
        traj: np.ndarray,
        zs_mm: np.ndarray,
        fov_mm: np.ndarray,
        shear_factor: float,
        shear_ax: int=0,
        slice_ax: int=2
        ) -> tuple[np.ndarray, np.ndarray]:
    """ Apply SCORE correction to k-space data (Eq. 11 in the MRM article).

    Shapes of ksp[None, ...] and traj must be compatible for broadcasting.
    Traj must have units 1/fov per BART convention.
    """
    traj = traj.copy()
    ksp = ksp * np.exp(1j * 2 * np.pi * traj[shear_ax] / fov_mm[shear_ax] * zs_mm * shear_factor)
    traj[slice_ax] -= traj[shear_ax] * shear_factor * fov_mm[slice_ax] / fov_mm[shear_ax]
    return ksp, traj

p = argparse.ArgumentParser(description="Image reconstruction using SCORE. Unsheared and Sheared Views are derived from the same 3D-MSI dataset.")
p.add_argument("root", type=str, help="Directory containing exam data ksp.{cfl,hdr}, pat.{cfl, hdr}, sens.{cfl. hdr} and seq.yml.")
p.add_argument("--fft", action="store_true", help="Use regular FFT (vs NUFFT) for PICS where possible.")

if __name__ == "__main__":

    args = p.parse_args()

    # Prepare paths
    pics_path = path.join(path.dirname(__file__), 'pics.sh')
    ksp_path = path.join(args.root, 'ksp')
    pat_path = path.join(args.root, 'pat')
    sens_path = path.join(args.root, 'sens')
    seq_path = path.join(args.root, 'seq.yml')

    # Load exam data
    print('Loading exam data... ', end='')
    seq = Seq.from_yaml(seq_path)
    ksp = cfl.readcfl(ksp_path)
    pat = cfl.readcfl(pat_path).astype(bool)
    sens = cfl.readcfl(sens_path)
    print('Done.')

    # Reconstruct each SCORE view
    for view in View:

        print('RECONSTRUCTING {} VIEW'.format(view.name))

        # Prepare view-specific paths
        view_path = path.join(args.root, view.name.lower())
        ksp_path = path.join(view_path, 'ksp')
        traj_path = path.join(view_path, 'traj')
        bin_im_path = path.join(view_path, 'bin', 'im')
        msi_im_path = path.join(view_path, 'msi', 'im')
        makedirs(path.join(view_path, 'bin'), exist_ok=True)
        makedirs(path.join(view_path, 'msi'), exist_ok=True)

        print('-- Preparing input data (eq. 11)... ', end='')
        start = time()
        ksp_view, traj_view = get_view(ksp, seq, view)
        if seq.sampling == 'gz_off' and view == View.UNSHEARED:
            use_fft = args.fft
        elif seq.sampling == 'gz_on' and view == View.SHEARED:
            use_fft = args.fft
        else:
            use_fft = False
        if not use_fft:
            ksp_view, traj_view = utils.sample_kspace(ksp_view, traj_view, pat)
            # cfl.writecfl(ksp_path + '_nocrop' + view_suffix, ksp_view.reshape(1, -1, 1, ksp_view.shape[Dim.C], ksp_view.shape[Dim.B]))
            # cfl.writecfl(traj_path + '_nocrop' + view_suffix, traj_view.reshape(3, -1))
            fov_mm = seq.field_of_view_mm(ksp.shape)
            ksp_view, traj_view = utils.crop_kspace(ksp_view, traj_view, Dim.Z, fov_mm[Dim.Z], seq.xyz_resolution_mm[Dim.Z])
            cfl.writecfl(traj_path, traj_view)
        cfl.writecfl(ksp_path, ksp_view)
        end = time()
        print(f'Done. Elapsed time: {int(end - start)} seconds.')

        # PICS reconstruction
        print('-- Running PICS recon... ', end='')
        start = time()
        if use_fft:
            subprocess.run([pics_path, ksp_path, sens_path, bin_im_path], check=True)
        else:
            subprocess.run([pics_path, ksp_path, sens_path, bin_im_path, traj_path], check=True)
        end = time()
        print(f'Done. Elapsed time: {int(end - start)} seconds.')
        bin_im = cfl.readcfl(bin_im_path)

        # Homodyne reconstruction if partial Fourier was used
        if seq.partial_fourier_fraction < 1.0:
            start = time()
            print('-- Running homodyne correction...', end='')
            bin_im = bart(1, 'homodyne -I 1 {}'.format(seq.partial_fourier_fraction), bin_im)
            end = time()
            print(f'Done. Elapsed time: {int(end - start)} seconds.')

        # Combine bins to form 3D-MSI image volume
        print('-- Combining bins... ', end='')
        msi_im = np.linalg.norm(bin_im, axis=Dim.B)
        print('Done.')

        # Save the final image volumes
        print('-- Saving outputs... ', end='')
        cfl.writecfl(bin_im_path, bin_im)
        cfl.writecfl(msi_im_path, msi_im)
        print('Done.')
