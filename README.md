[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7130642.svg)](https://doi.org/10.5281/zenodo.7130642)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7018725.svg)](https://doi.org/10.5281/zenodo.7018725)

# ARtracks - a Global Atmospheric River Catalogue Based on ERA5 and IPART

<p align="center">
<img src="track_id_89162.gif" width="605" height="449"/>
</p>

## Content

- [About](#about)
- [Overview](#overview)
- [Installation](#installation) 
- [Getting Original Data](#getting-original-data)
- [Creating the ARtracks Atmospheric River Catalogue](#creating-the-artracks-atmospheric-river-catalogue)
- [Loading the ARtracks Atmospheric River Catalogue Using Python](#loading-the-artracks-atmospheric-river-catalogue-using-python)
- [Data Content](#data-content)


## About

This repository provides a collection of Python scripts that produces a global,
high-resolution catalogue of atmospheric rivers (AR). The catalogue is based on
the [ERA5 climate reanalysis dataset](https://www.ecmwf.int/en/forecasts/datasets/reanalysis-datasets/era5),
specifically the output parameters "vertical integral of 
east-/northward water vapour flux". Most of the processing relies on
[IPART](https://github.com/ihesp/IPART) (Image-Processing based Atmospheric River Tracking),
a Python package for automated AR detection, axis finding and AR tracking.

The catalogue is provided as a pickled pandas.DataFrame, as well as a CSV file.

Note: the quality of the ARtracks catalogue depends on the ERA5 input data, as 
well as the IPART algorithm. It is therefore strongly recommended to read the 
respective documentation

- [ERA5 Documentation](https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation)
- [IPART paper](https://doi.org/10.5194/gmd-13-4639-2020)
- [IPART documentation](https://ipart.readthedocs.io/en/latest/)

Download: the ARtracks catalogue, processed for the years 1979-2019, can be 
downloaded here: https://doi.org/10.5281/zenodo.7018725


## Overview

Essentially, this repository provides convenience scripts to produce a global
catalogue of atmospheric rivers (ARs) utilizing ERA5 data and the IPART software 
package. In addition to the functionality IPART provides, we add some pre- and post-processing 
scripts, as well as one central location to adjust all the parameters that go into creating
the AR catalogue.

The first step in creating the AR catalogue is to adjust the parameters and
folder settings in `config.yml`. The original ERA5 data can then be downloaded
with `00_download_ERA5_ivt.py`. Running `01_regrid_ivt.py` will regrid the ivt data
from the original 0.25° lat/lon (1-hourly) grid to a 0.75° lat/lon (6-hourly)
grid. After aggregating the regridded data (`02_aggregate.py`), subsequent scripts 
perform the main functionalities of IPART

- top-hat by reconstruction (THR) computation on input data (`03_ipart_ar_tracking_thr_multifile.py`)
- Detect ARs from the output of the previous step (`04_ipart_ar_tracking_detection.py`)
- Identify AR axis (`04_ipart_tracking_detection.py`)
- Track ARs detected at individual time steps to form tracks (`05_ipart_ar_tracking_trace_over_time.py`)

Please refer to the [documentation of IPART](https://ipart.readthedocs.io/en/latest/) 
for details.

At this point, all the output of the IPART software package is stored in the output folder
set in `config.py`. Postprocessing of this output is implemented in 
`06_ar_landfall_continents.py` and `07_aggregate.py`, resulting in a single file 
AR catalogue. Postprocessing involves several computations. For each AR detected, 
we compute the following properties in addition to the 
[output of IPART](https://ipart.readthedocs.io/en/latest/Detect-ARs.html#ar-records-dataframe)

- Each sequence of ARs that forms a track is associated with a unique `trackid`
- The AR area and axis length computed by IPART is discarded, and a more accurate 
  estimation respecting the geographical projection is provided (`ar_area` and 
  `axis_length`)
- Each AR is intersected with continental land masses, to compute the proportion of the 
  AR that is located over `ocean` and `land`, and over the different continents 
  (`Africa`, `Asia`, `Australia`, `North America`, `Oceania`, `South America`,
  `Antarctica`, `Europe`)
- For each landfalling AR, we provide the location of the landfall (`lf_lon`, 
  `lf_lat`) and the respective IVT value (`lf_ivt`). If an AR hits multiple locations
  over a continent, which is usually the case, the location with the highest IVT 
  is chosen as the landfalling location. In case an AR hits multiple continents,
  a priority list of continents can be set in `config.py`. 

A complete description of the variables stored in the ARtracks catalogue is 
given in [Data Content](#data-content).


## Installation

No installation is required.

However, to run the python scripts the following packages are required

- ipart
- netcdf4
- xarray
- matplotlib
- xesmf
- geopandas
- pyproj
- numpy
- pandas
- rioxarray
- cartopy
- shapely
- dask
- antimeridian_splitter

You can use [conda](https://docs.conda.io/en/latest/) to set up an environment
and install dependencies via

```console
$ conda create -n AR
$ conda activate AR
$ conda install -c conda-forge ipart netcdf4 xarray matplotlib xesmf geopandas pyproj numpy pandas rioxarray cartopy shapely dask
```

Additionally, you need to install the `antimeridian_splitter-0.1.0.tar.gz` provided
in this repository

```console
$ pip install antimeridian_splitter-0.1.0.tar.gz
```

To compute intersections of ARs with continental land masses and landfalling
locations (`06_ar_landfall_continents.py`), you need to download the `WORLD_CONTINENTS`
folder provided in this repository, and place it in the same folder as the Python
scripts.


## Getting Original Data

To create the ARtracks catalogue, you need to first download the original ERA5 
IVT data that it is based on.

You can download the data here: https://confluence.ecmwf.int/display/CKB/How+to+download+ERA5

We provide a script to download the correct data variables and store them the way they need to 
be stored to work with the other scripts: `00_download_ERA5_ivt.py`. 


## Creating the ARtracks Atmospheric River Catalogue

1. Follow the [Installation](#installation) instructions

2. Download the python scripts and `config.yml` contained in this repository

3. Set user parameters in `config.yml`

4. `cd` into the directory containing the scripts, then run the scripts in the 
indicated order

  - `00_download_ERA5_ivt.py` (optional, to download original data)
  - `01_regrid_ivt.py` for each year in the range given in `config.yml`
  - `02_aggregate.py`
  - `03_ipart_ar_tracking_thr_multifile.py`
  - `04_ipart_ar_tracking_detection.py` for each year in the range given in `config.yml`
  - `05_ipart_ar_tracking_trace_over_time.py`
  - `06_ar_landfall_continents.py` for each year in the range given in `config.yml`
  - `07_aggregate.py`
  - `08_convert_ar_to_csv.py`
  
Note: some scripts have positional and/or optional arguments. Use

```console
$ python *script*.py -h
```

for more information.


## Loading the ARtracks Atmospheric River Catalogue Using Python

Using Python Pandas, you can load the pickled DataFrame / CSV file via the
following commands

```python
import pandas as pd

# pickled dataframe
ar_pkl = pd.read_pickle('ar.pkl')

# csv table
ar_csv = pd.read_csv('ar.csv', index_col=0)

```


## Data Content

The following table describes the columns of the ARtracks catalogue. Note that
the CSV version does not contain the following columns: `contour_y`, `contour_x`,
`axis_y`, `axis_x`, `axis_rdp_y` and `axis_rdp_x`.

| Name          | Description                                                     | Unit         | Valid Range   | Data Type       |
|:--------------|:----------------------------------------------------------------|:-------------|:--------------|:----------------|
| id            | numeric id for the AR at this particular time point             | -            | >= 0          | int64           |
| time          | date and time                                                   | -            | -             | datetime64      |
| contour_y     | y-coordinates (latitudes) of the AR contour                     | degrees      | [-90, 90]     | list of float64 |
| contour_x     | x-coordinates (longitude) of the AR contour                     | degrees      | [-180, 180]   | list of float64 |
| centroid_y    | latitude of the AR centroid, weighted by the IVT value          | degrees      | [-90, 90]     | float64         |
| centroid_x    | longitude of the AR centroid, weighted by the IVT value         | degrees      | [-180, 180]   | float64         |
| axis_y        | latitudes of the AR axis                                        | degrees      | [-90, 90]     | list of float64 |
| axis_x        | longitude of the AR axis                                        | degrees      | [-180, 180]   | list of float64 |
| axis_rdp_y    | latitude of the simplified AR axis                              | degrees      | [-90, 90]     | list of float64 |
| axis_rdp_x    | longitude of the simplified AR axis                             | degrees      | [-180, 180]   | list of float64 |
| width         | effective width as area/length                                  | km           | > 0           | float64         |
| LW_ratio      | length/width ratio                                              | -            | > 0           | float64         |
| strength      | spatially averaged IVT value within the AR region               | kg m^-1 s^-1 | > 0           | float64         |
| strength_ano  | spatially averaged anomalous IVT value within the AR region     | kg m^-1 s^-1 | > 0           | float64         |
| strength_std  | standard deviation of IVT within the AR region                  | kg m^-1 s^-1 | > 0           | float64         |
| max_strength  | maximum IVT value within the AR region                          | kg m^-1 s^-1 | > 0           | float64         |
| mean_angle    | spatially averaged angle between the IVT vector and the AR axis | degrees      | [-180, 180]   | float64         |
| is_relaxed    | True or False, whether the AR is flagged as "relaxed"           | -            | -             | bool            |
| qv_mean       | spatially averaged meridional integrated vapor flux             | kg m^-1 s^-1 | [-inf, inf]   | float64         |
| trackid       | unique AR track id                                              | -            | >= 0          | int64           |
| axis_length   | length of the AR                                                | km           | > 0           | float64         |
| ar_area       | area of the AR                                                  | km^2         | > 0           | float64         |
| ocean         | percentage of area over ocean                                   | -            | [0, 100]      | float64         |
| land          | percentage of area over land                                    | -            | [0, 100]      | float64         |
| lf_lon        | longitude of landfalling location                               | degrees      | [-180, 180]   | float64         |
| lf_lat        | latitude of landfalling location                                | degrees      | [-90, 90]     | float64         |
| lf_ivt        | ivt-value of landfalling location                               | kg m^-1 s^-1 | > 0           | float64         |
| Africa        | percentage of area over Africa                                  | -            | [0, 100]      | float64         |
| Asia          | percentage of area over Asia                                    | -            | [0, 100]      | float64         |
| Australia     | percentage of area over Australia                               | -            | [0, 100]      | float64         |
| North America | percentage of area over North America                           | -            | [0, 100]      | float64         |
| Oceania       | percentage of area over Oceania                                 | -            | [0, 100]      | float64         |
| South America | percentage of area over South America                           | -            | [0, 100]      | float64         |
| Antarctica    | percentage of area over Antarctica                              | -            | [0, 100]      | float64         |
| Europe        | percentage of area over Europe                                  | -            | [0, 100]      | float64         |

