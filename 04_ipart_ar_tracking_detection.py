# Copyright (C) 2022 by
# Dominik Traxl <dominik.traxl@posteo.org>
# All rights reserved.
# GPL-3.0 license.

import os
import sys
import argparse

import yaml
import numpy as np
from netCDF4 import Dataset
from ipart.utils import funcs
from ipart.AR_detector import findARsGen

# argument parameters
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    'year',
    type=str,
    help='detect for given year',
)
parser.add_argument(
    '--config', '-c',
    type=str,
    help='path to the config.yml file',
    default=os.path.join(os.getcwd(), 'config.yml'),
)
args = parser.parse_args()

# load config
config = yaml.safe_load(open(args.config))

# parameters
year = args.year
shift_lon = config['shift_lon']  # shift to center Pacific and Altantic
param_dict = {
    # kg/m/s, define AR candidates as regions >= than this anomalous ivt.
    # If None is given, compute a threshold based on anomalous ivt data. See
    # the docstring of ipart.AR_detector.determineThresLow() for details.
    'thres_low': config['thres_low'],
    # km^2, drop AR candidates smaller than this area.
    'min_area': config['min_area'],
    # km^2, drop AR candidates larger than this area.
    'max_area': config['max_area'],
    # float, min length/width ratio.
    'min_LW': config['min_LW'],
    # degree, exclude systems whose centroids are lower than this latitude.
    # NOTE this is the absolute latitude for both NH and SH. For SH, systems
    # with centroid latitude north of -20 will be excluded.
    'min_lat': config['min_lat'],
    # degree, exclude systems whose centroids are higher than this latitude.
    # NOTE this is the absolute latitude for both NH and SH. For SH, systems
    # with centroid latitude south of -80 will be excluded.
    'max_lat': config['max_lat'],
    # km, ARs shorter than this length is treated as relaxed.
    'min_length': config['min_length'],
    # km, ARs shorter than this length is discarded.
    'min_length_hard': config['min_length_hard'],
    # degree lat/lon, error when simplifying axis using rdp algorithm.
    'rdp_thres': config['rdp_thres'],
    # grids. Remove small holes in AR contour.
    'fill_radius': config['fill_radius'],
    # do peak partition or not, used to separate systems that are merged
    # together with an outer contour.
    'single_dome': config['single_dome'],
    # max prominence/height ratio of a local peak. Only used when
    # single_dome=True
    'max_ph_ratio': config['max_ph_ratio'],
    # minimal proportion of flux component in a direction to total flux to
    # allow edge building in that direction
    'edge_eps': config['edge_eps'],
    # bool, if True, treat the data as zonally cyclic (e.g. entire hemisphere
    # or global). ARs covering regions across the longitude bounds will be
    # correctly treated as one. If your data is not zonally cyclic, or a zonal
    # shift of the data can put the domain of interest to the center, consider
    # doing the shift and setting this to False, as it will save computations.
    'zonal_cyclic': config['zonal_cyclic'],
}

# filesystem
data_folder_e = config['data_folder_e']
data_folder_n = config['data_folder_n']
output_folder = config['output_folder']
os.makedirs(os.path.join(output_folder, 'ipart', 'ar'), exist_ok=True)
label_file_out_name = f'{year}_labels_angles_ivt.nc'
record_file_out_name = f'{year}_ar_records.csv'

# load flux data
if config['do_regridding']:
    quNV = funcs.readNC(
        os.path.join(output_folder, 'ivt_regridded', f'{year}.nc'), 'uflux')
    qvNV = funcs.readNC(
        os.path.join(output_folder, 'ivt_regridded', f'{year}.nc'), 'vflux')
else:
    quNV = funcs.readNC(
        os.path.join(data_folder_e, f'{year}.nc'), 'uflux')
    qvNV = funcs.readNC(
        os.path.join(data_folder_n, f'{year}.nc'), 'vflux')

# shift flux data
quNV = quNV.shiftLon(shift_lon)
qvNV = qvNV.shiftLon(shift_lon)

# load ivt/thr data (already shifted)
t, s = config['kernel'][:2]
ivtNV = funcs.readNC(os.path.join(
    output_folder, 'ipart', 'thr', f'{year}-THR-kernel-t{t}-s{s}.nc'),
    'ivt')
ivtrecNV = funcs.readNC(os.path.join(
    output_folder, 'ipart', 'thr', f'{year}-THR-kernel-t{t}-s{s}.nc'),
    'ivt_rec')
ivtanoNV = funcs.readNC(os.path.join(
    output_folder, 'ipart', 'thr', f'{year}-THR-kernel-t{t}-s{s}.nc'),
    'ivt_ano')

# get coordinates
latax = quNV.getLatitude()
lonax = quNV.getLongitude()
timeax = ivtNV.getTime()

# nc file to save AR location labels
ncfout = Dataset(os.path.join(
    output_folder, 'ipart', 'ar', label_file_out_name), 'w')

# csv file to save AR record table
# remove summarization in csv file
np.set_printoptions(threshold=sys.maxsize)

with open(os.path.join(
        output_folder, 'ipart', 'ar', record_file_out_name), 'w') as dfout:

    finder_gen = findARsGen(ivtNV.data, ivtrecNV.data, ivtanoNV.data,
                            quNV.data, qvNV.data, latax, lonax, times=timeax,
                            **param_dict)
    # create metadata
    next(finder_gen)

    for (tidx, timett, label, angle, cross, result_df) in finder_gen:

        # store ar records
        result_df.to_csv(dfout, header=dfout.tell() == 0, index=False)

        # store labels, angles, ivt
        funcs.saveNCDims(ncfout, label.axislist)
        funcs._saveNCVAR(ncfout, label, 'int')
        funcs._saveNCVAR(ncfout, angle)
        funcs._saveNCVAR(ncfout, cross)

# close .nc file
ncfout.close()
