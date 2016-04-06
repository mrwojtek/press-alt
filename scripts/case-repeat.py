#!/usr/bin/env python
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

import glob
import warnings
import pressalt
import matplotlib.patches
import matplotlib.pyplot as plt
import numpy as np


def plot_plot(file, fig, ax, tight, xlabel, ylabel, loc, title=None):
    if tight:
        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.tick_params(axis='both', which='major', labelsize=9)
        if title is not None:
            ax.set_title(title, fontsize=9)
            fig.subplots_adjust(0.1, 0.13, 0.985, 0.93)
        else:
            fig.subplots_adjust(0.1, 0.13, 0.985, 0.97)
    else:
        ax.set_xlabel(xlabel, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.tick_params(axis='both', which='major', labelsize=9)
        if title is not None:
            ax.set_title(title, fontsize=12)
            fig.subplots_adjust(0.13, 0.15, 0.95, 0.9)
        else:
            fig.subplots_adjust(0.13, 0.15, 0.95, 0.95)

    if file is not None:
        fig.savefig(file)
    else:
        plt.pause(0)


def plot_altitudes(filters, altitude, elevation, file, title, tight=True, width=6.4, height=3.6,
                   dpi=100):
    x_lim = [-0.1, 9.5]
    y_lim = [85, 135]

    fig = plt.figure(figsize=(width, height), dpi=dpi)
    ax = fig.add_subplot(111)
    ax.add_patch(matplotlib.patches.Rectangle((2.45, 85.0), 8.0-2.45, 135-85, color='#E6F0ED'))

    for f, reader, filter in filters:
        dist, alt = altitude(f, reader, filter)
        ax.plot(dist/1000.0, alt)

    if elevation is not None:
        gps_dist, gps_elev = elevation
        ax.plot(gps_dist/1000.0, gps_elev, '#ff6f00', alpha=0.9, label='SRTM')

    ax.set_xlim(x_lim)
    ax.set_ylim(y_lim)

    plot_plot(file, fig, ax, tight, 'Distance [km]', 'Altitude [m]', 'upper left', title)


def altitude_gps(file,reader, filter):
    return reader.gps_distance(), reader.gps_altitude()


def altitude_press(file, reader, filter):
    return reader.press_distance(), filter.altitude()


class AltitudePressMoved:

    def __init__(self, ref_reader, ref_filter, smooth=False):
        self.offset = -3.0
        self.ref_reader = ref_reader
        self.ref_alt = ref_filter.altitude_gps()
        self.ref_ind = range(1, self.ref_alt.shape[0] + 1)
        self.ref_dist = ref_reader.gps_distance()
        self.smooth = smooth

    def __call__(self, file, reader, filter):
        if self.smooth:
            alt = reader.smooth_wavelet(filter.altitude_gps(), 4)
        else:
            alt = filter.altitude_gps()
        i, iw, d = self.ref_reader.match_points(reader.gps_coordinates(), 10.0)
        alt_n = np.concatenate((alt, [np.NaN]))
        m = self.ref_reader.mean_offset(i, iw, self.ref_alt, alt_n)
        sd = self.ref_reader.mean_sd(i, iw, self.ref_alt, alt_n)
        print('file=%s, missing=%f%%, mean_offset=%f, std_dev=%f' %
              (file, 100.0*len(iw)/len(i), m, sd))
        return self.ref_dist, alt_n[i] + m + self.offset

    def elevation(self, elev, geoid):
        if elev is not None:
            gps_lon = self.ref_reader.gps_longitude()
            gps_lat = self.ref_reader.gps_latitude()
            return self.ref_dist, elev.values(gps_lon, gps_lat, geoid=geoid)
        else:
            return None

try:
    # 90-m elevation data from http://srtm.csi.cgiar.org
    elevation = pressalt.GeoFiles(['srtm/srtm_40_02/srtm_40_02.tif',
                                   'srtm/srtm_41_02/srtm_41_02.tif',
                                   'srtm/srtm_41_05/srtm_41_05.tif'])
    # SRTM data is given with reference to the mean sea level surface.
    # https://sourceforge.net/p/geographiclib/code/ci/v1.46/tree/wrapper/python/
    try:
        import PyGeographicLib
        geoid = PyGeographicLib.Geoid("egm2008-1")
    except ImportError as e:
        warnings.warn("PyGeographicLib module is not available: %s" % str(e))
        raise
except (AttributeError, ImportError):
    elevation = None
    geoid = None

files = glob.glob('records/repeat/*')
files_g = set(glob.glob('records/repeat/*-g.*'))
filters = []
filters_g = []
for file in files:
    reader = pressalt.GpsPressureReader()
    if file.endswith('log'):
        pressalt.read_text(file, reader)
    else:
        pressalt.read_binary(file, reader, True)
    filter = pressalt.AltitudeRateSmoother()
    filter.execute(reader.gps_events, reader.press_events)
    filters.append((file, reader, filter))
    if file in files_g:
        filters_g.append((file, reader, filter))

plot_altitudes(filters_g, altitude_gps, None, 'repeat-gps-9.png', 'GPS Altitude', tight=True,
               width=7.0)
plot_altitudes(filters, altitude_press, None, 'repeat-press-16.png', 'Filtered Altitude',
               tight=True, width=7.0)

apm = AltitudePressMoved(filters[0][1], filters[0][2])
plot_altitudes(filters, apm, apm.elevation(elevation, geoid), 'repeat-press-moved-16.png',
               'Filtered Altitude (positioned)', tight=True, width=7.0)

apms = AltitudePressMoved(filters[0][1], filters[0][2], True)
plot_altitudes(filters, apms, apms.elevation(elevation, geoid), 'repeat-press-moved-smooth-16.png',
               'Filtered Altitude (positioned, smoothed)', tight=True, width=7.0)
