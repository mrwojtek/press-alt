# Pressure Altitude Filters

Set of Python3 scripts for altitude estimation from the fusion of GPS and barometer pressure
measurements. This project contains three Kalman filter implementations for altitude estimation using a barometer measurements. For review please refer to the [Case Studies](https://github.com/mrwojtek/press-alt/wiki/Case-Studies) document.

Back in 2013 I've become an owner of Samsung Galaxy S3 phone which is supplied with barometer chip. I used to bike a lot (especially in the forests) and in that conditions GPS measurements are rather poor. I wrote a set of Kalman filters to correct for those errors using pressure measurements. This project is neither a complete tool nor complete product but rather a proof of concept how much can be done using data available for Android phones. There is large potential for improvements but the basic code is here and I've decided to release it as an Open Source code.

## Usage

This project is primarily dedicated to process GPS and pressure measurements recorded by an Android phones. The sibling [sens-rec](https://github.com/mrwojtek/sens-rec) project provides with an Android application that can be used to record those measurements in a form of a binary or text files.

To use the scripts in this project a Python3.x installation is required with the `pyproj`, `pywavelets`, `simplekml`, `scipy`, `numpy` and `matplotlib` packages installed. Additionally, in order to use digital elevation maps (for example [SRTM](http://srtm.csi.cgiar.org/SELECTION/inputCoord.asp) data) the packages `osgeo` and `gdal` for Python must be installed. There is an option to adjust for geoid undulation (difference between mean sea level and WGS84 ellipsoid) with the help of [GeographicLib](http://geographiclib.sourceforge.net/) project but Python3 library for geoid calculations must be compiled manually from the Python wrapper [example](https://sourceforge.net/p/geographiclib/code/ci/v1.46/tree/wrapper/python).

Right now there is no setup file for this project and in order to use it, it is best to add a local project directory to the `PYTHONPATH` environmental variable. It is then possible to run `analyze.py` script. For example to plot GPS altitude and filtered altitude on the left axis and heart rate measurements on the right axis one could run:  
`$ ./analyze.py "Recording 1.bin" -1 alt_gps alt_filt -2 heart_rate`

## License

This project is a free Open Source software release under the [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0).
