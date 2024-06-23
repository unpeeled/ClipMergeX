#!/usr/bin/python3
'''
ClipMergeX - Cut and Merge MTS to Videos.

A tool for cutting MTS files from MTS Files from camcorder (via CSV-File), add
auotmatic effects (date stamps, fading) and glue all together to one video in
h264, vp9, av1.

Project Site: https://github.com/unpeeled/ClipMergeX
'''
import argparse
import sys
from videator import VideoCollection

description=\
'''A tool for cutting MTS files from MTS Files from camcorder (via CSV-File),
add auotmatic effects (date stamps, fading) and glue all together to one video
in h264, h265, vp9, av1.
'''

parser = argparse.ArgumentParser(prog='ClipMergeX',
                                 description=description)

parser.add_argument('--input_dir', '-i' ,help='directory where MTS files are stored', required=True)
parser.add_argument('--csv_list', '-c', help='input csv list which filters / cuts the input')
parser.add_argument('--output_file', '-o', help='path to filename where the mp4/webm video shall be saved. [MP4: h264,aac|WEBM: vp9,opus]', required=True)
parser.add_argument('--timezone', '-tz', help='Timezone used to set date strings.', required=False, default='UTC')
parser.add_argument('--effects', help='Remove effects (time stamp, fading after day).', action=argparse.BooleanOptionalAction, default=True)
parser.add_argument('--codec', help='Video codec to select (supported: h264,h265,vp9,av1)', required=False)

args = parser.parse_args()

config = {}
config_elements = ['timezone', 'effects', 'codec']
for entry in config_elements:
    config[entry] = args.__dict__[entry]

video_collection = VideoCollection(args.input_dir, args.output_file, csv_file=args.csv_list, config=config)
video_collection.convert()
video_collection.concat()
video_collection.clean()
