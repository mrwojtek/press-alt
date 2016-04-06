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

import codecs
import struct
import uuid
import sys


class RecordReaderError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class RecordReader:

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def update_time(self, millisecond):
        if not self.start_time:
            self.start_time = millisecond
        self.end_time = millisecond

    def expand_time(self, start_time, end_time):
        if start_time < self.start_time:
            self.start_time = start_time
        if end_time > self.end_time:
            self.end_time = end_time

    def time_range(self):
        return self.start_time, self.end_time

    def duration(self):
        return (self.end_time - self.start_time) / 1000.0

    def time_to_seconds(self, value):
        return (value - self.start_time) / 1000.0

    def time_to_unit(self, value):
        return (value - self.start_time) / float(self.end_time - self.start_time)

    def on_sensor(self, type, device, time, timestamp, values):
        # TODO: Support the remaining sensors
        if type == 6:
            self.on_pressure(time, values[0])
            
    def on_sensor_accuracy(self, type, device, time, accuracy, resolution, maximum):
        # TODO: Support the remaining sensors accuracies
        if type == 6:
            self.on_pressure_accuracy(time, accuracy, resolution, maximum)
            
    def on_start(self, time, start_time, version):
        pass

    def on_end(self, time, end_time, version, duration, moving_time, distance):
        pass

    def on_gps(self, millisecond, latitude, longitude, altitude_geoid, bearing, speed, accuracy,
               time):
        pass

    def on_accel(self, millisecond, ax, ay, az):
        pass

    def on_accel_accuracy(self, millisecond, accuracy, resolution, maximum):
        pass

    def on_gyro(self, millisecond, avx, avy, avz):
        pass

    def on_gyro_accuracy(self, millisecond, accuracy, resolution, maximum):
        pass

    def on_magn(self, millisecond, gx, gy, gz):
        pass

    def on_magn_accuracy(self, millisecond, accuracy, resolution, maximum):
        pass

    def on_pressure(self, millisecond, pressure):
        pass

    def on_pressure_accuracy(self, millisecond, accuracy, resolution, maximum):
        pass

    def on_temp(self, millisecond, temp):
        pass

    def on_temp_accuracy(self, millisecond, accuracy, resolution, maximum):
        pass

    def on_humi(self, millisecond, humi):
        pass

    def on_humi_accuracy(self, millisecond, accuracy, resolution, maximum):
        pass

    def on_light(self, millisecond, light):
        pass

    def on_light_accuracy(self, millisecond, accuracy, resolution, maximum):
        pass

    def on_prox(self, millisecond, prox):
        pass

    def on_prox_accuracy(self, millisecond, accuracy, resolution, maximum):
        pass

    def on_battery(self, millisecond, percent, voltage, temperature):
        pass

    def on_nmea(self, millisecond, timestamp, nmea):
        pass

    def on_ble(self, device, millisecond, ble_uuid, value):
        pass


class RecordToText(RecordReader):
    
    def __init__(self, file=sys.stdout):
        RecordReader.__init__(self)
        self.file = file
        self.sensor = {
            1: 'accel_%d',
            2: 'magn_%d',
            3: 'orient_%d',
            4: 'gyro_%d',
            5: 'light_%d',
            6: 'press_%d',
            8: 'prox_%d',
            9: 'grav_%d',
            10: 'lacc_%d',
            11: 'rotv_%d',
        }
        self.accuracy = {
            1: 'accel_%d_acc',
            2: 'magn_%d_acc',
            3: 'orient_%d_acc',
            4: 'gyro_%d_acc',
            5: 'light_%d_acc',
            6: 'press_%d_acc',
            8: 'prox_%d_acc',
            9: 'grav_%d_acc',
            10: 'lacc_%d_acc',
            11: 'rotv_%d_acc',
        }
      
    def on_start(self, time, start_time, version):
        print('start\tSensorsRecord\t%d\t%d\t%d' % (version, time, start_time), file=self.file)
        
    def on_end(self, time, end_time, version, duration, moving_time, distance):
        print('end\tSensorsRecord\t%d\t%d\t%d\t%d\t%d\t%f' %
              (version, time, end_time, duration, moving_time, distance), file=self.file)
       
    def on_sensor(self, type, device, time, timestamp, values):
        if type in self.sensor:
            s = '%s\t%d\t%d\t%d' % ((self.sensor[type] % device), time, timestamp, len(values))
            for value in values:
                s += '\t%f' % value
            print(s, file=self.file)
        else:
            print(type, device, time, values, file=self.file)
    
    def on_sensor_accuracy(self, type, device, time, accuracy, resolution, maximum):
        if type in self.accuracy:
            print('%s\t%d\t%d\t%d\t%d' % ((self.accuracy[type] % device), time, accuracy,
                                          resolution, maximum), file=self.file)
        else:
            print(type, device, time, accuracy, file=self.file)
    
    def on_gps(self, millisecond, latitude, longitude, altitude_geoid, bearing, speed, accuracy,
               time):
        print("gps\t%d\t%.8f\t%.8f\t%.3f\t%f\t%f\t%f\t%d" %
              (millisecond, latitude, longitude, altitude_geoid, bearing, speed, accuracy, time),
              file=self.file)
              
    def on_accel(self, millisecond, ax, ay, az):
        print("accel\t%d\t%f\t%f\t%f" % (millisecond, ax, ay, az), file=self.file)
    
    def on_accel_accuracy(self, millisecond, accuracy, resolution, maximum):
        print("accel_acc\t%d\t%d\t%f\t%f" % (millisecond, accuracy, resolution, maximum),
              file=self.file)
    
    def on_gyro(self, millisecond, avx, avy, avz):
        print("gyro\t%d\t%f\t%f\t%f" % (millisecond, avx, avy, avz),
              file=self.file)
    
    def on_gyro_accuracy(self, millisecond, accuracy, resolution, maximum):
        print("gyro_acc\t%d\t%d\t%f\t%f" % (millisecond, accuracy, resolution, maximum),
              file=self.file)
    
    def on_magn(self, millisecond, mx, my, mz):
        print("magn\t%d\t%f\t%f\t%f" % (millisecond, mx, my, mz),
              file=self.file)
    
    def on_magn_accuracy(self, millisecond, accuracy, resolution, maximum):
        print("magn_acc\t%d\t%d\t%f\t%f" % (millisecond, accuracy, resolution, maximum),
              file=self.file)
        
    def on_pressure(self, millisecond, pressure):
        print("press\t%d\t%f" % (millisecond, pressure), file=self.file)

    def on_pressure_accuracy(self, millisecond, accuracy, resolution, maximum):
        print("press_acc\t%d\t%d\t%f\t%f" % (millisecond, accuracy, resolution, maximum),
              file=self.file)
    
    def on_temp(self, millisecond, temp):
        print("temp\t%d\t%f" % (millisecond, temp), file=self.file)
    
    def on_temp_accuracy(self, millisecond, accuracy, resolution, maximum):
        print("temp_acc\t%d\t%d\t%f\t%f" % (millisecond, accuracy, resolution, maximum),
              file=self.file)
    
    def on_humi(self, millisecond, humi):
        print("humi\t%d\t%f" % (millisecond, humi), file=self.file)
    
    def on_humi_accuracy(self, millisecond, accuracy, resolution, maximum):
        print("humi_acc\t%d\t%d\t%f\t%f" % (millisecond, accuracy, resolution, maximum),
              file=self.file)
    
    def on_light(self, millisecond, light):
        print("light\t%d\t%f" % (millisecond, light), file=self.file)
    
    def on_light_accuracy(self, millisecond, accuracy, resolution, maximum):
        print("light_acc\t%d\t%d\t%f\t%f" % (millisecond, accuracy, resolution, maximum),
              file=self.file)
    
    def on_prox(self, millisecond, prox):
        print("prox\t%d\t%f" % (millisecond, prox), file=self.file)
    
    def on_prox_accuracy(self, millisecond, accuracy, resolution, maximum):
        print("prox_acc\t%d\t%d\t%f\t%f" % (millisecond, accuracy, resolution, maximum),
              file=self.file)
              
    def on_battery(self, millisecond, percent, voltage, temperature):
        print("bat\t%d\t%f\t%d\t%d" % (millisecond, percent, voltage, temperature),
              file=self.file)
              
    def on_nmea(self, millisecond, timestamp, nmea):
        print("nmea\t%d\t%d\t%s" % (millisecond, timestamp, nmea), file=self.file)
    
    def on_ble(self, device, millisecond, ble_uuid, value):
        print("ble_%d\t%d\t%s\t%s" % (device, millisecond, ble_uuid.hex,
                                      codecs.encode(value, 'hex').decode()), file=self.file)


class RecordBatteryToText(RecordReader):

    def on_battery(self, millisecond, percent, voltage, temperature):
        print("%d\tbat\t%f\t%d\t%d" % (millisecond, percent, voltage, temperature))


class RecordNmeaToText(RecordReader):

    def on_nmea(self, millisecond, timestamp, nmea):
        print("nmea\t%d\t%d\t%s" % (millisecond, timestamp, nmea))
        

def __read_binary_v10(millisecond, data_type, f, reader):
    if data_type == 1:
        (latitude, longitude, altitude_geoid, bearing, speed, accuracy, time)\
                = struct.unpack('!dddfffq', f.read(44))
        reader.on_gps(millisecond, latitude, longitude, altitude_geoid, bearing, speed, accuracy,
                      time)
    elif data_type == 2:
        (ax, ay, az) = struct.unpack('!fff', f.read(12))
        reader.on_accel(millisecond, ax, ay, az)
    elif data_type == 3:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_accel_accuracy(millisecond, acc, res, max_range)
    elif data_type == 4:
        (avx, avy, avz) = struct.unpack('!fff', f.read(12))
        reader.on_gyro(millisecond, avx, avy, avz)
    elif data_type == 5:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_gyro_accuracy(millisecond, acc, res, max_range)
    elif data_type == 6:
        (mx, my, mz) = struct.unpack('!fff', f.read(12))
        reader.on_magn(millisecond, mx, my, mz)
    elif data_type == 7:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_magn_accuracy(millisecond, acc, res, max_range)
    elif data_type == 8:
        pressure = struct.unpack('!f', f.read(4))[0]
        reader.on_pressure(millisecond, pressure)
    elif data_type == 9:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_pressure_accuracy(millisecond, acc, res, max_range)
    elif data_type == 10:
        temp = struct.unpack('!f', f.read(4))[0]
        reader.on_temp(millisecond, temp)
    elif data_type == 11:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_temp_accuracy(millisecond, acc, res, max_range)
    elif data_type == 12:
        humi = struct.unpack('!f', f.read(4))[0]
        reader.on_humi(millisecond, humi)
    elif data_type == 13:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_humi_accuracy(millisecond, acc, res, max_range)
    elif data_type == 14:
        light = struct.unpack('!f', f.read(4))[0]
        reader.on_light(millisecond, light)
    elif data_type == 15:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_light_accuracy(millisecond, acc, res, max_range)
    elif data_type == 16:
        prox = struct.unpack('!f', f.read(4))[0]
        reader.on_prox(millisecond, prox)
    elif data_type == 17:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_prox_accuracy(millisecond, acc, res, max_range)
    elif data_type == 18:
        (pct, voltage, temp) = struct.unpack('!fii', f.read(12))
        reader.on_battery(millisecond, pct, voltage, temp)
    elif data_type == 19:
        length, = struct.unpack('!i', f.read(4))
        nmea = f.read(length)[:-1]
        reader.on_nmea(millisecond, nmea)
    else:
        raise RecordReaderError('Binary data corruption (dt=%d)' % data_type)


def __read_binary_v11(ms, data_type, f, reader):
    if data_type == 1:
        (latitude, longitude, altitude_geoid, bearing, speed, accuracy, time)\
                = struct.unpack('!dddfffq', f.read(44))
        reader.on_gps(ms, latitude, longitude, altitude_geoid, bearing, speed, accuracy, time)
    elif data_type == 2:
        (ts, ax, ay, az) = struct.unpack('!qfff', f.read(20))
        reader.on_accel(ms, ax, ay, az)
    elif data_type == 3:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_accel_accuracy(ms, acc, res, max_range)
    elif data_type == 4:
        (ts, avx, avy, avz) = struct.unpack('!qfff', f.read(20))
        reader.on_gyro(ms, avx, avy, avz)
    elif data_type == 5:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_gyro_accuracy(ms, acc, res, max_range)
    elif data_type == 6:
        (ts, mx, my, mz) = struct.unpack('!qfff', f.read(20))
        reader.on_magn(ms, mx, my, mz)
    elif data_type == 7:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_magn_accuracy(ms, acc, res, max_range)
    elif data_type == 8:
        (ts, pressure) = struct.unpack('!qf', f.read(12))
        reader.on_pressure(ms, pressure)
    elif data_type == 9:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_pressure_accuracy(ms, acc, res, max_range)
    elif data_type == 10:
        (ts, temp) = struct.unpack('!qf', f.read(12))
        reader.on_temp(ms, temp)
    elif data_type == 11:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_temp_accuracy(ms, acc, res, max_range)
    elif data_type == 12:
        (ts, humi) = struct.unpack('!qf', f.read(12))
        reader.on_humi(ms, humi)
    elif data_type == 13:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_humi_accuracy(ms, acc, res, max_range)
    elif data_type == 14:
        (ts, light) = struct.unpack('!qf', f.read(12))
        reader.on_light(ms, light)
    elif data_type == 15:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_light_accuracy(ms, acc, res, max_range)
    elif data_type == 16:
        (ts, prox) = struct.unpack('!qf', f.read(12))
        reader.on_prox(ms, prox)
    elif data_type == 17:
        (acc, res, max_range) = struct.unpack('!iff', f.read(12))
        reader.on_prox_accuracy(ms, acc, res, max_range)
    elif data_type == 18:
        (pct, voltage, temp) = struct.unpack('!fii', f.read(12))
        reader.on_battery(ms, pct, voltage, temp)
    elif data_type == 19:
        (ts, length) = struct.unpack('!qi', f.read(12))
        nmea = f.read(length)[:-1]
        reader.on_nmea(ms, 0, nmea)
    else:
        raise RecordReaderError('Binary data corruption (dt=%d)' % data_type)


def __read_binary_v12(type, device, version, f, reader):
    if type == -7:
        time, timestamp, length = struct.unpack('!qqi', f.read(20))
        nmea = f.read(length)
        reader.on_nmea(time, timestamp, nmea)
    elif type == -6:
        time, latitude, longitude, altitude_geoid, bearing, speed, accuracy, timestamp\
            = struct.unpack('!qdddfffq', f.read(52))
        reader.on_gps(time, latitude, longitude, altitude_geoid, bearing, speed, accuracy,
                      timestamp)
    elif type == -5:
        time, percentage, voltage, temperature = struct.unpack('!qfii', f.read(20))
        reader.on_battery(time, percentage, voltage, temperature)
    elif type == -8:
        time, = struct.unpack('!q', f.read(8))
        ble_uuid = uuid.UUID(bytes=f.read(16))
        value = f.read(*struct.unpack('!i', f.read(4)))
        reader.on_ble(device, time, ble_uuid, value)
    elif type == -3:
        magic_word = b'SensorsRecord'
        length, magic, version, time, end_time, duration, moving_time, distance\
            = struct.unpack('!i%dsiqqqqd' % len(magic_word), f.read(48 + len(magic_word)))
        reader.on_end(time, end_time, version, duration, moving_time, distance)
    elif type > 0:
        accuracy = type % 2 == 1
        type //= 2
        if accuracy:
            time, accuracy = struct.unpack('!qi', f.read(12))
            if version >= 1300:
                resolution, maximum = struct.unpack('!ff', f.read(8))
            else:
                resolution, maximum = float(0), float(0)
            reader.on_sensor_accuracy(type, device, time, accuracy, resolution, maximum)
        else:
            time, timestamp, length = struct.unpack('!qqh', f.read(18))
            values = struct.unpack('!%df' % length, f.read(4 * length))
            reader.on_sensor(type, device, time, timestamp, values)
    else:
        raise RecordReaderError('Binary data corruption (type=%d)' % type)


def read_binary(log_file, reader, legacy=False):

    def read_legacy(time, version, read_fun):
        reader.on_start(time, 0, version)
        binary = f.read(10)
        while binary:
            data_type, time = struct.unpack('!hq', binary)
            read_fun(time, data_type, f, reader)
            binary = f.read(10)
            
    def read_new(time, start_time, version, read_fun):
        reader.on_start(time, start_time, version)
        binary = f.read(4)
        while binary:
            type, device = struct.unpack('!hh', binary)
            read_fun(type, device, version, f, reader)
            binary = f.read(4)
        
    magic_word = b'SensorsRecord'
    
    with open(log_file, 'rb') as f:
        data_type, = struct.unpack('!h', f.read(2))
        if data_type == -1:
            # Check the validity of a starting frame.
            zero, length, magic, version =\
                struct.unpack('!hi%dsi' % len(magic_word), f.read(10 + len(magic_word)))
            if zero != 0 or length != len(magic_word) or magic_word != magic:
                raise RecordReaderError('Record format not recognized')
            if version == 1200 or version == 1300 or version == 1301:
                time, start_time = struct.unpack('!qq', f.read(16))
                read_new(time, start_time, version, __read_binary_v12)
            else:
                raise RecordReaderError('Record version unknown: %d' % version)
        elif legacy:
            # This is old legacy code which was never released.
            version = 1000
            if data_type == 0:
                time, version = struct.unpack('!qi', f.read(12))
            else:
                time = struct.unpack('!q', f.read(8))
            if version == 1000:
                __read_binary_v10(time, data_type, f, reader)
                read_legacy(time, version, __read_binary_v10)
            elif version == 1100:
                read_legacy(time, version, __read_binary_v11)
            else:
                raise RecordReaderError('Legacy format version error: %d' % version)
        else:
            raise RecordReaderError('Invalid binary file format')

    return reader


def read_text(log_file, sensors_reader):
    with open(log_file, 'r') as f:
        for line in f:
            values = line[:-1].split('\t')
            
            if len(values) < 2:
                continue
            
            try:
                millisecond = int(values[0])
                data_type = values[1]
                
                if data_type == 'gyro_acc':
                    pass
                elif data_type == 'prox':
                    pass
                elif data_type == 'gyro':
                    pass
                elif data_type == 'accel_acc':
                    pass
                elif data_type == 'accel':
                    pass
                elif data_type == 'magn_acc':
                    pass
                elif data_type == 'press_acc':
                    pressure_accuracy = int(values[2])
                    sensors_reader.on_pressure_accuracy(millisecond, pressure_accuracy, None, None)
                elif data_type == 'light_acc':
                    pass
                elif data_type == 'prox_acc':
                    pass
                elif data_type == 'light':
                    pass
                elif data_type == 'press':
                    pressure = float(values[2])
                    sensors_reader.on_pressure(millisecond, pressure)
                elif data_type == 'gps':
                    latitude = float(values[2])
                    longitude = float(values[3])
                    altitude_geoid = float(values[4])
                    bearing = float(values[5])
                    speed = float(values[6])
                    accuracy = float(values[7])
                    time = int(values[8])
                    sensors_reader.on_gps(millisecond, latitude, longitude, altitude_geoid,
                                          bearing, speed, accuracy, time)
                elif data_type == 'magn':
                    pass
            except ValueError:
                pass
    return sensors_reader
