# Copyright (C) 2022 by
# Dominik Traxl <dominik.traxl@posteo.org>
# All rights reserved.
# GPL-3.0 license.

import os
import argparse

import yaml
import numpy as np
import pandas as pd
import xarray as xr
import xesmf as xe

# argument parameters
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    'year',
    type=str,
    help='regrid given year',
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

# config parameters
spatial_resolution = config['spatial_resolution']
temporal_resolution = config['temporal_resolution']

# filesystem
data_folder_e = config['data_folder_e']
data_folder_n = config['data_folder_n']
output_folder = config['output_folder']
os.makedirs(
    os.path.join(output_folder, 'ivt_regridded', args.year),
    exist_ok=True
)

# era5 files
# name: vertical integral of eastward water vapour flux; yearly downloads
vapfut_files = os.listdir(data_folder_e)
# name: vertical integral of northward water vapour flux; yearly downloads
vapfvt_files = os.listdir(data_folder_n)

# output resolution
ds_out = xr.Dataset({
    "latitude": (["latitude"],
                 np.arange(90, -90-spatial_resolution, -spatial_resolution)),
    "longitude": (["longitude"],
                  np.arange(0, 360, spatial_resolution))
})

# create file dictionary
uflux_files = {}
for f in vapfut_files:
    year = f.split('_')[-1][:4]
    uflux_files[year] = f

vflux_files = {}
for f in vapfvt_files:
    year = f.split('_')[-1][:4]
    vflux_files[year] = f

# load uflux
uflux_fn = uflux_files[args.year]
ds_uflux = xr.open_dataset(os.path.join(data_folder_e, uflux_fn))
assert len(ds_uflux.data_vars) == 1
ds_uflux = ds_uflux.rename({list(ds_uflux.data_vars)[0]: 'uflux'})

# load vflux
vflux_fn = vflux_files[args.year]
ds_vflux = xr.open_dataset(os.path.join(data_folder_n, vflux_fn))
assert len(ds_vflux.data_vars) == 1
ds_vflux = ds_vflux.rename({list(ds_vflux.data_vars)[0]: 'vflux'})

# combine
ds = ds_uflux
ds['vflux'] = ds_vflux['vflux']

# assert correct number of time-slices
days_in_year = pd.Timestamp(int(args.year), 12, 31).day_of_year
assert ds.time.shape[0] == days_in_year * 24

# pos array
positions = np.arange(0, ds.time.shape[0] + 24, 24)

# regrid on a daily basis
for i in range(len(positions) - 1):

    print(f'{args.year}-{i+1:03d}')

    # subset
    dst = ds.isel(time=slice(positions[i], positions[i+1]))

    # compute ivt
    dst['ivt'] = np.sqrt(dst['uflux']**2 + dst['vflux']**2)

    # create regridder
    try:
        regridder = xe.Regridder(
            dst, ds_out, "bilinear", periodic=True,
            reuse_weights=True,
            filename=os.path.join(output_folder,
                                  "ivt_regridded",
                                  "bilinear_peri.nc"))
    except OSError as e:
        print(OSError, e)
        regridder = xe.Regridder(dst, ds_out, "bilinear", periodic=True)
        regridder.to_netcdf(
            os.path.join(output_folder, 'ivt_regridded', 'bilinear_peri.nc'))

    # perform regridding
    dst_r = regridder(dst)

    # resample time
    dst_rr = dst_r.resample(time=f'{temporal_resolution}h',
                            loffset='3h',
                            ).mean()

    # store
    dst_rr.to_netcdf(os.path.join(
        output_folder, 'ivt_regridded', args.year, f'{i:03d}.nc'), mode='w')
