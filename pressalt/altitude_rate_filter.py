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

from .filter_base import FilterBase
import numpy as np


class AltitudeRateFilter(FilterBase):

    PRESSURE_EXPONENT = 5.25588
    PRESSURE_FACTOR = 0.0000225577

    def __init__(self, gps_var_factor=6.0**2, pressure_var=0.3**2, pressure_smooth=1.0,
                 altitude_noise=1e-2, altitude_rate_noise=1e-4, pressure_noise=1e-5,
                 P0=np.diag([200.0, 50.0, 2.0])):
        self._gps_var_factor = gps_var_factor
        self._pressure_var = pressure_var
        self._pressure_smooth = pressure_smooth
        self._altitude_noise = altitude_noise
        self._altitude_rate_noise = altitude_rate_noise
        self._pressure_noise = pressure_noise
        self._P0 = P0

        self._altitude_gps = list()
        self._altitude_sd_gps = list()
        self._altitude = list()
        self._altitude_sd = list()
        self._pressure_msl = list()

        self._x = np.ones(3)*np.NaN
        self._P = np.ones((3, 3))*np.NaN

        self._started = False
        self._last_time = None
        self._last_altitude = None
        self._last_pressure = None

    def altitude_gps(self):
        return np.array(self._altitude_gps)

    def altitude_sd_gps(self):
        return np.array(self._altitude_sd_gps)

    def altitude(self):
        return np.array(self._altitude)

    def altitude_sd(self):
        return np.array(self._altitude_sd)

    def pressure_msl(self):
        return np.array(self._pressure_msl)

    def on_gps(self, time, altitude, accuracy):
        self._last_altitude = altitude
        if self._started:
            H = np.array([1.0, 0.0, 0.0])
            MR = np.array([accuracy * accuracy * self._gps_var_factor])
            self._on_measurement(altitude - self._x[0], H, MR)
        self._altitude_gps.append(self._x[0])
        self._altitude_sd_gps.append(self._P[0, 0])

    def on_pressure(self, time, pressure):

        # Simple filter for discarding very noisy pressure measurements, this
        # is more like a hack and requires improvement.
        if self._last_pressure is None or abs(self._last_pressure - pressure) < 2.0:
            if not self._started and self._last_altitude:
                # Filter initialization
                altitude_msl = self._last_altitude
                pressure_msl = pressure / pow(1.0 - self.PRESSURE_FACTOR * altitude_msl,
                                              self.PRESSURE_EXPONENT)
                self._x = np.array([altitude_msl, 0.0, pressure_msl])
                self._P = self._P0
                self._last_time = time
                self._started = True
            elif self._started:
                # Filter update operation
                dt = abs(time - self._last_time) / 1000.0

                F = np.array([[1.0,  dt, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 1.0]])

                Q = np.diag([self._altitude_noise,
                             self._altitude_rate_noise,
                             self._pressure_noise])

                # A priori covariance estimation
                self._P = F.dot(self._P.dot(F.T)) + Q * dt

                # Pressure measurement operation
                e, f = self.PRESSURE_EXPONENT, self.PRESSURE_FACTOR
                z, zd, p_msl = self._x
                H = np.array([-p_msl*e*f*pow(1.0 - f*z, e - 1.0),
                              0.0,
                              pow(1.0 - f*z, e)])
                MR = np.array([self._pressure_var])
                self._on_measurement(pressure - p_msl*pow(1.0 - f*z, e), H, MR)
                self._last_time = time

        # Update last pressure
        self._last_pressure = pressure

        # Append the measurement
        self._altitude.append(self._x[0])
        self._altitude_sd.append(self._P[0, 0])
        self._pressure_msl.append(self._x[2])

    def _on_measurement(self, r, H, MR):
        K = self._P.dot(H) / (H.dot(self._P.dot(H)) + MR)
        self._x += K.dot(r)
        self._P = (np.identity(3) - np.outer(K, H)).dot(self._P)
