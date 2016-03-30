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

from .record_readers import *
import matplotlib.mlab as ml
import numpy as np
import scipy.signal as signal
import scipy.spatial
import scipy.optimize
import scipy.interpolate
import pyproj
import pywt
from simplekml import Kml
from math import *


class GpsPressureReader(RecordReader):

    PRESSURE_EXPONENT = 5.25588
    PRESSURE_FACTOR = 0.0000225577

    def __init__(self):
        self.gps_events = list()
        self.press_events = list()

        self._gps_time = list()
        self._gps_bearing = list()
        self._gps_speed = list()
        self._gps_altitude = list()
        self._gps_latitude = list()
        self._gps_longitude = list()
        self._gps_points = None
        self._gps_distance = None

        self._press_time = list()
        self._press_pressure = list()
        self._press_altitude = list()
        self._press_distance = None

        self._start_time = None
        self._end_time = None

        self._last_altitude = None
        self._pressure_msl = None

        self._proj_src = None
        self._proj_dst = None

    def on_start(self, time, start_time, version):
        self.__init__()

    def on_gps(self, millisecond, latitude, longitude, altitude_geoid, bearing, speed, accuracy,
               time):
        self._update_time(millisecond)
        self.gps_events.append((millisecond, altitude_geoid, accuracy))
        self._gps_time.append(millisecond)
        self._gps_latitude.append(latitude)
        self._gps_longitude.append(longitude)
        self._gps_altitude.append(altitude_geoid)
        self._gps_bearing.append(bearing)
        self._gps_speed.append(speed)
        self._last_altitude = altitude_geoid

    def on_pressure(self, millisecond, pressure):
        self._update_time(millisecond)
        self.press_events.append((millisecond, pressure))
        self._press_time.append(millisecond)
        self._press_pressure.append(pressure)

        ap = self._find_altitude_pressure(pressure)
        self._press_altitude.append(ap if ap else np.NaN)

    def _update_time(self, millisecond):
        if not self._start_time:
            self._start_time = millisecond
        self._end_time = millisecond

    def duration(self):
        return (self._end_time - self._start_time) / 1000.0

    def time_to_seconds(self, value):
        return (value - self._start_time) / 1000.0

    def time_to_unit(self, value):
        return (value - self._start_time) / float(self._end_time - self._start_time)

    def gps_distance(self):
        if self._gps_distance is None:
            gps_points = self.gps_points()
            self._gps_distance = list()
            distance = 0.0
            for i in range(len(gps_points)):
                j = 0 if i == 0 else i - 1
                d = gps_points[i] - gps_points[j]
                distance += sqrt(d[0]**2 + d[1]**2)
                self._gps_distance.append(distance)
        return np.array(self._gps_distance)

    def gps_time(self):
        return np.array(self._gps_time)

    def gps_seconds(self):
        return self.time_to_seconds(self.gps_time())

    def gps_altitude(self):
        return np.array(self._gps_altitude)

    def gps_bearing(self):
        return np.array(self._gps_bearing)

    def gps_speed(self):
        return np.array(self._gps_speed)

    def gps_latitude(self):
        return np.array(self._gps_latitude)

    def gps_longitude(self):
        return np.array(self._gps_longitude)

    def gps_coordinates(self):
        return np.array([self._gps_latitude, self._gps_longitude]).T

    def gps_points(self):
        if self._gps_points is None:
            self._gps_points, self._proj_src, self._proj_dst = \
                self.project_coordinates(self.gps_coordinates())
        return self._gps_points

    def press_time(self):
        return np.array(self._press_time)

    def press_seconds(self):
        return self.time_to_seconds(self.press_time())

    def press_altitude(self):
        return np.array(self._press_altitude)

    def press_pressure(self):
        return np.array(self._press_pressure)

    def press_distance(self):
        if self._press_distance is None:
            f = scipy.interpolate.interp1d(self.gps_time(), self.gps_distance(),
                                           bounds_error=False)
            self._press_distance = f(self.press_time())
        return self._press_distance

    def translated_position_test(self):
        r2d = pi/180.0
        P = np.array([self._gps_latitude, self._gps_longitude])
        B = np.array(self._gps_bearing)
        S = self.gps_speed()
        return P + np.array([np.cos(B*r2d)*S, np.sin(B*r2d)*S])

    @staticmethod
    def project_coordinates(coords, proj_src=None, proj_dst=None):
        if not proj_src:
            proj_src = pyproj.Proj('+init=EPSG:4326')
        if not proj_dst:
            lat_0 = np.mean(coords[:, 0])
            lon_0 = np.mean(coords[:, 1])
            proj_dst = pyproj.Proj('+proj=aeqd +lat_0=%.8f +lon_0=%.8f' % (lat_0, lon_0))
        points = [pyproj.transform(proj_src, proj_dst, lon, lat) for (lat, lon) in coords]
        return np.array(points), proj_src, proj_dst

    def match_points(self, coords, cutoff):
        gps_points = self.gps_points()
        points, _, _ = self.project_coordinates(coords, self._proj_src, self._proj_dst)
        tree = scipy.spatial.cKDTree(points)
        dist = list()
        ind = list()
        for p in gps_points:
            (d, i) = tree.query(p, distance_upper_bound=cutoff)
            dist.append(d)
            ind.append(i)

        ind = np.array(ind)
        return ind, ml.find(ind == coords.shape[0]), np.array(dist)

    def mean_offset(self, i, iw, a0, a1):
        return np.mean(np.delete(a0 - a1[i], iw))

    def mean_offset2(self, i, iw, a0, a1):
        return np.mean(np.delete(a0 - a1[i], iw)**2)

    def mean_sd(self, i, iw, a0, a1):
        return sqrt(self.mean_sd2(i, iw, a0, a1))

    def mean_sd2(self, i, iw, a0, a1):
        m = self.mean_offset(i, iw, a0, a1)
        return np.mean(np.delete(a0 - a1[i] + m, iw)**2)

    def statistics(self, a):
        a_min = a[0]
        a_max = a[0]
        a_gain = 0.0
        a_loss = 0.0

        for i in range(1, len(a)):
            if a[i] < a_min:
                a_min = a[i]
            if a[i] > a_max:
                a_max = a[i]

            diff = a[i] - a[i-1]
            if diff > 0.0:
                a_gain += diff
            else:
                a_loss += diff

        return a_min, a_max, a_gain, a_loss, a[-1]-a[0]

    def smooth(self, a):
        filtern = 51
        W = signal.slepian(filtern, width=0.05)
        W = W/np.sum(W)
        s = signal.convolve(a, W, mode='valid')
        return np.hstack([[s[0]]*(filtern/2), s, [s[-1]]*(filtern/2)])

    def smooth_wavelet(self, data, levels=8, w='sym4', mode=pywt.MODES.sp1):
        w = pywt.Wavelet(w)
        a = data

        for i in range(levels):
            (a, d) = pywt.dwt(a, w, mode)

        coeff_list = [a, None] + [None] * (levels-1)
        rec = pywt.waverec(coeff_list, w)

        if len(data) == len(rec):
            return rec
        else:
            return rec[1:len(data)-len(rec)+1]

    def export_to_kml(self, file_name):
        coords = list()
        for i in range(len(self._gps_latitude)):
            coords.append((self._gps_longitude[i], self._gps_latitude[i]))

        kml = Kml()
        lin = kml.newlinestring(name="Track", description="A track.", coords=coords)
        lin.style.linestyle.color = 'ff0000ff'  # Red
        lin.style.linestyle.width = 2           # 10 pixels
        kml.save(file_name)

    def _find_altitude_pressure(self, pressure):
        if not self._pressure_msl:
            if self._last_altitude:
                self._pressure_msl = pressure/pow(1.0 - self.PRESSURE_FACTOR * self._last_altitude,
                                                  self.PRESSURE_EXPONENT)
                return self._last_altitude
            else:
                return None
        else:
            e = pow(pressure/self._pressure_msl, 1.0/self.PRESSURE_EXPONENT)
            return (1.0 - e)/self.PRESSURE_FACTOR
