
# A Novel Scheme for Seamless Global Mapping of Daily Mean Air Temperature (SGM_DMAT) at 1-Kilometer Spatial Resolution Using Satellite and Auxiliary Data

## Project Overview
This repository contains code for Data Preprocessing,code for DMAT_CLEAR estimation,and code for DMAT_CLOUD estimation,as well as Global DMAT datasets .

## Folders

### Data Preprocessing
Includes the extraction of LST, EVI, LONG, LAT, ANG, M, and DOY from TERRA/AQUA MODIS products, and H from GVE products; filtering and interpolating EVI time series.

### DMAT_CLEAR estimation
Includes the selection of the optimal algorithm, the best feature combination, and the most suitable calibration dataset, and establishing the ranked order for DMAT estimation models from various combinations of MODIS TERRA/AQUA daytime/nighttime LST with auxiliary data.

### DMAT_CLOUD estimation
Includes the selection of reference image, interpolation of reference images and non-reference images.

## Global DMAT datasets

This dataset provides seamless global Daily Mean Air Temperature (DMAT) data, covering major terrestrial areas worldwide from 2020 to 2023, with a spatial resolution of 1 km(https://data.tpdc.ac.cn/en/data/dd408db4-2313-407b-8ae1-2d62b551e3fc).
