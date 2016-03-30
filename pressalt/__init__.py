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

from .record_readers import *
from .gps_pressure_reader import *
from .heart_rate_reader import *
from .altitude_filter import *
from .altitude_rate_filter import *
from .altitude_rate_smoother import *

try:
    from .elevation import *
except ImportError as e:
    warnings.warn("Elevation module is not available: %s" % str(e))