# How to use the CDS API:
# https://cds.climate.copernicus.eu/api-how-to

import os
import argparse
import yaml

import cdsapi

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
variables = [
    'vertical_integral_of_eastward_water_vapour_flux',
    'vertical_integral_of_northward_water_vapour_flux',
]

# filesystem
data_folder_e = config['data_folder_e']
data_folder_n = config['data_folder_n']

# initiate client
c = cdsapi.Client()

# get data
for year in years:
    for variable in variables:

        if "eastward" in variable:
            folder = data_folder_e
        elif "northward" in variable:
            folder = data_folder_n

        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'format': 'netcdf',
                'variable': variable,
                'year': year,
                'month': [
                    '01', '02', '03',
                    '04', '05', '06',
                    '07', '08', '09',
                    '10', '11', '12',
                ],
                'day': [
                    '01', '02', '03',
                    '04', '05', '06',
                    '07', '08', '09',
                    '10', '11', '12',
                    '13', '14', '15',
                    '16', '17', '18',
                    '19', '20', '21',
                    '22', '23', '24',
                    '25', '26', '27',
                    '28', '29', '30',
                    '31',
                ],
                'time': [
                    '00:00', '01:00', '02:00',
                    '03:00', '04:00', '05:00',
                    '06:00', '07:00', '08:00',
                    '09:00', '10:00', '11:00',
                    '12:00', '13:00', '14:00',
                    '15:00', '16:00', '17:00',
                    '18:00', '19:00', '20:00',
                    '21:00', '22:00', '23:00',
                ],
            },
            os.path.join(folder, f'{year}.nc'))
