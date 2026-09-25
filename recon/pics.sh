#!/bin/bash

# Reconstruct spectral bin images from raw k-space using the bart pics tool.
# The reconstruction uses NUFFT if a trajectory is provided, otherwise FFT.
#
# Usage: bash pics.sh <ksp> <sens> <im> [traj]
#   ksp:  cfl name of k-space with shape (nx, ny, nz, coils, 1, bins)
#   sens: cfl name of coil sensitivity maps with shape (nx, ny, nz, coils, maps, bins)
#   im:   cfl name for OUTPUT images with shape (nx, ny, nz, 1, 1, bins)
#   traj: cfl name of trajectory with shape (3, samples, 1, 1, 1, 1) - optional

if [ $# -lt 3 ]; then
    echo "Usage: $0 <ksp> <sens> <im> [traj]"
    exit 1
fi

ksp=$1
sens=$2
im=$3
if [ $# -eq 4 ]; then
    traj=$4
    use_nufft=true
else
    use_nufft=false
fi

pics_lambda=0.01
debug_level=1
bin_dim=5

# run one iteration of pics on central bin to get a common scaling factor
num_bins=$(bart show -d $bin_dim $ksp)
center_bin=$(awk "BEGIN {print int($num_bins / 2)}")
bart slice 5 $center_bin $ksp ${ksp}_bin
bart slice 5 $center_bin $sens ${sens}_bin
if $use_nufft; then
    scale_factor=$(bart pics -g -t $traj -d 4 -i 0 ${ksp}_bin ${sens}_bin ${im}_bin 2>&1 | grep Scaling | awk '{print $2}')
    export scale_factor=${scale_factor::-1}
else
    scale_factor=$(bart pics -g -d 4 -i 0 ${ksp}_bin ${sens}_bin ${im}_bin 2>&1 | grep Scaling | awk '{print $2}')
    export scale_factor=${scale_factor::-1}
fi
rm ${ksp}_bin.* ${sens}_bin.* ${im}_bin.*

# spectral images are reconstructed for each bin separately
if $use_nufft; then
    loop_cmd="pics -g -w ${scale_factor} -S -R Q:${pics_lambda} -d ${debug_level} -t $traj $ksp $sens $im"
else
    loop_cmd="pics -g -w ${scale_factor} -S -R Q:${pics_lambda} -d ${debug_level} $ksp $sens $im"
fi
bart --loop $(bart bitmask $bin_dim) -r $ksp $loop_cmd
