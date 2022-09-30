# Copyright (C) 2022 by
# Dominik Traxl <dominik.traxl@posteo.org>
# All rights reserved.
# GPL-3.0 license.

import os
import argparse
import yaml

import pandas as pd

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
v = pd.read_pickle(os.path.join(output_folder, 'ar.pkl'))

# delete columns
cols = ['contour_x', 'contour_y', 'axis_x', 'axis_y', 'axis_rdp_x',
        'axis_rdp_y']
for col in cols:
    del v[col]

# store
v.to_csv(os.path.join(output_folder, 'ar.csv'))
