# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
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

import datetime, errno, json, math, numbers, os, re, select, shlex, sys, time
from subprocess import check_output, Popen, PIPE
from xml.dom import minidom

from .. import comparison, filesystem, validation
from ..datetime import datetime_now, parts_to_time, secs_to_time, str_to_time, time_ratio
from ..encoding import string_types
from ..subprocess import make_async
from ..types import get_slots

__all__ = (
    'ENCODING_REGEX', 'DURATION_REGEX', 'WIDTH', 'HEIGHT', 'BaseInfo', 'Codec', 'Format', 'Stream', 'AudioStream',
    'SubtitleStream', 'VideoStream', 'Media', 'FFmpeg'
)

# frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s
ENCODING_REGEX = re.compile(
    r'frame=\s*(?P<frame>\d+)\s+fps=\s*(?P<fps>\d+\.?\d*)\s+q=\s*(?P<q>\S+)\s+\S*size=\s*(?P<size>\S+)\s+'
    r'time=\s*(?P<time>\S+)\s+bitrate=\s*(?P<bitrate>\S+)'
)
DURATION_REGEX = re.compile(r'PT(?P<hours>\d+)H(?P<minutes>\d+)M(?P<seconds>[^S]+)S')
WIDTH, HEIGHT = range(2)


def _to_args_list(value):
    return (shlex.split(value) if isinstance(value, string_types) else value) or []


def _to_framerate(fps):
    """
    Return the frame rate as float or None in case of error.

    **Example usage**

    >>> print(_to_framerate({}))
    None
    >>> print(_to_framerate(25.0))
    25.0
    >>> print(_to_framerate('59000/1000'))
    59.0
    """
    try:
        if isinstance(fps, numbers.Number):
            return fps
        if '/' in fps:
            num, denom = fps.split('/')
            return float(num) / float(denom)
        return float(fps)
    except:
        return None


class BaseInfo(validation.CleanAttributesMixin, comparison.SlotsEqualityMixin):

    defaults = {}

    def __init__(self, infos):
        for attr in get_slots(self):
            self._set_attribute(attr, infos)

    def _set_attribute(self, name, infos):
        """Set attribute `name` value from the `infos` or ``self.defaults`` dictionary."""
        setattr(self, name, infos.get(name, self.defaults.get(name)))


class Codec(BaseInfo):

    __slots__ = ('long_name', 'name', 'tag', 'tag_string', 'time_base', 'type')

    def __init__(self, infos):
        for attr in get_slots(self):
            setattr(self, attr, infos['codec_' + attr])

    clean_time_base = lambda s, v: _to_framerate(v)


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

    def __init__(self, infos):
        for attr in get_slots(self):
            if attr == 'codec':
                self.codec = self.codec_class(infos)
            else:
                self._set_attribute(attr, infos)

    clean_avg_frame_rate = clean_r_frame_rate = clean_time_base = lambda s, v: None if v is None else _to_framerate(v)
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

    @property
    def directory(self):
        return os.path.abspath(os.path.dirname(self.filename))

    def clean_options(self, value):
        return _to_args_list(value)

    def create_directory(self):
        filesystem.try_makedirs(self.directory)

    def to_args(self, is_input):
        return self.options + (['-i', self.filename] if is_input else [self.filename])


class FFmpeg(object):

    duration_regex = DURATION_REGEX
    encoding_regex = ENCODING_REGEX
    encoding_executable = 'ffmpeg'
    parsing_executable = 'ffprobe'
    media_class = Media
    format_class = None
    stream_classes = {'audio': None, 'subtitle': None, 'video': None}

    def __init__(self, encoding_executable=None, parsing_executable=None,
                 default_in_duration=datetime.timedelta(seconds=0), ratio_delta=0.01, time_delta=1, max_time_delta=5,
                 sanity_min_ratio=0.95, sanity_max_ratio=1.05, encoding='utf-8'):
        self.encoding_executable = encoding_executable or self.encoding_executable
        self.parsing_executable = parsing_executable or self.parsing_executable
        self.default_in_duration = default_in_duration
        self.ratio_delta = ratio_delta
        self.time_delta = time_delta
        self.max_time_delta = max_time_delta
        self.sanity_min_ratio = sanity_min_ratio
        self.sanity_max_ratio = sanity_max_ratio
        self.encoding = encoding

    def _clean_medias_argument(self, value):
        """
        Return a list of Media instances from passed value. Value can be one or multiple instances of string or Media.
        """
        values = [value] if isinstance(value, (string_types, Media)) else value
        return [self.media_class(v) if isinstance(v, string_types) else v for v in values] if values else []

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
        options = _to_args_list(options)
        args = [self.encoding_executable, '-y']
        for the_input in inputs:
            args.extend(the_input.to_args(is_input=True))
        args.extend(options)
        for output in outputs:
            args.extend(output.to_args(is_input=False))
        return args, inputs, outputs, options

    def _get_chunk(self, process):
        select.select([process.stderr], [], [])
        return process.stderr.read()

    def _get_process(self, arguments, **process_kwargs):
        """
        Return an encoding process with stderr made asynchronous.

        This function ensure subprocess.args is set to the arguments of the ffmpeg subprocess.
        """
        process = Popen(arguments, stderr=PIPE, close_fds=True, **process_kwargs)
        if not hasattr(process, 'args'):
            process.args = arguments
        make_async(process.stderr)
        return process

    def _get_progress(self, in_duration, stats):
        out_duration = str_to_time(stats['time'])
        ratio = time_ratio(out_duration, in_duration)
        return out_duration, ratio

    def _get_statistics(self, chunk):
        match = self.encoding_regex.match(chunk)
        return match.groupdict() if match else {}

    def _clean_statistics(self, stats, **statistics):
        if 'eta_time' not in statistics:
            elapsed_time, ratio = statistics['elapsed_time'], statistics['ratio']
            statistics['eta_time'] = elapsed_time * ((1.0 - ratio) / ratio) if ratio > 0 else datetime.timedelta(0)
        return statistics

    def get_media_duration(self, filename_or_infos, as_delta=False):
        """
        Returns the duration of a media as an instance of time or None in case of error.

        If input `filename` is a MPEG-DASH MPD, then duration will be parser from value of key
        *mediaPresentationDuration*. For any other type of file, this is a *ffprobe* subprocess
        that detect duration of the media.
        """
        is_filename = not isinstance(filename_or_infos, dict)
        if is_filename and os.path.splitext(filename_or_infos)[1] == '.mpd':
            mpd = minidom.parse(filename_or_infos)
            if mpd.firstChild.nodeName == 'MPD':
                match = self.duration_regex.search(mpd.firstChild.getAttribute('mediaPresentationDuration'))
                if match is not None:
                    hours, minutes = int(match.group('hours')), int(match.group('minutes'))
                    microseconds, seconds = math.modf(float(match.group('seconds')))
                    microseconds, seconds = int(1000000 * microseconds), int(seconds)
                    return parts_to_time(hours, minutes, seconds, microseconds, as_delta=as_delta)
        else:
            infos = self.get_media_infos(filename_or_infos) if is_filename else filename_or_infos
            try:
                duration = secs_to_time(float(infos['format']['duration']), as_delta=as_delta) if infos else None
            except KeyError:
                return None
            # ffmpeg may return this so strange value, 00:00:00.04, let it being None
            if duration and (duration >= datetime.timedelta(seconds=1) if as_delta else
                             duration >= datetime.time(0, 0, 1)):
                return duration
        return None

    def get_media_infos(self, filename):
        """Return a Python dictionary containing informations about the media or None in case of error."""
        try:
            return json.loads(check_output([self.parsing_executable, '-v', 'quiet', '-print_format', 'json',
                                            '-show_format', '-show_streams', filename]).decode('utf-8'))
        except:
            return None

    def get_media_format(self, filename_or_infos, fail=False):
        """Return informations about the container (and file) or None in case of error."""
        infos = filename_or_infos if isinstance(filename_or_infos, dict) else self.get_media_infos(filename_or_infos)
        try:
            cls, the_format = self.format_class, infos['format']
            return cls(the_format) if cls and not isinstance(the_format, cls) else the_format
        except:
            if fail:
                raise
            return None

    def get_media_streams(self, filename_or_infos, condition=lambda stream: True, fail=False):
        infos = filename_or_infos if isinstance(filename_or_infos, dict) else self.get_media_infos(filename_or_infos)
        try:
            raw_streams = (s for s in infos['streams'] if condition(s))
        except:
            if fail:
                raise
            return []
        streams = []
        for stream in raw_streams:
            stream_class = self.stream_classes[stream['codec_type']]
            streams.append(stream_class(stream) if stream_class and not isinstance(stream, stream_class) else stream)
        return streams

    def get_audio_streams(self, filename_or_infos, fail=False):
        """Return a list with the audio streams `filename_or_infos` or [] in case of error."""
        return self.get_media_streams(filename_or_infos, condition=lambda s: s['codec_type'] == 'audio', fail=fail)

    def get_subtitle_streams(self, filename_or_infos, fail=False):
        """Return a list with the subtitle streams `filename_or_infos` or [] in case of error."""
        return self.get_media_streams(filename_or_infos, condition=lambda s: s['codec_type'] == 'subtitle', fail=fail)

    def get_video_streams(self, filename_or_infos, fail=False):
        """Return a list with the video streams `filename_or_infos` or [] in case of error."""
        return self.get_media_streams(filename_or_infos, condition=lambda s: s['codec_type'] == 'video', fail=fail)

    def get_video_framerate(self, filename_or_infos, index=0, fail=False):
        """
        Return the frame rate of the video stream at `index` in `filename_or_infos` or None in case of error.
        """
        try:
            stream = self.get_video_streams(filename_or_infos)[index]
            return _to_framerate(stream['avg_frame_rate']) if isinstance(stream, dict) else stream.avg_frame_rate
        except:
            if fail:
                raise
            return None

    def get_video_resolution(self, filename_or_infos, index=0, fail=False):
        """
        Return [width, height] of the video stream at `index` in `filename_or_infos` or None in case of error.
        """
        try:
            stream = self.get_video_streams(filename_or_infos)[index]
            is_dict = isinstance(stream, dict)
            return [int(stream['width']), int(stream['height'])] if is_dict else [stream.width, stream.height]
        except:
            if fail:
                raise
            return None

    def get_now(self):
        return datetime_now()

    def get_size(self, path):
        return filesystem.get_size(path)

    def encode(self, inputs, outputs, options=None, base_track=0, create_directories=True, process_kwargs=None,
               yield_at_start=False):
        """
        Encode a set of input files input to a set of output files and yields statistics about the encoding.

        * Toggle `yield_at_start` to yield a python dictionary with the process when it just started.

        .. note:: Current implementation only handles a unique output.
        """
        arguments, inputs, outputs, _ = self._get_arguments(inputs, outputs, options)
        if len(outputs) != 1:
            raise NotImplementedError()

        # Create outputs directories
        if create_directories:
            for output in outputs:
                output.create_directory()

        process = self._get_process(arguments, **(process_kwargs or {}))
        try:
            # Get input media duration and size to be able to estimate ETA
            in_duration = self.get_media_duration(inputs[base_track].filename) or self.default_in_duration
            in_size = self.get_size(inputs[base_track].filename)

            # Initialize metrics
            output = ''
            stats = {}
            start_date, start_time = self.get_now(), time.time()
            prev_ratio = prev_time = ratio = 0

            while True:
                if yield_at_start:
                    yield {'process': process}
                # Wait for data to become available
                chunk = self._get_chunk(process)
                if not isinstance(chunk, string_types):
                    chunk = chunk.decode(self.encoding)
                output += chunk
                elapsed_time = time.time() - start_time
                stats = self._get_statistics(chunk)
                if stats:
                    try:
                        out_duration, ratio = self._get_progress(in_duration, stats)
                    except ValueError:
                        continue  # parsed statistics are broken, skip the whole match
                    delta_time = elapsed_time - prev_time
                    if ((ratio - prev_ratio > self.ratio_delta and delta_time > self.time_delta) or
                            delta_time > self.max_time_delta):
                        prev_ratio, prev_time = ratio, elapsed_time
                        yield self._clean_statistics(
                            stats=stats, status='PROGRESS', output=output, returncode=None, start_date=start_date,
                            elapsed_time=datetime.timedelta(seconds=elapsed_time), ratio=ratio, in_size=in_size,
                            in_duration=in_duration, out_size=self.get_size(outputs[0].filename),
                            out_duration=out_duration, frame=int(stats['frame']), fps=float(stats['fps']),
                            bitrate=stats['bitrate'], quality=stats.get('q'), sanity=None, process=process
                        )
                returncode = process.poll()
                if returncode is not None:
                    break

            # Output media file sanity check
            out_duration = self.get_media_duration(outputs[0].filename)
            ratio = time_ratio(out_duration, in_duration) if out_duration else 0.0
            frame = int(stats.get('frame', 0))  # FIXME compute latest frame based on output infos
            fps = float(stats.get('fps', 0))  # FIXME compute average fps
            yield self._clean_statistics(
                stats=stats, status='ERROR' if returncode else 'SUCCESS', output=output, returncode=returncode,
                start_date=start_date, elapsed_time=datetime.timedelta(seconds=elapsed_time),
                eta_time=datetime.timedelta(0), ratio=ratio if returncode else 1.0, in_size=in_size,
                in_duration=in_duration, out_size=self.get_size(outputs[0].filename), out_duration=out_duration,
                frame=frame, fps=fps, bitrate=stats.get('bitrate'), quality=stats.get('q'),
                sanity=self.sanity_min_ratio <= ratio <= self.sanity_max_ratio, process=process
            )
        except Exception as exception:
            tb = sys.exc_info()[2]
            try:
                process.kill()
            except OSError as e:
                if e.errno != errno.ESRCH:
                    raise
            raise exception.with_traceback(tb) if hasattr(exception, 'with_traceback') else exception
