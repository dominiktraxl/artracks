# Copyright (C) 2022 by
# Dominik Traxl <dominik.traxl@posteo.org>
# All rights reserved.
# GPL-3.0 license.

import os
import argparse

import yaml
import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
import rioxarray
from pyproj import Geod
from pyproj.exceptions import GeodError
import shapely.geometry
from shapely.geometry import Polygon, LineString
from antimeridian_splitter import split_polygon
import json

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# argument parameters
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    'year',
    type=str,
    help='process given year',
)
parser.add_argument(
    '--config', '-c',
    type=str,
    help='path to the config.yml file',
    default=os.path.join(os.getcwd(), 'config.yml'),
)
args = parser.parse_args()
year = args.year

# load config
config = yaml.safe_load(open(args.config))

# parameters
plot = False

# filesystem
scripts_folder = config['scripts_folder']
output_folder = config['output_folder']
if config['do_regridding']:
    ivt_folder = os.path.join(output_folder, 'ivt_regridded')
else:
    ivt_folder = os.path.join(output_folder, 'ivt')
os.makedirs(os.path.join(output_folder, 'AR_parts'), exist_ok=True)

# load data
wc = gpd.read_file(os.path.join(
    scripts_folder, 'WORLD_CONTINENTS', 'World_Continents.shp'))
ar = pd.read_pickle(os.path.join(
    output_folder, 'ipart', 'ar', 'ar_tracks.pkl'))

# subset ARs by year
ar = ar.loc[ar['time'].dt.year == int(year)]

# set longitudes to range [-180, 180]
for col in ['contour_x', 'axis_x', 'axis_rdp_x', 'centroid_x']:
    ar.loc[:, col] = (ar[col] % 360 + 540) % 360 - 180

# extract axis as LineStrings
geod = Geod(ellps="WGS84")
continents = wc['CONTINENT'].values
cols = ['axis_length', 'ar_area', 'ocean', 'land',
        'lf_lon', 'lf_lat', 'lf_ivt'] + config['landfall_continent_priority']
template = pd.DataFrame(index=[0], data={col: np.nan for col in cols})
lss = []
vs = []
tperrors = []
nodataerrors = []
for i in range(ar.shape[0]):

    print(f'{i+1}/{ar.shape[0]}')

    # subset row/column
    art = ar.iloc[i]

    # create AR polygon
    c_x = art['contour_x']
    c_y = art['contour_y']
    c_df = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(c_x, c_y, crs='EPSG:4326'))
    p = Polygon(c_df['geometry'])

    # take care of antimeridian wrapping
    p = split_polygon(json.loads(json.dumps(shapely.geometry.mapping(p))),
                      output_format="geometrycollection")
    if len(p) == 1:
        p = p[0]

    # compute area/perimeter of AR
    area, _ = geod.geometry_area_perimeter(p)
    area = abs(area)/1e6  # km^2
    # perimeter = abs(perimeter)/1e3  # km

    # intersect AR with continents
    try:
        intersection = wc.intersection(p).to_frame()
    except shapely.errors.TopologicalError:
        print(f'{i} topological error!')
        tperrors.append(i)
        lss.append(LineString())
        vs.append(template)
        continue

    intersection['CONTINENT'] = wc['CONTINENT']

    # compute intersection area for each continent
    area_proportions = []
    for _, row in intersection.iterrows():
        try:
            area_c = abs(geod.geometry_area_perimeter(row[0])[0])/1e6
            area_p = area_c/area*100
        except GeodError:
            area_p = 0
        area_proportions.append(area_p)
    intersection['area_proportion'] = area_proportions

    # area and continent proportions
    land = intersection['area_proportion'].sum()
    ocean = 100 - land

    # for maximum ivt of each continent
    intersection['lat'] = np.nan
    intersection['lon'] = np.nan
    intersection['ivt'] = np.nan

    # find maximum ivt over landfalling locations
    if land > 0:

        year = art['time'].year

        # load ivt data
        ds = xr.open_dataset(os.path.join(
            ivt_folder, f'{year}.nc'), decode_coords="all")
        ds = ds.sel(time=art['time'])['ivt']

        # convert to range -180, 180
        ds = ds.assign_coords(longitude=(((ds.longitude + 180) % 360) - 180))
        ds = ds.sortby('longitude')
        ds.rio.write_crs("epsg:4326", inplace=True)

        # add maximum ivt for each continent
        for index, row in intersection.iterrows():
            ip = row[0]
            if not ip.is_empty:
                try:
                    if ip.geom_type == 'MultiPolygon':
                        ids = ds.rio.clip(list(ip), all_touched=True)
                    else:
                        ids = ds.rio.clip([ip], all_touched=True)

                    # find maximum
                    ids = ids.where(ids == ids.max(), drop=True).squeeze()

                    # add small random numbers in case there are multiple max
                    # values
                    print('size ', ids.size)
                    while ids.size != 1:
                        ids += (np.random.rand(*ids.shape) - 0.5) / 1e3
                        ids = ids.where(ids == ids.max(), drop=True).squeeze()
                        print('size now ', ids.size)
                        print(f'storing {ids}')

                    intersection.loc[index, 'ivt'] = float(ids.data)
                    intersection.loc[index, 'lat'] = float(ids.latitude.data)
                    intersection.loc[index, 'lon'] = float(ids.longitude.data)

                except rioxarray.exceptions.NoDataInBounds:
                    nodataerrors.append(i)
                    ids = None

        if plot:
            # plot continent intersections
            fig = plt.figure()
            ax = fig.add_subplot(projection=ccrs.PlateCarree())
            wc.plot('CONTINENT', ax=ax, alpha=.3, transform=ccrs.Geodetic())
            for _, row in intersection.iterrows():
                ip = row[0]
                gpd.GeoSeries(ip).plot(ax=ax, alpha=.8,
                                       transform=ccrs.Geodetic())
                if not ip.is_empty:
                    if ip.geom_type == 'MultiPolygon':
                        ids = ds.rio.clip(list(ip), all_touched=True)
                    else:
                        ids = ds.rio.clip([ip], all_touched=True)
                    ids.plot(ax=ax, alpha=.5)
            # plot ivt field of AR mask
            fig = plt.figure()
            ax = fig.add_subplot(projection=ccrs.PlateCarree())
            wc.plot('CONTINENT', ax=ax, alpha=.3, transform=ccrs.Geodetic())
            gpd.GeoSeries(p).plot(ax=ax, alpha=.5, transform=ccrs.Geodetic())
            ds.plot(ax=ax, alpha=.1, vmin=300, vmax=600)
            ds.rio.clip([p], all_touched=True).plot(
                ax=ax, alpha=.8, vmin=300, vmax=600)

    # compute axis length
    gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(
        art['axis_x'], art['axis_y'], crs='EPSG:4326'))
    ls = LineString(gdf['geometry'])
    lss.append(ls)
    length = geod.geometry_length(ls)/1000

    # priority list in case an AR hits multiple continents
    lcp = config['landfall_continent_priority']
    ci = dict((v, k) for k, v in wc['CONTINENT'].to_dict().items())
    cp = {lcpi: intersection.at[ci[lcpi], 'area_proportion'] for lcpi in lcp}

    # if no intersection, no land fall
    lf_lat = np.nan
    lf_lon = np.nan
    lf_ivt = np.nan

    # if intersection, go by continent priority
    for lcpi in lcp[::-1]:
        if cp[lcpi] > 0:
            lf_lat = intersection.at[ci[lcpi], 'lat']
            lf_lon = intersection.at[ci[lcpi], 'lon']
            lf_ivt = intersection.at[ci[lcpi], 'ivt']

    # put together
    v = pd.DataFrame(data={
        'axis_length': [length],
        'ar_area': [area],
        'ocean': [ocean],
        'land': [land],
        'lf_lon': [lf_lon],
        'lf_lat': [lf_lat],
        'lf_ivt': [lf_ivt]})

    # add continent proportions
    for _, row in intersection.iterrows():
        v[row['CONTINENT']] = row['area_proportion']

    vs.append(v)

# concat vs
v = pd.concat(vs)
v.index = range(len(v))

# concat with ar
ar.index = range(len(ar))
ar = pd.concat([ar, v], axis=1)

# create gar
ar_axis = gpd.GeoDataFrame(geometry=lss, crs='EPSG:4326')

# errors
tperrors = np.asarray(tperrors)
nodataerrors = np.asarray(nodataerrors)

# store tables
ar.to_pickle(os.path.join(output_folder, 'AR_parts', f'{year}.pkl'))
ar_axis.to_file(os.path.join(
    output_folder, 'AR_parts', f'{year}_axis.gpkg'), driver="GPKG")
np.save(os.path.join(
    output_folder, 'AR_parts', f'{year}_tperrors.npy'), tperrors)
np.save(os.path.join(
    output_folder, 'AR_parts', f'{year}_nodataerrors.npy'), nodataerrors)
