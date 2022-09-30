# Copyright (C) 2022 by
# Dominik Traxl <dominik.traxl@posteo.org>
# All rights reserved.
# GPL-3.0 license.

import os
import argparse
import yaml

import pandas as pd
import numpy as np
import geopandas as gpd

# argument parameters
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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

# filesystem
output_folder = config['output_folder']

# load data
ystart = config['year_start']
yend = config['year_end']
nyears = yend - ystart + 1
ar = []
ar_axis = []
err = pd.DataFrame(index=np.arange(ystart, yend + 1),
                   data={'n_ars': np.zeros(nyears),
                         'tperrors': np.zeros(nyears),
                         'nodataerrors': np.zeros(nyears), })

for year in range(ystart, yend + 1):
    print(f'loading {year}..')
    art = pd.read_pickle(os.path.join(
        output_folder, 'AR_parts', f'{year}.pkl'))
    ar.append(art)
    ar_axis.append(gpd.read_file(os.path.join(
        output_folder, 'AR_parts', f'{year}_axis.gpkg')))
    err.at[year, 'n_ars'] = len(art)
    err.at[year, 'tperrors'] = len(np.load(os.path.join(
        output_folder, 'AR_parts', f'{year}_tperrors.npy')))
    err.at[year, 'nodataerrors'] = len(np.load(os.path.join(
        output_folder, 'AR_parts', f'{year}_nodataerrors.npy')))

# concat
ar = pd.concat(ar)
ar_axis = pd.concat(ar_axis)

# index
ar.index = range(len(ar))
ar_axis.index = range(len(ar_axis))

# get rid of 'area' and 'length', computed by IPART
for col in ['area', 'length']:
    del ar[col]

# store
ar.to_pickle(os.path.join(output_folder, 'ar.pkl'))
ar_axis.to_file(os.path.join(output_folder, 'ar_axis.gpkg'), driver='GPKG')
err.to_pickle(os.path.join(output_folder, 'ar_err.pkl'))
