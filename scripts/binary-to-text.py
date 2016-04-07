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

parser = argparse.ArgumentParser(description='Convert binary recording to the text file.')
parser.add_argument('file', type=str, help='File with a binary recording')
parser.add_argument('-o', '--output', dest='output',
                    help='Output file, writing to standard output when missing')
args = parser.parse_args()

if args.output is not None:
    with open(args.output, 'w') as f:
        pressalt.read_binary(args.file, pressalt.RecordToText(file=f))
else:
    pressalt.read_binary(args.file, pressalt.RecordToText())
