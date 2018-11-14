# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime, re, time

from pytoolbox import module
from pytoolbox.datetime import datetime_now, multiply_time, secs_to_time, str_to_time, time_ratio

from . import ffprobe, utils

_all = module.All(globals())

ENCODING_REGEX = re.compile(  # frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s
    r'frame=\s*(?P<frame>\d+)\s+fps=\s*(?P<frame_rate>\d+\.?\d*)\s+q=\s*(?P<qscale>\S+)\s+\S*.*size=\s*(?P<size>\S+)\s+'
    r'time=\s*(?P<time>\S+)\s+bitrate=\s*(?P<bit_rate>\S+)'
)


class EncodeState(object):
    NEW = 'NEW'
    STARTED = 'STARTED'
    PROCESSING = 'PROCESSING'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'

    ALL_STATES = frozenset([NEW, STARTED, PROCESSING, SUCCESS, FAILURE])
    FINAL_STATES = frozenset([SUCCESS, FAILURE])


class EncodeStatistics(object):

    default_in_duration = datetime.timedelta(seconds=0)
    encoding_regex = ENCODING_REGEX
    ffprobe_class = ffprobe.FFprobe
    states = EncodeState

    def __init__(self, inputs, outputs, options, in_base_index=0, out_base_index=0):
        self.inputs = inputs
        self.outputs = outputs
        self.options = options
        self.in_base_index = in_base_index
        self.out_base_index = out_base_index

        self.process = None
        self.process_output = ''
        self.returncode = None

        self.state = self.states.NEW
        self.start_date = None
        self.start_time = None
        self.elapsed_time = None
        self.ratio = None
        self.frame = None
        self.frame_rate = None
        self.qscale = None
        self.bit_rate = None

        # Retrieve input media duration and size, handle sub-clipping
        duration = self.ffprobe_class().get_media_duration(
            self.input, as_delta=True) or self.default_in_duration
        self.input.duration, self.input.size = \
            self._get_subclip_duration_and_size(duration, self.input.size, options)
        self.output.duration = None

    @property
    def eta_time(self):
        if self.state in self.states.FINAL_STATES:
            return datetime.timedelta(0)
        if not self.ratio:
            return None
        return multiply_time(self.elapsed_time, (1.0 - self.ratio) / self.ratio, as_delta=True)

    @property
    def input(self):
        return self.inputs[self.in_base_index]

    @property
    def output(self):
        return self.outputs[self.out_base_index]

    def get_now(self):
        return datetime_now()

    def start(self, process):
        self.state = self.states.STARTED
        self.process = process
        self.start_date = self.get_now()
        self.start_time = time.time()
        self.elapsed_time = datetime.timedelta(0)
        self.output.duration = datetime.timedelta(0)
        self.frame = 0
        self._update_ratio()
        return self

    def progress(self, chunk):
        self.state = self.states.PROCESSING
        self.elapsed_time = datetime.timedelta(seconds=time.time() - self.start_time)
        ffmpeg_statistics = self._parse_chunk(chunk)
        if ffmpeg_statistics:
            self.output.duration = ffmpeg_statistics['time']
            self.frame = ffmpeg_statistics['frame']
            self.frame_rate = ffmpeg_statistics['frame_rate']
            self.qscale = ffmpeg_statistics['qscale']
            self.output.size = ffmpeg_statistics['size']
            self.bit_rate = ffmpeg_statistics['bit_rate']
        self._update_ratio()
        return self

    def end(self, returncode):
        self.state = self.states.FAILURE if returncode else self.states.SUCCESS
        self.returncode = returncode
        self.elapsed_time = datetime.timedelta(seconds=time.time() - self.start_time)
        self.frame_rate = self.frame / (self.elapsed_time.total_seconds() or 0.0001)
        self.output.duration = self.ffprobe_class().get_media_duration(
            self.output.path, as_delta=True)
        self.output.size = None
        self._update_ratio()
        return self

    def _update_ratio(self):
        if self.state == self.states.SUCCESS:
            self.ratio = 1.0
        else:
            ratio = self._compute_ratio()
            self.ratio = None if ratio is None else min(1.0, max(0.0, ratio))

    def _compute_ratio(self):
        if self.input.duration and self.output.duration is not None:
            return time_ratio(self.output.duration, self.input.duration)

    def _get_subclip_duration_and_size(self, duration, size, options):
        """Adjust duration and size if we only encode a sub-clip."""
        def to_time(t):
            return str_to_time(t, as_delta=True) if ':' in t else secs_to_time(t, as_delta=True)
        try:
            sub_pos = to_time(options[options.index('-ss') + 1]) or datetime.timedelta(0)
        except (IndexError, ValueError):
            sub_pos = datetime.timedelta(0)
        try:
            sub_dur = to_time(options[options.index('-t') + 1])
        except (IndexError, ValueError):
            sub_dur = duration
        if sub_dur is not None:
            sub_dur = max(datetime.timedelta(0), min(duration - sub_pos, sub_dur))
            return sub_dur, int(size * time_ratio(sub_dur, duration))
        return duration, size

    def _parse_chunk(self, chunk):
        self.process_output += chunk
        match = self.encoding_regex.match(chunk.strip())
        if match:
            ffmpeg_statistics = match.groupdict()
            try:
                ffmpeg_statistics['time'] = str_to_time(ffmpeg_statistics['time'], as_delta=True)
            except ValueError:
                return None  # Parsed statistics are broken, do not use them
            ffmpeg_statistics['frame'] = int(ffmpeg_statistics['frame'])
            ffmpeg_statistics['frame_rate'] = float(ffmpeg_statistics['frame_rate'])
            qscale = ffmpeg_statistics.get('qscale')
            ffmpeg_statistics['qscale'] = None if qscale is None else float(qscale)
            ffmpeg_statistics['size'] = utils.to_size(ffmpeg_statistics['size'])
            ffmpeg_statistics['bit_rate'] = utils.to_bit_rate(ffmpeg_statistics['bit_rate'])
            return ffmpeg_statistics


class FrameBasedRatioMixin(object):
    """
    Compute ratio based on estimated input number of frames and current output number of frames.
    Fall-back to super's ratio computation method.
    """

    def __init__(self, *args, **kwargs):
        super(FrameBasedRatioMixin, self).__init__(*args, **kwargs)
        fps = self.ffprobe_class().get_video_frame_rate(self.input)
        if fps and self.input.duration:
            self.input.frame = fps * self.input.duration.total_seconds()
        else:
            self.input.frame = None

    def _compute_ratio(self):
        if self.input.frame and self.frame is not None:
            return self.frame / self.input.frame
        return super(FrameBasedRatioMixin, self)._compute_ratio()


__all__ = _all.diff(globals())
