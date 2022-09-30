# Copyright (C) 2022 by
# Dominik Traxl <dominik.traxl@posteo.org>
# All rights reserved.
# GPL-3.0 license.

import os
import argparse

import yaml
from ipart import thr

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

# parameters
years = range(config['year_start'], config['year_end'] + 1)
kernel = config['kernel']
shift_lon = config['shift_lon']

# filesystem
output_folder = config['output_folder']
os.makedirs(os.path.join(output_folder, 'ipart', 'thr'), exist_ok=True)
if config['do_regridding']:
    input_ivt_folder = 'ivt_regridded/'
else:
    input_ivt_folder = 'ivt/'

# create file list
filelist = []
for year in years:
    file_in_name = f'{year:d}.nc'
    abpath_in = os.path.join(output_folder, input_ivt_folder, file_in_name)
    filelist.append(abpath_in)
print(filelist)

# need at least two years of data
assert len(filelist) >= 2

# compute
thr.rotatingTHR(filelist, 'ivt', kernel,
                os.path.join(output_folder, 'ipart', 'thr'),
                shift_lon=shift_lon)
