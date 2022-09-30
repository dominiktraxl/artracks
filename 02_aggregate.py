# Copyright (C) 2022 by
# Dominik Traxl <dominik.traxl@posteo.org>
# All rights reserved.
# GPL-3.0 license.

import os
import sys
import argparse

import yaml
import xarray as xr

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

# exit if user does not want to regrid
if not config['do_regridding']:
    sys.exit(0)

# filesystem
output_folder = config['output_folder']

# aggregate files for each year
for year in range(config['year_start'], config['year_end'] + 1):
    print(f'opening {year}')
    ds = xr.open_mfdataset(os.path.join(
        output_folder, 'ivt_regridded', str(year), '*.nc'))
    print('writing to file')
    ds.to_netcdf(os.path.join(output_folder, 'ivt_regridded', f'{year}.nc'))
