# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime, errno, json, math, numbers, os, re, select, subprocess, sys, time
from xml.dom import minidom

from .. import comparison, filesystem, validation
from ..datetime import datetime_now, multiply_time, parts_to_time, secs_to_time, str_to_time, time_ratio
from ..encoding import string_types
from ..subprocess import kill, make_async, raw_cmd, to_args_list
from ..types import get_slots

__all__ = (
    'BIT_RATE_REGEX', 'BIT_RATE_COEFFICIENT_FOR_UNIT', 'DURATION_REGEX', 'ENCODING_REGEX', 'PIPE_REGEX', 'WIDTH',
    'HEIGHT', 'is_pipe', 'to_bit_rate', 'to_frame_rate', 'to_size', 'BaseInfo', 'Codec', 'Format', 'Stream',
    'AudioStream', 'SubtitleStream', 'VideoStream', 'Media', 'FFprobe', 'FFmpeg', 'EncodeState', 'EncodeStatistics'
)

_missing = object()

BIT_RATE_REGEX = re.compile(r'^(?P<value>\d+\.?\d*)(?P<units>[a-z]+)/s$')
BIT_RATE_COEFFICIENT_FOR_UNIT = {'b': 1, 'k': 1000, 'm': 1000**2, 'g': 1000**3}
DURATION_REGEX = re.compile(r'PT(?P<hours>\d+)H(?P<minutes>\d+)M(?P<seconds>[^S]+)S')
# frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s
ENCODING_REGEX = re.compile(
    r'frame=\s*(?P<frame>\d+)\s+fps=\s*(?P<frame_rate>\d+\.?\d*)\s+q=\s*(?P<qscale>\S+)\s+\S*.*size=\s*(?P<size>\S+)\s+'
    r'time=\s*(?P<time>\S+)\s+bitrate=\s*(?P<bit_rate>\S+)'
)
PIPE_REGEX = re.compile(r'^-$|^pipe:\d+$')
SIZE_REGEX = re.compile(r'^(?P<value>\d+\.?\d*)(?P<units>[a-zA-Z]+)$')
SIZE_COEFFICIENT_FOR_UNIT = {'b': 1, 'k': 1024, 'm': 1024**2, 'g': 1024**3}
WIDTH, HEIGHT = range(2)


def is_pipe(filename):
    return isinstance(filename, string_types) and PIPE_REGEX.match(filename)


def to_bit_rate(bit_rate):
    match = BIT_RATE_REGEX.match(bit_rate)
    if match:
        match = match.groupdict()
        return int(float(match['value']) * BIT_RATE_COEFFICIENT_FOR_UNIT[match['units'][0]])
    if bit_rate == 'N/A':
        return None
    raise ValueError(bit_rate)


def to_frame_rate(frame_rate):
    if isinstance(frame_rate, numbers.Number):
        return frame_rate
    if '/' in frame_rate:
        try:
            num, denom = frame_rate.split('/')
            return float(num) / float(denom)
        except ZeroDivisionError:
            return None
    return float(frame_rate)


def to_size(size):
    match = SIZE_REGEX.match(size)
    if match:
        match = match.groupdict()
        return int(float(match['value']) * SIZE_COEFFICIENT_FOR_UNIT[match['units'][0].lower()])
    raise ValueError(size)


class BaseInfo(validation.CleanAttributesMixin, comparison.SlotsEqualityMixin):

    defaults = {}
    attr_name_template = '{name}'

    def __init__(self, info):
        for attr in get_slots(self):
            self._set_attribute(attr, info)

    def _set_attribute(self, name, info):
        """Set attribute `name` value from the `info` or ``self.defaults`` dictionary."""
        setattr(self, name, info.get(self.attr_name_template.format(name=name), self.defaults.get(name)))


class Codec(BaseInfo):

    __slots__ = ('long_name', 'name', 'tag', 'tag_string', 'time_base', 'type')

    attr_name_template = 'codec_{name}'
    clean_time_base = lambda s, v: to_frame_rate(v)


class Format(BaseInfo):

    __slots__ = (
        'bit_rate', 'duration', 'filename', 'format_name', 'format_long_name', 'nb_programs', 'nb_streams',
        'probe_score', 'size', 'start_time'
    )

    clean_bit_rate = clean_nb_programs = clean_nb_streams = clean_probe_score = clean_size = \
        lambda s, v: None if v is None else int(v)
    clean_duration = clean_start_time = lambda s, v: None if v is None else float(v)


class Stream(BaseInfo):

    __slots__ = ('avg_frame_rate', 'codec', 'disposition', 'index', 'r_frame_rate', 'time_base')

    codec_class = Codec

    def __init__(self, info):
        for attr in get_slots(self):
            if attr == 'codec':
                self.codec = self.codec_class(info)
            else:
                self._set_attribute(attr, info)

    clean_avg_frame_rate = clean_r_frame_rate = clean_time_base = lambda s, v: None if v is None else to_frame_rate(v)
    clean_index = lambda s, v: None if v is None else int(v)


class AudioStream(Stream):

    __slots__ = (
        'bit_rate', 'bits_per_sample', 'channel_layout', 'channels', 'duration', 'duration_ts', 'nb_frames',
        'sample_fmt', 'sample_rate', 'start_pts', 'start_time', 'tags'
    )

    clean_bit_rate = clean_bits_per_sample = clean_channels = clean_duration_ts = clean_nb_frames = \
        clean_sample_rate = clean_start_pts = lambda s, v: None if v is None else int(v)
    clean_duration = clean_start_time = lambda s, v: None if v is None else float(v)


class SubtitleStream(Stream):

    __slots__ = ('duration', 'duration_ts', 'start_pts', 'start_time', 'tags')

    clean_duration_ts = clean_start_pts = lambda s, v: None if v is None else int(v)
    clean_duration = clean_start_time = lambda s, v: None if v is None else float(v)


class VideoStream(Stream):

    __slots__ = (
        'display_aspect_ratio', 'has_b_frames', 'height', 'level', 'nb_frames', 'pix_fmt', 'sample_aspect_ratio',
        'width'
    )

    clean_height = clean_level = clean_nb_frames = clean_width = lambda s, v: None if v is None else int(v)


class Media(validation.CleanAttributesMixin, comparison.SlotsEqualityMixin):

    __slots__ = ('filename', 'options')

    def __init__(self, filename, options=None):
        self.filename = filename
        self.options = options
        self._size = None

    @property
    def directory(self):
        return None if self.is_pipe else os.path.abspath(os.path.dirname(self.filename))

    @property
    def is_pipe(self):
        return is_pipe(self.filename)

    @property
    def size(self):
        if self._size is None:
            return 0 if self.is_pipe else filesystem.get_size(self.filename)
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def clean_options(self, value):
        return to_args_list(value)

    def create_directory(self):
        if not self.is_pipe:
            filesystem.try_makedirs(self.directory)

    def to_args(self, is_input):
        return self.options + (['-i', self.filename] if is_input else [self.filename])


class FFprobe(object):

    executable = 'ffprobe'
    duration_regex = DURATION_REGEX
    format_class = None
    media_class = Media
    stream_classes = {'audio': None, 'subtitle': None, 'video': None}

    def __init__(self, executable=None):
        self.executable = executable or self.executable

    def get_media_duration(self, media, as_delta=False, options=None):
        """
        Returns the duration of a media as an instance of time or None in case of error.

        Set `media` to an instance of `self.media_class`, a filename or the output of `get_media_info()`.
        If `media` is the path to a MPEG-DASH MPD, then duration will be parser from value of key
        *mediaPresentationDuration*.
        """
        if isinstance(media, string_types) and os.path.splitext(media)[1] == '.mpd':
            mpd = minidom.parse(media)
            if mpd.firstChild.nodeName == 'MPD':
                match = self.duration_regex.search(mpd.firstChild.getAttribute('mediaPresentationDuration'))
                if match is not None:
                    hours, minutes = int(match.group('hours')), int(match.group('minutes'))
                    microseconds, seconds = math.modf(float(match.group('seconds')))
                    microseconds, seconds = int(1000000 * microseconds), int(seconds)
                    return parts_to_time(hours, minutes, seconds, microseconds, as_delta=as_delta)
        else:
            info = self.get_media_info(media)
            try:
                duration = secs_to_time(float(info['format']['duration']), as_delta=as_delta) if info else None
            except KeyError:
                return None
            # ffmpeg may return this so strange value, 00:00:00.04, let it being None
            if duration and (duration >= datetime.timedelta(seconds=1) if as_delta else
                             duration >= datetime.time(0, 0, 1)):
                return duration

    def get_media_info(self, media):
        """
        Return a Python dictionary containing information about the media or None in case of error.
        Set `media` to an instance of `self.media_class` or a filename.
        If `media` is a Python dictionary, then it is returned.
        """
        if isinstance(media, dict):
            return media
        media = self.to_media(media)
        if not is_pipe(media.filename):  # Read media information from a PIPE not yet implemented
            try:
                return json.loads(subprocess.check_output([self.executable, '-v', 'quiet', '-print_format', 'json',
                                  '-show_format', '-show_streams', media.filename]).decode('utf-8'))
            except:
                pass

    def get_media_format(self, media, fail=False):
        """
        Return information about the container (and file) or None in case of error.
        Set `media` to an instance of `self.media_class`, a filename or the output of `get_media_info()`.
        """
        info = self.get_media_info(media)
        try:
            cls, the_format = self.format_class, info['format']
            return cls(the_format) if cls and not isinstance(the_format, cls) else the_format
        except:
            if fail:
                raise

    def get_media_streams(self, media, condition=lambda stream: True, fail=False):
        """
        Return a list with the media streams of `media` or [] in case of error.
        Set `media` to an instance of `self.media_class`, a filename or the output of `get_media_info()`.
        """
        info = self.get_media_info(media)
        try:
            raw_streams = (s for s in info['streams'] if condition(s))
        except:
            if fail:
                raise
            return []
        streams = []
        for stream in raw_streams:
            stream_class = self.stream_classes[stream['codec_type']]
            streams.append(stream_class(stream) if stream_class and not isinstance(stream, stream_class) else stream)
        return streams

    def get_audio_streams(self, media, fail=False):
        """
        Return a list with the audio streams of `media` or [] in case of error.
        Set `media` to an instance of `self.media_class`, a filename or the output of `get_media_info()`.
        """
        return self.get_media_streams(media, condition=lambda s: s['codec_type'] == 'audio', fail=fail)

    def get_subtitle_streams(self, media, fail=False):
        """
        Return a list with the subtitle streams of `media` or [] in case of error.
        Set `media` to an instance of `self.media_class`, a filename or the output of `get_media_info()`.
        """
        return self.get_media_streams(media, condition=lambda s: s['codec_type'] == 'subtitle', fail=fail)

    def get_video_streams(self, media, fail=False):
        """
        Return a list with the video streams of `media` or [] in case of error.
        Set `media` to an instance of `self.media_class`, a filename or the output of `get_media_info()`.
        """
        return self.get_media_streams(media, condition=lambda s: s['codec_type'] == 'video', fail=fail)

    def get_video_frame_rate(self, media, index=0, fail=False):
        """
        Return the frame rate of the video stream at `index` in `media` or None in case of error.
        Set `media` to an instance of `self.media_class`, a filename or the output of `get_media_info()`.
        """
        try:
            stream = self.get_video_streams(media)[index]
            return to_frame_rate(stream['avg_frame_rate']) if isinstance(stream, dict) else stream.avg_frame_rate
        except:
            if fail:
                raise

    def get_video_resolution(self, media, index=0, fail=False):
        """
        Return [width, height] of the video stream at `index` in `media` or None in case of error.
        Set `media` to an instance of `self.media_class`, a filename or the output of `get_media_info()`.
        """
        try:
            stream = self.get_video_streams(media)[index]
            is_dict = isinstance(stream, dict)
            return [int(stream['width']), int(stream['height'])] if is_dict else [stream.width, stream.height]
        except:
            if fail:
                raise

    def to_media(self, media):
        return media if isinstance(media, self.media_class) else self.media_class(media)


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
    ffprobe_class = FFprobe
    states = EncodeState

    def __init__(self, inputs, outputs, options, in_base_index=0, out_base_index=0, ratio_delta=0.01, time_delta=1,
                 max_time_delta=5):
        self.inputs = inputs
        self.outputs = outputs
        self.options = options
        self.in_base_index = in_base_index
        self.out_base_index = out_base_index
        self.ratio_delta = ratio_delta
        self.time_delta = datetime.timedelta(seconds=time_delta)
        self.max_time_delta = datetime.timedelta(seconds=max_time_delta)

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
        duration = self.ffprobe_class().get_media_duration(self.input, as_delta=True) or self.default_in_duration
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
        if self._should_report():
            return self

    def end(self, returncode):
        self.state = self.states.FAILURE if returncode else self.states.SUCCESS
        self.returncode = returncode
        self.elapsed_time = datetime.timedelta(seconds=time.time() - self.start_time)
        self.frame_rate = self.frame / (self.elapsed_time.total_seconds() or 0.0001)
        self.output.duration = self.ffprobe_class().get_media_duration(self.output.filename, as_delta=True)
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
            ffmpeg_statistics['size'] = to_size(ffmpeg_statistics['size'])
            ffmpeg_statistics['bit_rate'] = to_bit_rate(ffmpeg_statistics['bit_rate'])
            return ffmpeg_statistics

    def _should_report(self):
        elapsed_time, ratio = self.elapsed_time or datetime.timedelta(0), self.ratio or 0
        if not hasattr(self, '_prev_elapsed_time') or not hasattr(self, '_prev_ratio'):
            self._prev_elapsed_time, self._prev_ratio = elapsed_time, ratio
            return True
        delta_time = (elapsed_time - self._prev_elapsed_time) if elapsed_time else datetime.timedelta(0)
        delta_ratio = (ratio - self._prev_ratio) if ratio else 0
        if (delta_ratio > self.ratio_delta and delta_time > self.time_delta) or delta_time > self.max_time_delta:
            self._prev_elapsed_time, self._prev_ratio = elapsed_time, ratio
            return True
        return False


class FFmpeg(object):
    """
    Encode a set of input files input to a set of output files and yields statistics about the encoding.
    """

    executable = 'ffmpeg'
    ffprobe_class = FFprobe
    statistics_class = EncodeStatistics

    def __init__(self, executable=None, chunk_read_timeout=0.5, encode_poll_delay=0.5, encoding='utf-8'):
        self.executable = executable or self.executable
        self.chunk_read_timeout = chunk_read_timeout
        self.encode_poll_delay = encode_poll_delay
        self.encoding = encoding
        self.ffprobe = self.ffprobe_class()

    def encode(self, inputs, outputs, options=None, create_directories=True, process_poll=True, process_kwargs=None,
               statistics_kwargs=None):
        """
        Encode a set of input files input to a set of output files and yields statistics about the encoding.
        """
        arguments, inputs, outputs, options = self._get_arguments(inputs, outputs, options)

        # Create outputs directories
        if create_directories:
            for output in outputs:
                output.create_directory()

        statistics = self.statistics_class(inputs, outputs, options, **(statistics_kwargs or {}))
        process = self._get_process(arguments, **(process_kwargs or {}))
        try:
            yield statistics.start(process)
            while True:
                chunk = self._get_chunk(process)
                if statistics.progress(chunk or ''):
                    yield statistics
                if process_poll:
                    returncode = process.poll()
                    if returncode is not None:
                        break
                if self.encode_poll_delay:
                    time.sleep(self.encode_poll_delay)
            yield statistics.end(returncode)
        except Exception as exception:
            tb = sys.exc_info()[2]
            kill(process)
            raise exception.with_traceback(tb) if hasattr(exception, 'with_traceback') else exception

    def _clean_medias_argument(self, value):
        """
        Return a list of Media instances from passed value. Value can be one or multiple instances of string or Media.
        """
        values = [value] if isinstance(value, (string_types, self.ffprobe.media_class)) else value
        return [self.ffprobe.to_media(v) for v in values] if values else []

    def _get_arguments(self, inputs, outputs, options=None):
        """
        Return the arguments for the encoding process.

        * Set inputs to one or multiple strings (filenames) or Media instances (with options).
        * Set outputs to one or multiple strings (filenames) or Media instances (with options).
        * Set options to a string or a list with the options to put in-between the inputs and outputs (legacy API).

        In return you will get a tuple with (arguments, inputs -> list Media, outputs -> list Media, options -> list).
        """
        inputs = self._clean_medias_argument(inputs)
        outputs = self._clean_medias_argument(outputs)
        options = to_args_list(options)
        args = [self.executable, '-y']
        for the_input in inputs:
            args.extend(the_input.to_args(is_input=True))
        args.extend(options)
        for output in outputs:
            args.extend(output.to_args(is_input=False))
        return args, inputs, outputs, options

    def _get_chunk(self, process):
        select.select([process.stderr], [], [], self.chunk_read_timeout)
        try:
            chunk = process.stderr.read()
            return chunk if chunk is None or isinstance(chunk, string_types) else chunk.decode(self.encoding)
        except IOError as e:
            if e.errno == errno.EAGAIN:
                return None
            raise

    def _get_process(self, arguments, **process_kwargs):
        """Return an encoding process with stderr made asynchronous."""
        process = raw_cmd(arguments, stderr=subprocess.PIPE, close_fds=True, **process_kwargs)
        make_async(process.stderr)
        return process
