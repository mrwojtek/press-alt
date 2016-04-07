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

import warnings
import pressalt
import matplotlib.pyplot as plt


def plot_plot(file, fig, ax, tight, xlabel, ylabel, loc, title=None):
    if tight:
        ax.legend(loc=loc, prop={'size': 9})
        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.tick_params(axis='both', which='major', labelsize=9)
        if title is not None:
            ax.set_title(title, fontsize=9)
            fig.subplots_adjust(0.1, 0.13, 0.985, 0.93)
        else:
            fig.subplots_adjust(0.1, 0.13, 0.985, 0.97)
    else:
        ax.legend(loc=loc, prop={'size': 9})
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


def plot_altitude(file, tight, width, height, dpi, x_lim, y_lim, title=None, gps_x=None,
                  gps_alt=None, gps_elev=None, press_x=None, press_alt=None, press_alt_sd=None):

    fig = plt.figure(figsize=(width, height), dpi=dpi)
    plt.ylim(y_lim)
    ax = fig.add_subplot(111)

    if gps_alt is not None:
        alpha = 0.9 if gps_elev is None and press_alt is None else 0.6
        ax.plot(gps_x, gps_alt, '#263238', alpha=alpha, label='GPS')

    if gps_elev is not None:
        alpha = 0.9 if press_alt is None else 0.6
        ax.plot(gps_x, gps_elev, '#ff6f00', alpha=alpha, label='SRTM')

    if press_alt is not None:
        ax.plot(press_x, press_alt, '#e91e63', label='Filtered')
        if press_alt_sd is not None:
            ax.fill_between(press_x, press_alt - press_alt_sd, press_alt + press_alt_sd,
                            facecolor='#e91e63', edgecolor='#e91e63', alpha=0.25)

    ax.set_xlim(x_lim)
    plot_plot(file, fig, ax, tight, 'Distance [km]', 'Altitude [m]', 'upper left', title)


def plot_milos(reader, filter, prefix, tight=True, width=6.4, height=3.6, dpi=100, elev=None,
               geoid=None):
    gps_dist = reader.gps_distance() / 1000.0
    gps_alt = reader.gps_altitude()
    gps_lon = reader.gps_longitude()
    gps_lat = reader.gps_latitude()
    gps_elev = elev.values(gps_lon, gps_lat, geoid=geoid) if elev is not None else None
    press_dist = reader.press_distance() / 1000.0
    press_alt = filter.altitude()

    x_lim = [0, 16]
    y_lim = [30, 300]

    plot_altitude('%s-alt.png' % prefix, tight, width, height, dpi, x_lim, y_lim, None, gps_dist,
                  gps_alt, gps_elev, press_dist, press_alt)


def plot_altitudes(reader, filters, prefix, tight=True, width=6.4, height=3.6, dpi=100):
    press_dist = reader.press_distance()/1000.0

    x_lim = [0, 16]
    y_lim = [30, 300]

    fig = plt.figure(figsize=(width, height), dpi=dpi)
    ax = fig.add_subplot(111)

    for _, filter, color in filters:
        press_alt = filter.altitude()
        ax.plot(press_dist, press_alt, color, alpha=0.9, label='%s' % filter.__class__.__name__)
        # press_alt_sd = filter.altitude_sd()
        # ax.fill_between(press_dist, press_alt - press_alt_sd, press_alt + press_alt_sd,
        #                 facecolor=color, edgecolor=color, alpha=0.25)

    ax.set_xlim(x_lim)
    ax.set_ylim(y_lim)

    file = '%s-altitudes.png' % prefix if prefix is not None else None
    plot_plot(file, fig, ax, tight, 'Distance [km]', 'Altitude [m]', 'upper left',
              'Filtered Altitudes')


def plot_pressures(reader, filters, prefix, tight=True, width=6.4, height=3.6, dpi=100):
    press_dist = reader.press_distance()/1000.0
    press_press = reader.press_pressure()

    x_lim = [0, 16]
    y_lim = [980, 1050]

    fig = plt.figure(figsize=(width, height), dpi=dpi)
    ax = fig.add_subplot(111)

    ax.plot(press_dist, press_press, '#03a9f4', alpha=0.9, label='Measured')

    for _, filter, color in filters:
        ax.plot(press_dist, filter.pressure_msl(), color, alpha=0.9,
                label='MSL (%s)' % filter.__class__.__name__)

    ax.set_xlim(x_lim)
    ax.set_ylim(y_lim)

    file = '%s-pressures.png' % prefix if prefix is not None else None
    plot_plot(file, fig, ax, tight, 'Distance [km]', 'Pressure [hPa]', 'upper right', 'Pressures')


def initialize_elevation():
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
        return elevation, geoid
    except (AttributeError, ImportError):
        return None, None


if __name__ == '__main__':
    elevation, geoid = initialize_elevation()
    # Different filters for comparison
    filters = [('milos-af', pressalt.AltitudeFilter(), '#e91e63'),
               ('milos-arf', pressalt.AltitudeRateFilter(), '#8bc34a'),
               ('milos-ars', pressalt.AltitudeRateSmoother(), '#3f51b5')]

    # Read recorder file
    reader = pressalt.read_binary('records/milos-20130813.bin', pressalt.GpsPressureReader(), True)
    reader.export_to_kml('milos.kml')

    # Filter and smooth the record
    for prefix, filter, _ in filters:
        filter.execute(reader.gps_events, reader.press_events)
        plot_milos(reader, filter, prefix, tight=False, width=7.0, elev=elevation, geoid=geoid)
    plot_altitudes(reader, filters, 'milos', tight=False, width=7.0)
    plot_pressures(reader, filters, 'milos', tight=False, width=7.0)
