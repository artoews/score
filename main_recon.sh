#!/bin/bash

# SCORE reconstruction pipeline.

# Operates on a scan directory containing:
#   - ksp_flat.{cfl/hdr}, flattened k-space with shape (nx, ny*nz, 1, coils, 1, bins)
#   - pat.{cfl/hdr}, sampling pattern with shape (1, ny, nz)
#   - seq.yml, acquisition protocol parameters
#
# All outputs are saved to the same directory, including:
#   - ksp.{cfl/hdr}, embedded k-space with shape (nx, ny, nz, coils, 1, bins)
#   - sens.{cfl/hdr}, coil sensitivity maps with shape (nx, ny, nz, coils, maps, bins)
#   - sheared/ directory, containing image reconstruction results for the sheared view
#   - unsheared/ directory, containing image reconstruction results for the unsheared view
#
# Usage: bash main_recon.sh <scan_dir>

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <scan_dir>"
    exit 0
fi

scan_dir=$1
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/recon

echo " -------------------- Zero-filled Embedding (~ 1 min) -------------------- "
time python -u $script_dir/embed.py $scan_dir
 
echo " -------------------- Coil Sensitivity Estimation (~ 10 min) -------------------- "
time bash $script_dir/ecalib.sh $scan_dir/ksp $scan_dir/sens

echo " -------------------- Image Reconstruction (~ 30 min) -------------------- "
time python -u $script_dir/recon.py $scan_dir --fft

echo " -------------------- Image Post-Processing (~ 30 min) -------------------- "
time python -u $script_dir/post.py $scan_dir --iso --up --window --no_ge
