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


class FilterBase:

    def on_gps(self, time, altitude, accuracy):
        pass

    def on_pressure(self, time, pressure):
        pass

    def execute(self, gps_events, pressure_events):
        ia, ip = 0, 0
        while True:
            do_gps = ia < len(gps_events)
            do_pressure = ip < len(pressure_events)
            if do_gps and do_pressure:
                if gps_events[ia][0] < pressure_events[ip][0]:
                    self.on_gps(*gps_events[ia])
                    ia += 1
                else:
                    self.on_pressure(*pressure_events[ip])
                    ip += 1
            elif do_gps:
                self.on_gps(*gps_events[ia])
                ia += 1
            elif do_pressure:
                self.on_pressure(*pressure_events[ip])
                ip += 1
            else:
                break


class SmootherBase:

    def on_gps(self, time, altitude, accuracy, backward):
        pass

    def on_pressure(self, time, pressure, backward):
        pass

    def execute(self, gps_events, pressure_events):
        # Forward events traversal
        ia, ip = 0, 0
        while True:
            last_pressure = ip + 1 == len(pressure_events)
            do_gps = ia < len(gps_events)
            do_pressure = ip < len(pressure_events)
            if do_gps and do_pressure:
                if gps_events[ia][0] < pressure_events[ip][0]:
                    self.on_gps(*gps_events[ia], False)
                    ia += 1
                else:
                    self.on_pressure(*pressure_events[ip], last_pressure)
                    ip += 1
            elif do_gps:
                self.on_gps(*gps_events[ia], False)
                ia += 1
            elif do_pressure:
                self.on_pressure(*pressure_events[ip], last_pressure)
                ip += 1
            else:
                break

        # Backward events traversal
        ia, ip = len(gps_events) - 1, len(pressure_events) - 2
        while True:
            do_gps = ia >= 0
            do_pressure = ip >= 0
            if do_gps and do_pressure:
                if gps_events[ia][0] > pressure_events[ip][0]:
                    self.on_gps(*gps_events[ia], True)
                    ia -= 1
                else:
                    self.on_pressure(*pressure_events[ip], True)
                    ip -= 1
            elif do_gps:
                self.on_gps(*gps_events[ia], True)
                ia -= 1
            elif do_pressure:
                self.on_pressure(*pressure_events[ip], True)
                ip -= 1
            else:
                break
