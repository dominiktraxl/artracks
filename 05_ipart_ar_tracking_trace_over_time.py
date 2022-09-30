# Copyright (C) 2022 by
# Dominik Traxl <dominik.traxl@posteo.org>
# All rights reserved.
# GPL-3.0 license.

import os
import sys
import argparse

import yaml
import numpy as np
import pandas as pd
from ipart.AR_tracer import readCSVRecord, trackARs, filterTracks

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
# Int, hours, gap allowed to link 2 records. Should be the time resolution of
# the data.
TIME_GAP_ALLOW = config['TIME_GAP_ALLOW']
# tracking scheme. 'simple': all tracks are simple paths.
# 'full': use the network scheme, tracks are connected by their joint points.
TRACK_SCHEME = config['TRACK_SCHEME']  # 'simple' | 'full'
# int, max Hausdorff distance in km to define a neighborhood relationship
MAX_DIST_ALLOW = config['MAX_DIST_ALLOW']  # km
# int, min duration in hrs to keep a track.
MIN_DURATION = config['MIN_DURATION']
# int, min number of non-relaxed records in a track to keep a track.
MIN_NONRELAX = config['MIN_NONRELAX']

# filesystem
output_folder = config['output_folder']

# combine csv files
if not os.path.isfile(os.path.join(
        output_folder, 'ipart', 'ar', 'ar_records.csv')):
    os.system(
        "awk '(NR == 1) || (FNR > 1)' "
        f"{os.path.join(output_folder, 'ipart', 'ar', '*.csv')}"
        f" > "
        f"{os.path.join(output_folder, 'ipart', 'ar', 'ar_records.csv')}"
    )

# read record
ardf = readCSVRecord(os.path.join(
    output_folder, 'ipart', 'ar', 'ar_records.csv'))

# track ARs
track_list = trackARs(
    ardf, TIME_GAP_ALLOW, MAX_DIST_ALLOW, track_scheme=TRACK_SCHEME)

# filter tracks
if config['do_filter_tracks']:
    track_list = filterTracks(track_list, MIN_DURATION, MIN_NONRELAX)

# collect tracks
trackdfs = []
for i in range(len(track_list)):

    print(i)

    ti = track_list[i]
    trackidi = i
    ti.data.loc[:, 'trackid'] = trackidi
    ti.trackid = trackidi

    trackdf = ti.data
    trackdfs.append(trackdf)

# concat
trackdf = pd.concat(trackdfs, axis=0, ignore_index=True)

# save data
abpath_out = os.path.join(output_folder, 'ipart', 'ar', 'ar_tracks.csv')
np.set_printoptions(threshold=sys.maxsize)
trackdf.to_csv(abpath_out, index=False)
trackdf.to_pickle(os.path.join(output_folder, 'ipart', 'ar', 'ar_tracks.pkl'))
