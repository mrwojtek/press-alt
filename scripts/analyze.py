#!/usr/bin/env python3
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

import argparse
import pressalt
import warnings
import matplotlib.pyplot as plt
import pywt


def make_plot(reader, filter, press_alt, elevation, geoid, heart_rate, output, x_axis, axis_1,
              axis_2, width, height, dpi, legend):

    def get_gps_x():
        nonlocal gps_x
        if gps_x is None:
            if x_axis == 'Time':
                gps_x = reader.gps_seconds()
            else:
                gps_x = reader.gps_distance() / 1000
        return gps_x

    def get_press_x():
        nonlocal press_x
        if press_x is None:
            if x_axis == 'Time':
                press_x = reader.press_seconds()
            else:
                press_x = reader.press_distance() / 1000
        return press_x

    def fill_axis(ax, variables):
        label = None
        if variables is not None:
            for v in variables:
                if label is None:
                    label = variables_unit_label[v]
                if v == 'alt_gps':
                    ax.plot(get_gps_x(), reader.gps_altitude(), variables_color[v],
                            label=variables_label[v])
                elif v == 'alt_press':
                    ax.plot(get_press_x(), reader.press_altitude(), variables_color[v],
                            label=variables_label[v])
                elif v == 'alt_filt':
                    ax.plot(get_press_x(), press_alt, variables_color[v],
                            label=variables_label[v])
                elif v == 'alt_dem':
                    if elevation is None:
                        raise ValueError('No dem data for elevation plot')
                    gps_lon = reader.gps_longitude()
                    gps_lat = reader.gps_latitude()
                    ax.plot(get_gps_x(), elevation.values(gps_lon, gps_lat, geoid=geoid),
                            variables_color[v], label=variables_label[v])
                elif v == 'alt_filt_sd':
                    alt = filter.altitude()
                    alt_sd = filter.altitude_sd()
                    ax.fill_between(get_press_x(), alt - alt_sd, alt + alt_sd,
                                    facecolor=variables_color[v], edgecolor=variables_color[v],
                                    alpha=0.25)
                elif v == 'press':
                    ax.plot(get_press_x(), reader.press_pressure(), variables_color[v],
                            label=variables_label[v])
                elif v == 'press_msl':
                    ax.plot(get_press_x(), filter.pressure_msl(), variables_color[v],
                            label=variables_label[v])
                elif v == 'speed_gps':
                    ax.plot(get_gps_x(), reader.gps_speed()*3.6, variables_color[v],
                            label=variables_label[v])
                elif v == 'bearing_gps':
                    ax.plot(get_gps_x(), reader.gps_bearing(), variables_color[v],
                            label=variables_label[v])
                elif v == 'heart_rate':
                    if x_axis != 'Time':
                        raise ValueError('Heart rate requires time on horizontal axis')
                    ax.plot(heart_rate.seconds(), heart_rate.values, variables_color[v],
                            label=variables_label[v])
                elif v == 'heart_rr':
                    if x_axis != 'Time':
                        raise ValueError('RR intervals require time on horizontal axis')
                    time, rr = heart_rate.expand_rr_intervals()
                    ax.plot(time, rr, 'o', color=variables_color[v], label=variables_label[v])
        return label

    gps_x = None
    press_x = None

    fig = plt.figure(figsize=(width, height), dpi=dpi)

    ax1 = fig.add_subplot(111)
    ax1.set_xlabel(x_unit_label[x_axis])
    label1 = fill_axis(ax1, axis_1)
    if label1 is not None:
        ax1.set_ylabel(label1)

    ax2 = ax1.twinx()
    label2 = fill_axis(ax2, axis_2)
    if label2 is not None:
        ax2.set_ylabel(label2)

    if legend is not None:
        handles1, labels1 = ax1.get_legend_handles_labels()
        handles2, labels2 = ax2.get_legend_handles_labels()
        fig.legend(handles1 + handles2, labels1 + labels2, loc=legend, prop={'size': 9})

    if output is not None:
        fig.savefig(output)
    else:
        plt.pause(0)


def process_arguments(args):

    def check_unit(variables):
        if variables is not None:
            unit = None
            for v in variables:
                if unit is None:
                    unit = variables_unit_label[v]
                elif unit != variables_unit_label[v]:
                    return False
        return True

    def needs_filter(variables):
        if variables is not None:
            for v in variables:
                if v in variables_filtered:
                    return True
        return False

    def needs_heart_rate(variables):
        if variables is not None:
            for v in variables:
                if v in variables_heart_rate:
                    return True
        return False

    def read_file(file, reader, legacy):
        if file.endswith('.log') or file.endswith('.txt'):
            return pressalt.read_text(file, reader)
        else:
            return pressalt.read_binary(file, reader, legacy)

    if args.dem is not None:
        # Import and load the SRTM elevation data
        elevation = pressalt.GeoFiles(args.dem)
        if args.geoid is not None:
            try:
                import PyGeographicLib
                geoid = PyGeographicLib.Geoid(args.geoid)
            except ImportError as e:
                warnings.warn("PyGeographicLib module is not available: %s" % str(e))
                raise
        else:
            geoid = None
    else:
        elevation = None
        geoid = None

    reader = read_file(args.file, pressalt.GpsPressureReader(), args.legacy)

    if args.kml is not None:
        reader.export_to_kml(args.kml)

    if not check_unit(args.axis_1):
        raise ValueError('Unit mismatch for axis 1')
    if not check_unit(args.axis_2):
        raise ValueError('Unit mismatch for axis 2')

    if needs_filter(args.axis_1) or needs_filter(args.axis_2):
        if args.dpss_smooth and args.wavelet_smooth:
            raise ValueError('Only one wavelet or dpss post-smoother can be used at once')
        filter = filters[args.filter]()
        filter.execute(reader.gps_events, reader.press_events)
        if args.dpss_smooth:
            press_alt = reader.smooth(filter.altitude(), args.dpss_n, args.dpss_width)
        elif args.wavelet_smooth:
            press_alt = reader.smooth_wavelet(filter.altitude(), args.wavelet_levels, args.wavelet)
        else:
            press_alt = filter.altitude()
    else:
        filter = None
        press_alt = None

    if needs_heart_rate(args.axis_1) or needs_heart_rate(args.axis_2):
        heart_rate = read_file(args.file, pressalt.HeartRateReader(), args.legacy)
        heart_rate.expand_time(*reader.time_range())
        reader.expand_time(*heart_rate.time_range())
    else:
        heart_rate = None

    make_plot(reader, filter, press_alt, elevation, geoid, heart_rate, args.output, args.x_unit,
              args.axis_1, args.axis_2, args.width, args.height, args.dpi, args.legend)


LABEL_ALTITUDE = 'Altitude [m]'
LABEL_PRESSURE = 'Pressure [hPa]'
LABEL_VELOCITY = 'Velocity [km/h]'
LABEL_ANGLE = 'Angle [°]'
LABEL_BPM = 'Rate [bpm]'
LABEL_INTERVAL = 'Interval [ms]'

filters = {'AltitudeFilter': pressalt.AltitudeFilter,
           'AltitudeRateFilter': pressalt.AltitudeRateFilter,
           'AltitudeRateSmoother': pressalt.AltitudeRateSmoother}
filters_name = ['AltitudeFilter', 'AltitudeRateFilter', 'AltitudeRateSmoother']

variables = ['alt_gps', 'alt_press', 'alt_filt', 'alt_filt_sd', 'alt_dem', 'press', 'press_msl',
             'speed_gps', 'bearing_gps', 'heart_rate', 'heart_rr']
variables_unit_label = {'alt_gps': LABEL_ALTITUDE,
                        'alt_press': LABEL_ALTITUDE,
                        'alt_filt': LABEL_ALTITUDE,
                        'alt_filt_sd': LABEL_ALTITUDE,
                        'alt_dem': LABEL_ALTITUDE,
                        'press': LABEL_PRESSURE,
                        'press_msl': LABEL_PRESSURE,
                        'speed_gps': LABEL_VELOCITY,
                        'bearing_gps': LABEL_ANGLE,
                        'heart_rate': LABEL_BPM,
                        'heart_rr': LABEL_INTERVAL}
variables_label = {'alt_gps': 'GPS Altitude',
                   'alt_press': 'Pressure Altitude',
                   'alt_filt': 'Filtered Altitude',
                   'alt_filt_sd': None,
                   'alt_dem': 'SRTM Altitude',
                   'press': 'Pressure',
                   'press_msl': 'MSL Pressure',
                   'speed_gps': 'Speed',
                   'bearing_gps': 'Bearing',
                   'heart_rate': 'Heart Rate',
                   'heart_rr': 'RR Interval'}
variables_color = {'alt_gps': '#546e7a',      # Blue Grey
                   'alt_press': '#9c27b0',    # Purple
                   'alt_filt': '#4caf50',     # Green
                   'alt_filt_sd': '#4caf50',  # Green
                   'alt_dem': '#ff9800',      # Orange
                   'press': '#2196f3',        # Blue,
                   'press_msl': '#009688',    # Teal
                   'speed_gps': '#795548',    # Brown
                   'bearing_gps': '#0097a7',  # Cyan
                   'heart_rate': '#f44336',   # Red
                   'heart_rr': '#689f38'}     # Light Green
variables_filtered = {'alt_filt', 'alt_filt_sd', 'press_msl'}
variables_heart_rate = {'heart_rate', 'heart_rr'}

x_unit = ['Time', 'Distance']
x_unit_label = {'Time': 'Time [s]', 'Distance': 'Distance [km]'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert binary recording to the text file.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('file', type=str,
                        help='Recording file, for *.log or *.txt files text reader is used.')
    parser.add_argument('-o', '--output', dest='output', help='Output image file.')
    parser.add_argument('-k', '--kml', dest='kml', help='Output kml file.')
    parser.add_argument('-d', '--dem', dest='dem', nargs='+', help='Digital elevation map files.')
    parser.add_argument('-g', '--geoid', dest='geoid', help='Geoid model to use as described in ' +
                        'http://geographiclib.sourceforge.net/html/geoid.html. ' +
                        'Used with --dem option.')
    parser.add_argument('-f', dest='filter', choices=filters_name, default='AltitudeRateSmoother',
                        help='Filtering algorithm to use.')
    parser.add_argument('-x', dest='x_unit', choices=x_unit, default='Time',
                        help='Unit of the horizontal axis.')
    parser.add_argument('-1', dest='axis_1', choices=variables, nargs='+',
                        help='Variable to be plotted on a first vertical axis.')
    parser.add_argument('-2', dest='axis_2', choices=variables, nargs='+',
                        help='Variable to be plotted on a second vertical axis.')
    parser.add_argument('--legacy', action='store_true', help='Use legacy binary mode.')
    parser.add_argument('--width', dest='width', type=float, default=6.4, help='Plot width.')
    parser.add_argument('--height', dest='height', type=float, default=3.6, help='Plot height.')
    parser.add_argument('--dpi', dest='dpi', type=float, default=100, help='Plot height.')
    parser.add_argument('--legend', dest='legend', help='Plot legend location.')
    parser.add_argument('--dpss-smooth', dest='dpss_smooth', action='store_true',
                        help='Smooth the filtered results using digital Slepian window.')
    parser.add_argument('--dpss-n', dest='dpss_n', type=int, default=51,
                        help='Digital Slepian window size.')
    parser.add_argument('--dpss-width', dest='dpss_width', type=float, default=0.5,
                        help='Digital Slepian window width.')
    parser.add_argument('--wavelet-smooth', dest='wavelet_smooth', action='store_true',
                        help='Smooth the filtered results using wavelet cut-off.')
    parser.add_argument('--wavelet-levels', dest='wavelet_levels', type=int, default=8,
                        help='Wavelet level for smoothing cut-off.')
    parser.add_argument('--wavelet', choices=pywt.wavelist(), dest='wavelet', default='sym4',
                        help='Wavelet function to use, see pywt.wavelist().')


    args = parser.parse_args()
    process_arguments(args)
