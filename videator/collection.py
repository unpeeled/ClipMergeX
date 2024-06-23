import glob
import os
import datetime
import sys
import subprocess

from .video import Video

class VideoCollection():

    _input_dir = None
    _videos_per_day = None
    _output_file = None
    _ending = None
    _video_ending = None
    
    def __init__(self, input_dir, output_file, csv_file=None, config={}):
        self._input_dir = input_dir
        self._output_file = output_file
        self._ending = output_file.split('.')[-1]
        if self._ending == 'mp4':
            self._video_ending = 'ts'
        else:
            self._video_ending = self._ending
        self._config = config
        if csv_file:
            self._videos_per_day = self._read_csv(csv_file)
            return
        self._videos_per_day = self._read(input_dir)

    def _read(self, input_dir):
        input_dir = os.path.abspath(input_dir)
        input_files = glob.glob(f'{input_dir}/*.MTS')
        videos_per_day = {}

        for in_video in input_files:

            video = Video(in_video, self._video_ending, config=self._config)

            try:
                videos_per_day[video.date].append(video)
            except KeyError:
                videos_per_day[video.date] = []
                videos_per_day[video.date].append(video)

        for videos in videos_per_day.values():
            videos.sort(key = lambda x: x.mtime)

        return videos_per_day

    def _read_csv(self, csv_file):
        csv_file = open(csv_file)
        csv_lines = csv_file.read().splitlines()
        csv_file.close()
        videos_per_day = {}

        for line in csv_lines:

            entries = line.split(';')
            entry_type = entries[0]
            entry_name = os.path.abspath(os.path.join(self._input_dir, entries[1]))
            entries.pop(0)
            entries.pop(0)

            # FIX: Empty param column
            # TODO: Parse times correctly
            try:
                if entries[-1] == '':
                    entries.pop(-1)
            except KeyError:
                pass

            if entry_type == 'file':
                video = Video(entry_name, self._video_ending, params=entries, config=self._config)

            try:
                videos_per_day[video.date].append(video)
            except KeyError:
                videos_per_day[video.date] = []
                videos_per_day[video.date].append(video)

        for videos in videos_per_day.values():
            videos.sort(key = lambda x: x.mtime)

        return videos_per_day
    
    @staticmethod
    def _cmd_date(day, start):
        return f',drawtext=text=\'{day}\':x=(w/10):y=(9*h/10):fontsize=24:fontcolor=white:enable=\'between(t,{start+1},{start+6})'

    @staticmethod
    def _cmd_cut(param):
        if not param:
            return ''
        
        timestamps = param.split('-')
        cmd = f'-ss {timestamps[0]}'

        try:
            cmd += f' -to {timestamps[1]}'
        except IndexError:
            pass

        return cmd

    def _cmd_fade_in(self, start):
        return f',fade=t=in:st={start}:d=5'

    def _cmd_fade_out(self, length):
        
        return f',fade=t=out:st={length-5}:d=5'

    @property
    def _codec_name(self):
        codec = self._config['codec']
        if not codec:
            if self._ending == 'mp4':
                return 'h264'
            elif self._ending == 'webm':
                return 'vp9'
            elif self._ending == 'mkv':
                return 'av1'
            else:
                sys.exit(1)
        return codec

    @property
    def _codec(self):
        if self._codec_name == 'h264':
            return '-c:v libx264 -b:v 3M -c:a aac -b:a 96k'
        elif self._codec_name == 'vp9':
            return '-c:a libopus -b:a 96k -c:v libvpx-vp9 -b:v 2M'
        elif self._codec_name == 'h265':
            return '-c:a aac -b:a 96k -c:v libx265 -b:v 2M -x265-params'
        elif self._codec_name == 'av1':
            return '-c:v libsvtav1 -b:v 2M -c:a libopus -b:a 96k'
        sys.exit(1)

    @property
    def _scale(self):
        if self._ending == 'mp4':
            return '1280'
        elif self._ending == 'webm':
            return '1280'
        sys.exit(1)

    def convert(self):

        temp_file = open('temp_files.txt','w')

        days = sorted(self._videos_per_day.keys(),
                      key=lambda x: datetime.datetime.strptime(x, '%d/%m/%Y'))

        print('Converting:')
        for day in days:
            videos = self._videos_per_day[day]

            for index, video in enumerate(videos):
                fade_in = ""
                fade_out = ""
                cmd_date = ""

                if index == 0 and self._config['effects']:
                    fade_in = self._cmd_fade_in(video.first_part_start)
                    cmd_date = self._cmd_date(day, video.first_part_start)

                if index == len(videos)-1 and self._config['effects']:
                    fade_out = self._cmd_fade_out(video.last_part_end)

                video_parts = video.params

                if not video_parts:
                    video_parts = [None]

                for index, part in enumerate(video_parts):

                    if self._codec_name in ['h264']:
                        command = f'ffmpeg -loglevel warning -y -fflags +genpts -i {video.path} {self._cmd_cut(part)} -vf "scale={self._scale}:-2,setsar=1:1{fade_in}{fade_out}{cmd_date}" {self._codec} "{video.output_name(index)}"'
                    elif self._codec_name in ['vp9']:
                        command_part = f'ffmpeg -loglevel warning -y -fflags +genpts -i {video.path} {self._cmd_cut(part)} -vf "scale={self._scale}:-2,setsar=1:1{fade_in}{fade_out}{cmd_date}" {self._codec}'
                        command = f'{command_part} -pass 1 -an -f null /dev/null && {command_part} -pass 2 "{video.output_name(index)}"'
                    elif self._codec_name in ['h265']:
                        command_part = f'ffmpeg -loglevel warning -y -fflags +genpts -i {video.path} {self._cmd_cut(part)} -vf "scale={self._scale}:-2,setsar=1:1{fade_in}{fade_out}{cmd_date}" {self._codec}'
                        command = f'{command_part} pass=1 -an -f null /dev/null && {command_part} pass=2 "{video.output_name(index)}"'
                    elif self._codec_name in ['av1']:
                        # TODO: Check two pass encoding later (with newer versions) again. Currentliy not working.
                        # command_part = f'ffmpeg -loglevel warning -y -fflags +genpts -i {video.path} {self._cmd_cut(part)} -vf "setsar=1:1{fade_in}{fade_out}{cmd_date}" {self._codec}'
                        # command = f'{command_part} -pass 1 -an -f null /dev/null && {command_part} -pass 2 "{video.output_name(index)}"'
                        command = f'ffmpeg -loglevel warning -y -fflags +genpts -i {video.path} {self._cmd_cut(part)} -vf "setsar=1:1{fade_in}{fade_out}{cmd_date}" {self._codec} "{video.output_name(index)}"'
                    else:
                        print(f'Codec name {self._codec_name} not supported.')
                        sys.exit(1)

                    print(f'..{video.basename} > {video.output_name(index)}')
                    FNULL = open(os.devnull, 'w')
                    subprocess.run(command, shell=True, stdout=FNULL, stderr=subprocess.STDOUT)

                    temp_file.write(f'file \'{video.output_name(index)}\'\n')

        temp_file.close()

    def concat(self):

        command = f'ffmpeg -loglevel warning -y -f concat -safe 0 -fflags +genpts -i temp_files.txt -c copy {self._output_file}'
        print(f'Concatting: {self._output_file}')
        subprocess.run(command, shell=True)

    def clean(self):
        command = f'rm -f temp_*'
        print("Cleaning.")
        subprocess.run(command, shell=True)

    def __repr__(self):
        return str(self._videos_per_day)
