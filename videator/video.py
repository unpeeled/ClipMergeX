import os
import datetime
import time
import subprocess
import pytz
import sys

def get_td(str_td):
    dt = datetime.datetime.strptime(str_td, "%H:%M:%S")  # string to datetime conversion

    total_sec = dt.hour*3600 + dt.minute*60 + dt.second  # total seconds calculation
    td = datetime.timedelta(seconds=total_sec)           # timedelta construction
    return td

class Video:
    _mtime = None
    _path = None

    def __init__(self, path, ending, params=[], config={}):
        self._path = path
        self._mtime = os.path.getmtime(path)
        self._ending = ending
        self._params = params
        self._config = config

    @property
    def date(self, include_time=False):
        local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        time = datetime.datetime.fromtimestamp(self._mtime, tz=pytz.timezone(self._config['timezone']))

        if include_time:
            return time.strftime('%d/%m/%Y H:%M')
        
        return time.strftime('%d/%m/%Y')

    @property
    def mtime(self):
        return self._mtime

    @property
    def path(self):
        return self._path

    @property
    def basename(self):
        return os.path.basename(self._path)

    @property
    def filename(self):
        return self.basename.split('.')[0]

    def output_name(self, index=0):
        return f'temp_{self.filename}_{index}.{self._ending}'

    @property
    def length(self):
        result = subprocess.check_output(f'ffprobe -i {self.path} -show_entries format=duration -v quiet -of csv="p=0" | head -n1', shell=True)
        return float(str(result, 'utf-8').split('\n')[0])

    @property
    def first_part_start(self):

        if not self.params or not self.params[0]:
            return 0

        start_end = self.params[0].split('-')
        start = get_td(start_end[0])

        return start.total_seconds()
    
    @property
    def last_part_end(self):

        if not self.params or not self.params[0]:
            return self.length

        start_end = self.params[-1].split('-')
        try:
            end = get_td(start_end[1])
        except IndexError:
            end = datetime.timedelta(seconds=self.length)

        return end.total_seconds()

    @property
    def params(self):
        return self._params
    
    def __repr__(self):
        return self.basename
