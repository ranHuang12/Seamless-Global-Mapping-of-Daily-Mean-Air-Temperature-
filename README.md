
# A Novel Scheme for Seamless Global Mapping of Daily Mean Air Temperature (SGM_DMAT) at 1-Kilometer Spatial Resolution Using Satellite and Auxiliary Data

## Project Overview
This repository contains DFAA event characteristic data, DFAA time series chart data, DFAA driver analysis results, as well as code for calculating SWAP indexes, code for extracting DFAA events, and code for Pettitt mutation tests.

## Folders

### Data Preprocessing
Includes the extraction of LST, EVI, LONG, LAT, ANG, M, and DOY from TERRA/AQUA MODIS products, and H from GVE products; filtering and interpolating EVI time series.

### DMAT_CLEAR estimation
Includes the selection of the optimal algorithm, the best feature combination, and the most suitable calibration dataset, and establishing the ranked order for DMAT estimation models from various combinations of MODIS TERRA/AQUA daytime/nighttime LST with auxiliary data.

### DMAT_CLOUD estimation
Includes the selection of reference image, interpolation of reference images and non-reference images.

## Global DMAT datasets

This dataset provides seamless global Daily Mean Air Temperature (DMAT) data, covering major terrestrial areas worldwide from 2020 to 2023, with a spatial resolution of 1 km(https://data.tpdc.ac.cn/en/data/dd408db4-2313-407b-8ae1-2d62b551e3fc).
