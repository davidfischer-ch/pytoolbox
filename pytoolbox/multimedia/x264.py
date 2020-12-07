import re

from .ffmpeg import FFmpeg

__all__ = ['ENCODING_REGEX', 'X264']

# [79.5%] 3276/4123 frames, 284.69 fps, 2111.44 kb/s, eta 0:00:02
ENCODING_REGEX = re.compile(
    r'\[(?P<percent>\d+\.\d*)%\]\s+(?P<frame>\d+)/(?P<frame_total>\d+)\s+frames,\s+'
    r'(?P<frame_rate>\d+\.\d*)\s+fps,\s+(?P<bit_rate>[^,]+),\s+eta\s+(?P<eta>[\d:]+)'
)


class X264(FFmpeg):

    # encoding_regex = ENCODING_REGEX
    executable = 'x264'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise NotImplementedError('Must be reimplemented based on newer FFmpeg class interface')

    def _get_arguments(self, inputs, outputs, in_options=None, out_options=None):
        raise NotImplementedError('Must be reimplemented based on newer FFmpeg class interface')
        # in_paths = [f for f in ([in_paths] if isinstance(in_paths, str) else in_paths)]
        # if len(in_paths) > 1:
        #     raise NotImplementedError('Unable to handle more than one input.')
        # out_path = out_path or '/dev/null'
        # options = (shlex.split(options) if isinstance(options, str) else options) or []
        # args = [self.executable] + options + ['-o', out_path] + in_paths
        # return args, in_paths, out_path, options

    # def _get_progress(self, in_duration, stats):
    #     out_duration = in_duration * float(stats['percent'])
    #     ratio = float(stats['frame']) / float(stats['frame_total'])
    #     return out_duration, ratio

    # def _clean_statistics(self, stats, **statistics):
    #     statistics.setdefault('eta_time', datetime.timedelta(seconds=total_seconds(stats['eta'])))
    #     return statistics
