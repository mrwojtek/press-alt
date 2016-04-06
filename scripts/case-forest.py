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


def plot_altitude(file, tight, width, height, dpi, loc, title, x_min, x_turn, y_lim, gps_x=None,
                  gps_alt=None, gps_elev=None, press_x=None, press_alt=None, press_alt_sd=None):
    fig = plt.figure(figsize=(width, height), dpi=dpi)
    plt.ylim(y_lim)
    ax = fig.add_subplot(111)

    if gps_alt is not None:
        alpha = 0.9 if gps_elev is None and press_alt is None else 0.6
        ax.plot(gps_x, gps_alt, '#263238', alpha=alpha, label='GPS')
        ax.plot(2*x_turn - gps_x, gps_alt, '#263238', alpha=alpha-0.2)

    if gps_elev is not None:
        alpha = 0.9 if press_alt is None else 0.6
        ax.plot(gps_x, gps_elev, '#ff6f00', alpha=alpha, label='SRTM')
        ax.plot(2*x_turn - gps_x, gps_elev, '#ff6f00', alpha=alpha-0.2)

    if press_alt is not None:
        ax.plot(press_x, press_alt, '#f44336', label='Forth')
        ax.plot(2*x_turn - press_x, press_alt, '#4caf50', label='Back')
        if press_alt_sd is not None:
            ax.fill_between(press_x, press_alt - press_alt_sd, press_alt + press_alt_sd,
                            facecolor='#f44336', edgecolor='#f44336', alpha=0.25)
            ax.fill_between(2*x_turn - press_x, press_alt - press_alt_sd, press_alt + press_alt_sd,
                            facecolor='#4caf50', edgecolor='#4caf50', alpha=0.25)

    ax.set_xlim([x_min, x_turn])

    plot_plot(file, fig, ax, tight, 'Distance [km]', 'Altitude [m]', loc, title)

    if file is not None:
        fig.savefig(file)
    else:
        plt.pause(0)


def plot_forest(reader, filter, prefix, tight=True, width=6.4, height=3.6, dpi=100, elev=None,
                geoid=None):
    gps_dist = reader.gps_distance()/1000.0
    gps_alt = reader.gps_altitude()
    gps_lon = reader.gps_longitude()
    gps_lat = reader.gps_latitude()
    gps_elev = elev.values(gps_lon, gps_lat, geoid=geoid) if elev is not None else None
    press_dist = reader.press_distance()/1000.0
    press_alt = filter.altitude()
    press_alt_sd = filter.altitude_sd()

    x_min = -0.11
    x_turn = 3.11
    y_lim = ([105, 155])

    plot_altitude('%s-gps.png' % prefix, tight, width, height, dpi, 'upper right', None, x_min,
                  x_turn, y_lim, gps_dist, gps_alt)
    plot_altitude('%s-gps-srtm.png' % prefix, tight, width, height, dpi, 'upper right', None,
                  x_min, x_turn, y_lim, gps_dist, gps_alt, gps_elev)
    plot_altitude('%s-gps-srtm-press.png' % prefix, tight, width, height, dpi, 'upper right', None,
                  x_min, x_turn, y_lim, gps_dist, gps_alt, gps_elev, press_dist, press_alt)
    plot_altitude('%s-press-sd.png' % prefix, tight, width, height, dpi, 'upper right',
                  filter.__class__.__name__, x_min, x_turn, y_lim, None, None, None, press_dist,
                  press_alt, press_alt_sd)


def plot_pressures(reader, filters, prefix, tight=True, width=6.4, height=3.6, dpi=100):
    press_dist = reader.press_distance()/1000.0
    press_press = reader.press_pressure()

    x_lim = [-0.11, 6.33]
    y_lim = [1000, 1030]

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


# Import and load the SRTM elevation data
try:
    elevation = pressalt.GeoFiles(['srtm/srtm_40_02/srtm_40_02.tif',
                                   'srtm/srtm_41_02/srtm_41_02.tif',
                                   'srtm/srtm_41_05/srtm_41_05.tif'])
    try:
        import PyGeographicLib
        geoid = PyGeographicLib.Geoid("egm2008-1")
    except ImportError as e:
        warnings.warn("PyGeographicLib module is not available: %s" % str(e))
        raise
except (AttributeError, ImportError):
    elevation = None
    geoid = None

# Different filters for comparison
filters = [('forest-af', pressalt.AltitudeFilter(), '#3f51b5'),
           ('forest-arf', pressalt.AltitudeRateFilter(), '#8bc34a'),
           ('forest-ars', pressalt.AltitudeRateSmoother(), '#e91e63')]

# Read recorder file
reader = pressalt.read_binary('records/forest-20130728.bin', pressalt.GpsPressureReader(), True)
reader.export_to_kml('forest.kml')

# Filter and smooth the record
for prefix, filter, _ in filters:
    filter.execute(reader.gps_events, reader.press_events)
    plot_forest(reader, filter, prefix, tight=False, elev=elevation, geoid=geoid, width=7.0)
plot_pressures(reader, filters, 'forest', tight=False, width=7.0)
