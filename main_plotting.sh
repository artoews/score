#!/bin/bash
# 
# Make all figures for paper.
# 
# The subject (case) & ROI for each figure is specified in plotting/data_config.py.
#
# Usage: bash main_plotting.sh <data_dir> <save_dir>

if [ "$#" -lt 2 ]; then
  echo "Usage: bash $0 <data_dir> <save_dir>"
  exit 0
fi

data_dir=$1
save_dir=$2

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
plotting_dir=$script_dir/plotting

echo 'Making figure 1...'
python $plotting_dir/figure1.py $data_dir $save_dir

echo 'Making figure 2...'
python $plotting_dir/figure2.py $save_dir

echo 'Making figure 3...'
python $plotting_dir/figure3.py $save_dir

echo 'Making figure 4...'
python $plotting_dir/figure4.py $save_dir

echo 'Making figure 5...'
python $plotting_dir/make_results_figure.py 5 $data_dir $save_dir

# # Figures 6 and 7 require data not included in released data
# echo 'Making figure 6...'
# python $plotting_dir/make_results_figure.py 6 $data_dir $save_dir
# echo 'Making figure 7...'
# python $plotting_dir/make_results_figure.py 7 $data_dir $save_dir

echo 'Making figure A1...'
python $plotting_dir/figureA1.py $save_dir

echo 'Done making all figures.'
