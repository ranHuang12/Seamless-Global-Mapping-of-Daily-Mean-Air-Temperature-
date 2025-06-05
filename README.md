1. Data Preprocessing: 
This part involves converting land surface temperature (LST) data collected from TERRA/AQUA MODIS products into TIFF format and generating various auxiliary datasets. 

2. DMAT_CLEAR estimation:
In this stage, data sample sets are extracted; the best feature combination and the optimal algorithm are determined through validation. A ranked order is established for DMAT estimation models from various combinations of MODIS TERRA/AQUA daytime/nighttime LST with auxiliary data. Based on these models, the final estimates of daily mean air temperature under clear-sky conditions are obtained. 

3. DMAT_CLOUD estimation:
In this stage, the focus is on interpolating missing pixel values in both reference and non-reference images caused by cloud cover, using spatial and temporal information to estimate DMAT. This part mainly includes the following components: selection of reference image dates, interpolation of reference images, interpolation of non-reference images, linear interpolation of the time series, and final validation of the seamless dataset.
