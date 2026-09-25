"""Global parameters used for plotting.

"""

import matplotlib.pyplot as plt

# standard font sizes
SMALLER_SIZE = 6
SMALL_SIZE = 7
MEDIUM_SIZE = 8
LARGE_SIZE = 10
LARGER_SIZE = 12

# global matplotlib rcParams
plt.rc('font', size=MEDIUM_SIZE, family='serif')
plt.rc('axes', titlesize=MEDIUM_SIZE)     
plt.rc('axes', labelsize=MEDIUM_SIZE)    
plt.rc('xtick', labelsize=SMALL_SIZE)    
plt.rc('ytick', labelsize=SMALL_SIZE)    
plt.rc('legend', fontsize=SMALL_SIZE)    
plt.rc('figure', titlesize=MEDIUM_SIZE)   
plt.rc('lines', linewidth=0.7)
plt.rc('axes', linewidth=0.7)
plt.rcParams['hatch.linewidth'] = 0.2

# colormaps
CMAP = {
    'image': 'gray',
    'freq': 'viridis',
    'error': 'seismic',
}

DPI = 600

FIG_WIDTH = (3.42, 5.12, 6.9)  # MRM figure widths (in inches) for single-column, 1.5 column, double column