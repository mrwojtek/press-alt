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
import uuid
import struct
import numpy as np

DEVICE_NAME_UUID = uuid.UUID('{00002a00-0000-1000-8000-00805f9b34fb}')
APPEARANCE_UUID = uuid.UUID('{00002a01-0000-1000-8000-00805f9b34fb}')
HEART_RATE_UUID = uuid.UUID('{00002a37-0000-1000-8000-00805f9b34fb}')
BODY_SENSOR_LOCATION_UUID = uuid.UUID('{00002a38-0000-1000-8000-00805f9b34fb}')
SYSTEM_ID_UUID = uuid.UUID('{00002a23-0000-1000-8000-00805f9b34fb}')
MODEL_NUMBER_STRING_UUID = uuid.UUID('{00002a24-0000-1000-8000-00805f9b34fb}')
SERIAL_NUMBER_STRING_UUID = uuid.UUID('{00002a25-0000-1000-8000-00805f9b34fb}')
FIRMWARE_REVISION_STRING_UUID = uuid.UUID('{00002a26-0000-1000-8000-00805f9b34fb}')
HARDWARE_REVISION_STRING_UUID = uuid.UUID('{00002a27-0000-1000-8000-00805f9b34fb}')
SOFTWARE_REVISION_STRING_UUID = uuid.UUID('{00002a28-0000-1000-8000-00805f9b34fb}')
MANUFACTURER_NAME_STRING_UUID = uuid.UUID('{00002a29-0000-1000-8000-00805f9b34fb}')
BATTERY_LEVEL_UUID = uuid.UUID('{00002a19-0000-1000-8000-00805f9b34fb}')

HEART_RATE_FORMAT_MASK = 0x01
HEART_RATE_FORMAT_UINT8 = 0x00
HEART_RATE_FORMAT_UINT16 = 0x01
HEART_RATE_CONTACT_MASK = 0x06
HEART_RATE_CONTACT_NOT_DETECTED = 0x04
HEART_RATE_CONTACT_DETECTED = 0x06
HEART_RATE_ENERGY_EXPANDED_MASK = 0x08
HEART_RATE_ENERGY_EXPANDED_PRESENT = 0x08
HEART_RATE_RR_INTERVALS_MASK = 0x10
HEART_RATE_RR_INTERVALS_PRESENT = 0x10


class HeartRateReader(RecordReader):

    def __init__(self):
        RecordReader.__init__(self)

        self.metadata = {}
        self.milliseconds = []
        self.flags = []
        self.values = []
        self.energies_expanded = []
        self.rr_intervals = []

    def seconds(self):
        return self.time_to_seconds(np.array(self.milliseconds))

    def expand_rr_intervals(self):
        milliseconds = []
        rr_intervals = []
        for i in range(len(self.milliseconds)):
            if self.rr_intervals[i] is not None:
                for rr in self.rr_intervals[i]:
                    milliseconds.append(self.milliseconds[i])
                    rr_intervals.append(rr)
        return self.time_to_seconds(np.array(milliseconds)), rr_intervals
      
    def on_ble(self, device, millisecond, ble_uuid, value):
        self.update_time(millisecond)
        if ble_uuid == DEVICE_NAME_UUID:
            self.on_device_name(millisecond, value.decode('utf-8'))
        if ble_uuid == APPEARANCE_UUID:
            self.on_appearance(millisecond, *struct.unpack('H', value))
        elif ble_uuid == HEART_RATE_UUID:
            self.on_heart_rate_measurement(millisecond,
                                           *self.__decode_heart_rate_measurement(value))
        elif ble_uuid == BODY_SENSOR_LOCATION_UUID:
            self.on_body_sensor_location(millisecond, int(value[0]))
        elif ble_uuid == SYSTEM_ID_UUID:
            self.on_system_id(millisecond, *struct.unpack('Q', value))
        elif ble_uuid == MODEL_NUMBER_STRING_UUID:
            self.on_model_number_string(millisecond, value.decode('utf-8'))
        elif ble_uuid == SERIAL_NUMBER_STRING_UUID:
            self.on_serial_number_string(millisecond, value.decode('utf-8'))
        elif ble_uuid == FIRMWARE_REVISION_STRING_UUID:
            self.on_firmware_revision_string(millisecond, value.decode('utf-8'))
        elif ble_uuid == HARDWARE_REVISION_STRING_UUID:
            self.on_hardware_revision_string(millisecond, value.decode('utf-8'))
        elif ble_uuid == SOFTWARE_REVISION_STRING_UUID:
            self.on_software_revision_string(millisecond, value.decode('utf-8'))
        elif ble_uuid == MANUFACTURER_NAME_STRING_UUID:
            self.on_manufacturer_name_string(millisecond, value.decode('utf-8'))
        elif ble_uuid == BATTERY_LEVEL_UUID:
            self.on_battery_level(millisecond, int(value[0]))

    @staticmethod
    def __decode_heart_rate_measurement(payload):
        def get_rr_intervals(pos):
            if flags & HEART_RATE_RR_INTERVALS_MASK == HEART_RATE_RR_INTERVALS_PRESENT:
                rr_intervals = []
                while len(payload) - pos > 2:
                    rr_intervals.append(*struct.unpack_from('H', payload, pos))
                    pos += 2
                return rr_intervals
            return None
            
        def get_energy_expanded(pos):
            if flags & HEART_RATE_ENERGY_EXPANDED_MASK == HEART_RATE_ENERGY_EXPANDED_PRESENT \
                    and len(payload) - pos > 2:
                return (struct.unpack_from('H', payload, pos),
                        get_rr_intervals(pos + 2))
            else:
                return None, get_rr_intervals(pos)
                
        def get_value(pos):
            if flags & HEART_RATE_FORMAT_MASK == HEART_RATE_FORMAT_UINT8 \
                    and len(payload) - pos > 1:
                value = int(payload[pos])
                return (value,) + get_energy_expanded(pos + 1)
            elif flags & HEART_RATE_FORMAT_MASK == HEART_RATE_FORMAT_UINT8 \
                    and len(payload) - pos > 2:
                value = struct.unpack_from('H', payload, pos)
                return (value,) + get_energy_expanded(pos + 2)
            else:
                return None, None, None

        if len(payload) > 0:
            flags = payload[0]
            return (flags,) + get_value(1)
        else:
            return None, None, None, None

    def on_appearance(self, millisecond, category):
        self.metadata['Appearance'] = category

    def on_device_name(self, millisecond, name):
        self.metadata['Device Name'] = name
    
    def on_heart_rate_measurement(self, millisecond, flags, value, energy_expanded, rr_intervals):
        self.milliseconds.append(millisecond)
        self.flags.append(flags)
        self.values.append(value)
        self.energies_expanded.append(energy_expanded)
        self.rr_intervals.append(rr_intervals)

    def on_body_sensor_location(self, millisecond, body_sensor_location):
        self.metadata['Body Sensor Location'] = body_sensor_location

    def on_system_id(self, millisecond, system_id):
        self.metadata['System ID'] = system_id

    def on_model_number_string(self, millisecond, model_number):
        self.metadata['Model Number'] = model_number

    def on_serial_number_string(self, millisecond, serial_number):
        self.metadata['Serial Number'] = serial_number

    def on_firmware_revision_string(self, millisecond, firmware_revision):
        self.metadata['Firmware Revision'] = firmware_revision

    def on_hardware_revision_string(self, millisecond, hardware_revision):
        self.metadata['Hardware Revision'] = hardware_revision

    def on_software_revision_string(self, millisecond, software_revision):
        self.metadata['Software Revision'] = software_revision

    def on_manufacturer_name_string(self, millisecond, manufacturer_name):
        self.metadata['Manufacturer Name'] = manufacturer_name

    def on_battery_level(self, millisecond, level):
        self.metadata['Battery Level'] = level
