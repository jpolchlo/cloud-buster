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
import ast
import copy
import json
import os
import re

import shapely.affinity  # type: ignore
import shapely.geometry  # type: ignore
import shapely.ops  # type: ignore


def cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--backstop', required=False,
                        default=True, type=ast.literal_eval)
    parser.add_argument('--coverage-count',
                        required=False, default=3, type=int)
    parser.add_argument('--max-selections', required=False, type=int)
    parser.add_argument('--input', required=True, type=str)
    parser.add_argument('--output', required=True, type=str)
    parser.add_argument('--date-regexp', required=False, type=str)
    parser.add_argument('--name-regexp', required=False, type=str)
    parser.add_argument('--minclouds', default=0.0, type=float)
    parser.add_argument('--max-uncovered', default=5e-4, type=float)
    return parser


if __name__ == '__main__':
    args = cli_parser().parse_args()

    with open(args.input, 'r') as f:
        response = json.load(f)

    results = response.get('results')
    results = list(filter(lambda s: float(
        s['sceneMetadata']['cloudyPixelPercentage']) >= args.minclouds, results))

    if args.name_regexp:
        results = list(filter(lambda r: re.search(
            args.name_regexp, r.get('name')) is not None, results))

    if args.date_regexp:
        results = list(filter(lambda r: re.search(
            args.date_regexp, r.get('createdAt')) is not None, results))

    for result in results:
        result['dataShape'] = shapely.geometry.shape(
            result.get('dataFootprint'))

    shape = shapely.geometry.shape(response.get('aoi'))
    shapes = []
    for i in range(args.coverage_count):
        shapes.append(copy.copy(shape))
    backstop = copy.copy(shape)

    selections = []

    def not_backstopped():
        area = backstop.area
        print(area)
        return area > args.max_uncovered

    def not_covered():
        areas = list(map(lambda s: s.area, shapes))
        print(areas)
        return sum(areas) > args.max_uncovered

    def enough_selected():
        return (args.max_selections is not None) and (len(selections) > args.max_selections)

    # Primary coverage
    while (not_covered()) and (not enough_selected()) and (len(results) > 0):
        i_best = -1
        j_best = -1
        area_best = 0.0
        for i in range(len(results)):
            for j in range(len(shapes)):
                raw_area = results[i].get(
                    'dataShape').intersection(shapes[j]).area
                non_cloudy_pct = 1.0 - \
                    float(results[i].get('sceneMetadata').get(
                        'cloudyPixelPercentage'))/100.0
                area = raw_area * non_cloudy_pct
                if area > area_best:
                    j_best = j
                    i_best = i
                    area_best = area
        if area_best <= 0.0:
            break
        shapes[j_best] = shapes[j_best].difference(
            results[i_best].get('dataShape'))
        selections.append(results[i_best])
        results = results[0:i_best] + results[i_best+1:]

    # Backstop
    while (not_backstopped() and args.backstop) and (not enough_selected()) and (len(results) > 0):
        i_best = -1
        area_best = 0.0
        for i in range(len(results)):
            raw_area = results[i].get('dataShape').intersection(backstop).area
            non_cloudy_pct = 1.0 - \
                float(results[i].get('sceneMetadata').get(
                    'cloudyPixelPercentage'))/100.0
            area = raw_area * non_cloudy_pct
            if area > area_best:
                i_best = i
                area_best = area
        if area_best <= 0.0:
            break
        backstop = backstop.difference(results[i_best].get('dataShape'))
        results[i_best]['backstop'] = True
        selections.append(results[i_best])
        results = results[0:i_best] + results[i_best+1:]

    print(len(selections))
    for selection in selections:
        del selection['dataShape']
    selections = {
        'bounds': shape.bounds,
        'selections': selections
    }

    # Render results
    if (not args.backstop or not not_backstopped()) and (not not_covered()):
        with open(args.output, 'w') as f:
            json.dump(selections, f, sort_keys=True,
                      indent=4, separators=(',', ': '))
    else:
        print('ERROR: not covered')
        with open(args.output + '.ERROR', 'w') as f:
            if args.coverage_count == 0:
                selections['selections'] = selections['selections'][0:1]
            json.dump(selections, f, sort_keys=True,
                      indent=4, separators=(',', ': '))
