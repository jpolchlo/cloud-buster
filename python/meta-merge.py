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
import json
import os


def cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dryrun', required=False,
                        default=False, type=ast.literal_eval)
    parser.add_argument('--input-path', required=True, type=str)
    parser.add_argument('--jobdef', required=True, type=str)
    parser.add_argument('--jobqueue', required=True, type=str)
    parser.add_argument('--merge', required=True, type=str)
    parser.add_argument('--name', required=True, type=str)
    parser.add_argument('--output-path', required=True, type=str)
    return parser


if __name__ == '__main__':
    args = cli_parser().parse_args()

    jobname = '{}-MERGE'.format(args.name)
    submission = ''.join([
        'aws batch submit-job ',
        '--job-name {} '.format(jobname),
        '--job-queue {} '.format(args.jobqueue),
        '--job-definition {} '.format(args.jobdef),
        '--container-overrides vcpus=8,memory=15000,',
        'command=./download_run.sh,{},'.format(args.merge),
        '--input-path,{},'.format(args.input_path),
        '--name,{},'.format(args.name),
        '--output-path,{}'.format(args.output_path)
    ])
    if args.dryrun:
        print(submission)
    else:
        os.system(submission)
