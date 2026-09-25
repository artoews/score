#!/bin/bash

# Estimate coil sensitivity maps for each spectral bin using ESPIRiT.
#
# Usage: bash ecalib.sh <ksp> <sens>
#   ksp:  cfl name of k-space with shape (nx, ny, nz, coils, 1, bins)
#   sens: cfl name for OUTPUT maps with shape (nx, ny, nz, coils, maps, bins)

if [ $# -lt 2 ]; then
    echo "Usage: $0 <ksp> <sens>"
    exit 1
fi

ksp=$1
sens=$2

bin_dim=5
debug_level=1

# coil maps are computed for each bin separately
bart --parallel-loop $(bart bitmask $bin_dim) -r $ksp -t 1 \
    ecalib -g -S -m 2 -d ${debug_level} $ksp $sens > /dev/null
