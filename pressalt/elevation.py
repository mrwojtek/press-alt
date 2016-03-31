# -*- coding: utf-8 -*-
#
#  (C) Copyright 2013, 2016 Wojciech Mruczkiewicz
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import gdal
import matplotlib.mlab as ml
import numpy as np
import pyproj
from osgeo import osr
from scipy import interpolate


class GeoFile:
    
    def __init__(self, file, band=1):
        self.dataset = gdal.Open(file)
        self.geotransform = self.dataset.GetGeoTransform()
        
        srs = osr.SpatialReference()
        srs.ImportFromWkt(self.dataset.GetProjection())
        self.proj = pyproj.Proj(srs.ExportToProj4())
        
        band = self.dataset.GetRasterBand(band)
        
    def values(self, x, y, proj=pyproj.Proj('+init=EPSG:4326'), geoid=None):
        assert(len(x) == len(y))
        
        pixels_x = np.empty(len(x))
        pixels_y = np.empty(len(y))
        for i in range(len(x)):
            geo = pyproj.transform(proj, self.proj, x[i], y[i])
            px, py = self._geo2pixel(self.geotransform, geo[0], geo[1])
            pixels_x[i] = px
            pixels_y[i] = py
            
        rx = self.dataset.RasterXSize - 1
        ry = self.dataset.RasterYSize - 1
        
        mx = max(0, int(np.floor(np.min(pixels_x))))
        Mx = min(rx, int(np.ceil(np.max(pixels_x))))
        my = max(0, int(np.floor(np.min(pixels_y))))
        My = min(ry, int(np.ceil(np.max(pixels_y))))

        if 0 <= Mx and mx <= rx and 0 <= My and my <= ry:
            v = self.dataset.ReadAsArray(mx, my, Mx-mx+1, My-my+1).astype(float)
            hi = interpolate.interp2d(range(mx, Mx+1), range(my, My+1), v, copy=False,
                                      bounds_error=False, fill_value=np.NaN)
            if geoid:
                h = lambda i: geoid.EllipsoidHeight(y[i], x[i], hi(pixels_x[i], pixels_y[i])[0])
            else:
                h = lambda i: hi(pixels_x[i], pixels_y[i])[0]
            return np.array([h(i) for i in range(len(x))])
        else:
            return np.ones(len(x))*np.NaN
    
    def _pixel2geo(self, gt, x, y):
        return gt[0] + x*gt[1] + y*gt[2], gt[3] + x*gt[4] + y*gt[5]

    def _geo2pixel(self, gt, x, y):
        s = 1.0/(gt[1]*gt[5] - gt[2]*gt[4])
        xt = x - gt[0]
        yt = y - gt[3]
        return s*(xt*gt[5] - yt*gt[2]), s*(-xt*gt[4] + yt*gt[1])


class GeoFiles:
    
    def __init__(self, files):
        self.files = [GeoFile(file) for file in files]
        
    def values(self, x, y, proj=pyproj.Proj('+init=EPSG:4326'), geoid=None):
        assert(len(x) == len(y))
        
        r = np.ones(len(x))*np.NaN
        for f in self.files:
            v = f.values(x, y, proj, geoid)
            i = ml.find(np.isfinite(v))
            r[i] = v[i]
        return r
