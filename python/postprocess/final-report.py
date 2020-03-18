#!/usr/bin/env python3

# The MIT License (MIT)
# =====================
#
# Copyright © 2020 Azavea
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the “Software”), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import argparse
import copy
import gzip
import json


def cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-json', help='The response',
                        required=True, type=str)
    parser.add_argument('--scramble-json',
                        help='The scramble response', required=False, type=str)
    parser.add_argument('--scramble-index',
                        help='The scramble index', required=False, type=int)
    parser.add_argument('--input-geojson',
                        help='The source report', required=True, type=str)
    parser.add_argument('--output', required=True, type=str)
    return parser


if __name__ == '__main__':
    args = cli_parser().parse_args()

    with open(args.input_json, 'r') as f:
        data_json = json.load(f)

    if args.scramble_json is not None and args.scramble_index is not None:
        with open(args.scramble_json, 'r') as f:
            data_json2 = json.load(f)

    with open(args.input_geojson, 'r') as f:
        data_geojson = json.load(f)

    for feature in data_geojson.get('features'):
        properties = feature.get('properties')
        index = int(properties.get('DN'))
        if (args.scramble_index is not None) and (index > args.scramble_index//2):
            index = index - args.scramble_index
            if index >= 0:
                properties['id'] = copy.copy(
                    data_json2.get('selections')[index].get('id'))
                for (k, v) in copy.copy(data_json2.get('selections')[index].get('sceneMetadata')).items():
                    properties[k] = v
        else:
            index = index - 1
            if index >= 0:
                properties['id'] = copy.copy(
                    data_json.get('selections')[index].get('id'))
                for (k, v) in copy.copy(data_json.get('selections')[index].get('sceneMetadata')).items():
                    properties[k] = v
        del properties['DN']

    with gzip.open(args.output, 'w') as f:
        json_str = json.dumps(data_geojson, sort_keys=True,
                              indent=4, separators=(',', ': ')) + '\n'
        json_data = json_str.encode()
        f.write(json_data)
