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

__all__ = (
    'ENCODING_REGEX', 'DURATION_REGEX', 'WIDTH', 'HEIGHT', 'MPD_TEST', 'Codec', 'AudioStream', 'VideoStream', 'Media',
    'FFmpeg'
)

# frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s
ENCODING_REGEX = re.compile(
    r'frame=\s*(?P<frame>\d+)\s+fps=\s*(?P<fps>\d+\.?\d*)\s+q=\s*(?P<q>\S+)\s+\S*size=\s*(?P<size>\S+)\s+'
    r'time=\s*(?P<time>\S+)\s+bitrate=\s*(?P<bitrate>\S+)'
)
DURATION_REGEX = re.compile(r'PT(?P<hours>\d+)H(?P<minutes>\d+)M(?P<seconds>[^S]+)S')
WIDTH, HEIGHT = range(2)

MPD_TEST = """<?xml version="1.0"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT0H6M7.83S">
  <useless text="testing encoding : ça va ou bien ?" />
</MPD>
"""


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


class Codec(validation.CleanAttributesMixin, comparison.SlotsEqualityMixin):

    __slots__ = ('long_name', 'name', 'tag', 'tag_string', 'time_base', 'type')

    def __init__(self, infos):
        for attr in self.__slots__:
            setattr(self, attr, infos['codec_' + attr])

    clean_time_base = lambda s, v: _to_framerate(v)


class AudioStream(validation.CleanAttributesMixin, comparison.SlotsEqualityMixin):

    __slots__ = (
        'avg_frame_rate', 'bit_rate', 'bits_per_sample', 'channel_layout', 'channels', 'codec', 'disposition',
        'duration', 'duration_ts', 'index', 'nb_frames', 'r_frame_rate', 'sample_fmt', 'sample_rate', 'start_pts',
        'start_time', 'tags', 'time_base'
    )

    def __init__(self, infos):
        for attr in self.__slots__:
            if attr == 'codec':
                self.codec = Codec(infos)
            else:
                setattr(self, attr, infos[attr])

    clean_avg_frame_rate = clean_r_frame_rate = clean_time_base = lambda s, v: _to_framerate(v)
    clean_bit_rate = clean_bits_per_sample = clean_channels = clean_duration_ts = clean_index = clean_nb_frames = \
        clean_sample_rate = clean_start_pts = lambda s, v: int(v)
    clean_duration = clean_start_time = lambda s, v: float(v)


class VideoStream(validation.CleanAttributesMixin, comparison.SlotsEqualityMixin):

    __slots__ = (
        'avg_frame_rate', 'codec', 'display_aspect_ratio', 'disposition', 'has_b_frames', 'height', 'index', 'level',
        'pix_fmt', 'r_frame_rate', 'sample_aspect_ratio', 'time_base', 'width'
    )

    def __init__(self, infos):
        for attr in self.__slots__:
            if attr == 'codec':
                self.codec = Codec(infos)
            else:
                setattr(self, attr, infos[attr])

    clean_avg_frame_rate = clean_r_frame_rate = clean_time_base = lambda s, v: _to_framerate(v)
    clean_height = clean_index = clean_level = clean_width = lambda s, v: int(v)


class Media(validation.CleanAttributesMixin, comparison.SlotsEqualityMixin):

    __slots__ = ('filename', 'options')

    def __init__(self, filename, options=None):
        self.filename = filename
        self.options = options

    @property
    def directory(self):
        return os.path.abspath(os.path.dirname(self.filename))

    def clean_options(self, value):
        return (shlex.split(value) if isinstance(value, string_types) else value) or []

    def create_directory(self):
        filesystem.try_makedirs(self.directory)

    def to_args(self, is_input):
        return self.options + (['-i', self.filename] if is_input else [self.filename])


class FFmpeg(object):

    duration_regex = DURATION_REGEX
    encoding_regex = ENCODING_REGEX
    encoding_executable = 'ffmpeg'
    parsing_executable = 'ffprobe'
    stream_classes = {
        'audio': None,
        'video': None
    }

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

        **Example usage**

        >>> from nose.tools import assert_list_equal as leq_
        >>> handle = FFmpeg()._clean_medias_argument

        >>> leq_(handle('a.mp4'), [Media('a.mp4')])
        >>> leq_(handle(['a.mp4', 'b.mp3']), [Media('a.mp4'), Media('b.mp3')])
        >>> leq_(handle(Media('a', '-f mp4')), [Media('a', ['-f', 'mp4'])])
        >>> leq_(handle([Media('a', ['-f', 'mp4']), Media('b.mp3')]), [Media('a', ['-f', 'mp4']), Media('b.mp3')])
        """
        values = [value] if isinstance(value, (string_types, Media)) else value
        return [Media(v) if isinstance(v, string_types) else v for v in values]

    def _get_arguments(self, inputs, outputs, options=None):
        """
        Return the arguments for the encoding process.

        * Set inputs to one or multiple strings (filenames) or Media instances (with options).
        * Set outputs to one or multiple strings (filenames) or Media instances (with options).
        * Set options to a string or a list with the options to put in-between the inputs and outputs (legacy API).

        In return you will get a tuple with (arguments, inputs -> list Media, outputs -> list Media, options -> list).

        **Example usage**

        >>> from nose.tools import assert_list_equal as leq_
        >>> get = FFmpeg()._get_arguments

        Using options (the legacy API, also simplify simple calls):

        >>> options_string = '-strict experimental -vf "yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2"'

        >>> args, inputs, outputs, options = get('input.mp4', 'output.mkv', options_string)
        >>> leq_(inputs, [Media('input.mp4')])
        >>> leq_(outputs, [Media('output.mkv')])
        >>> leq_(options, ['-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'])
        >>> leq_(args, ['ffmpeg', '-y', '-i', 'input.mp4'] + options + ['output.mkv'])

        Using instances of Media (the newest API, greater flexibility):

        >>> args, inputs, outputs, options = get(Media('in', '-f mp4'), Media('out.mkv', '-acodec copy -vcodec copy'))
        >>> leq_(inputs, [Media('in', ['-f', 'mp4'])])
        >>> leq_(outputs, [Media('out.mkv', ['-acodec', 'copy', '-vcodec', 'copy'])])
        >>> leq_(options, [])
        >>> leq_(args, ['ffmpeg', '-y', '-f', 'mp4', '-i', 'in', '-acodec', 'copy', '-vcodec', 'copy', 'out.mkv'])
        """
        inputs = self._clean_medias_argument(inputs)
        outputs = self._clean_medias_argument(outputs)
        options = Media.clean_options(None, options)
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

    def _get_process(self, arguments):
        """
        Return an encoding process with stderr made asynchronous.

        This function ensure subprocess.args is set to the arguments of the ffmpeg subprocess.

        **Example usage**

        >>> from nose.tools import assert_list_equal as leq_
        >>> options = ['-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2']
        >>> process = FFmpeg()._get_process(['ffmpeg', '-y', '-i', 'input.mp4'] + options + ['output.mkv'])
        >>> leq_(process.args, ['ffmpeg', '-y', '-i', 'input.mp4'] + options + ['output.mkv'])
        >>> process.terminate()
        """
        process = Popen(arguments, stderr=PIPE, close_fds=True)
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

        If input ``filename`` is a MPEG-DASH MPD, then duration will be parser from value of key
        *mediaPresentationDuration*. For any other type of file, this is a *ffprobe* subprocess
        that detect duration of the media.

        **Example usage**

        >>> from codecs import open
        >>> from nose.tools import eq_

        Bad file format:

        >>> with open('/tmp/test.txt', 'w', encoding='utf-8') as f:
        ...     f.write('Hey, I am not a MPD nor a média')
        >>> print(FFmpeg().get_media_duration('/tmp/test.txt'))
        None
        >>> os.remove('/tmp/test.txt')

        Some random bad things:

        >>> print(FFmpeg().get_media_duration({}))
        None

        A MPEG-DASH MPD:

        >>> with open('/tmp/test.mpd', 'w', encoding='utf-8') as f:
        ...     f.write(MPD_TEST)
        >>> print(FFmpeg().get_media_duration('/tmp/test.mpd').strftime('%H:%M:%S.%f'))
        00:06:07.830000
        >>> FFmpeg().get_media_duration('/tmp/test.mpd', as_delta=True)
        datetime.timedelta(0, 367, 830000)
        >>> os.remove('/tmp/test.mpd')

        A MP4:

        >>> print(FFmpeg().get_media_duration('small.mp4').strftime('%H:%M:%S'))
        00:00:05
        >>> print(FFmpeg().get_media_duration(FFmpeg().get_media_infos('small.mp4')).strftime('%H:%M:%S'))
        00:00:05
        >>> eq_(FFmpeg().get_media_duration(FFmpeg().get_media_infos('small.mp4'), as_delta=True).seconds, 5)
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
        """
        Return a Python dictionary containing informations about the media informations or None in case of error.

        Thanks to: https://gist.github.com/nrk/2286511

        **Example usage**

        Remark: This doctest is disabled because in Travis CI, the installed ffprobe doesn't output the same exact
        string.

        >> from pprint import pprint
        >> pprint(FFmpeg().get_media_infos('small.mp4'))  # doctest: +ELLIPSIS
        {'format': {'bit_rate': '551193',
                     'duration': '5.568000',
                     'filename': 'small.mp4',
                     'format_long_name': 'QuickTime / MOV',
                     'format_name': 'mov,mp4,m4a,3gp,3g2,mj2',
                     'nb_programs': 0,
                     'nb_streams': 2,
                     'probe_score': 100,
                     'size': '383631',
                     'start_time': '0.000000',
                     'tags': {'compatible_brands': 'mp42isomavc1',
                              'creation_time': '2010-03-20 21:29:11',
                              'encoder': 'HandBrake 0.9.4 2009112300',
                              'major_brand': 'mp42',
                              'minor_version': '0'}},
         'streams': [{'avg_frame_rate': '30/1',
                       'bit_rate': '465641',
                       'codec_long_name': 'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10',
                       'codec_name': 'h264',
                       'codec_tag': '0x31637661',
                       'codec_tag_string': 'avc1',
                       'codec_time_base': '1/60',
                       'codec_type': 'video',
                       'display_aspect_ratio': '0:1',
                       'disposition': {'attached_pic': 0,
                                       'clean_effects': 0,
                                       'comment': 0,
                                       'default': 1,
                                       'dub': 0,
                                       'forced': 0,
                                       'hearing_impaired': 0,
                                       'karaoke': 0,
                                       'lyrics': 0,
                                       'original': 0,
                                       'visual_impaired': 0},
                       'duration': '5.533333',
                       'duration_ts': 498000,
                       'has_b_frames': 0,
                       'height': 320,
                       'index': 0,
                       'level': 30,
                       'nb_frames': '166',
                       'pix_fmt': 'yuv420p',
                       'profile': 'Constrained Baseline',
                       'r_frame_rate': '30/1',
                       'sample_aspect_ratio': '0:1',
                       'start_pts': 0,
                       'start_time': '0.000000',
                       'tags': {'creation_time': '2010-03-20 21:29:11',
                                'language': 'und'},
                       'time_base': '1/90000',
                       'width': 560},
                      {'avg_frame_rate': '0/0',
                       'bit_rate': '83050',
                       'bits_per_sample': 0,
                       'channel_layout': 'mono',
                       'channels': 1,
                       'codec_long_name': 'AAC (Advanced Audio Coding)',
                       'codec_name': 'aac',
                       'codec_tag': '0x6134706d',
                       'codec_tag_string': 'mp4a',
                       'codec_time_base': '1/48000',
                       'codec_type': 'audio',
                       'disposition': {'attached_pic': 0,
                                       'clean_effects': 0,
                                       'comment': 0,
                                       'default': 1,
                                       'dub': 0,
                                       'forced': 0,
                                       'hearing_impaired': 0,
                                       'karaoke': 0,
                                       'lyrics': 0,
                                       'original': 0,
                                       'visual_impaired': 0},
                       'duration': '5.568000',
                       'duration_ts': 267264,
                       'index': 1,
                       'nb_frames': '261',
                       'r_frame_rate': '0/0',
                       'sample_fmt': 'fltp',
                       'sample_rate': '48000',
                       'start_pts': 0,
                       'start_time': '0.000000',
                       'tags': {'creation_time': '2010-03-20 21:29:11',
                                 'language': 'eng'},
                       'time_base': '1/48000'}]}
        """

        try:
            return json.loads(check_output([self.parsing_executable, '-v', 'quiet', '-print_format', 'json',
                                            '-show_format', '-show_streams', filename]).decode('utf-8'))
        except:
            return None

    def get_streams(self, filename_or_infos, condition=lambda stream: True):
        infos = filename_or_infos if isinstance(filename_or_infos, dict) else self.get_media_infos(filename_or_infos)
        try:
            raw_streams = (s for s in infos['streams'] if condition(s))
        except:
            return []
        streams = []
        for stream in raw_streams:
            stream_class = self.stream_classes[stream['codec_type']]
            streams.append(stream_class(stream) if stream_class and not isinstance(stream, stream_class) else stream)
        return streams

    def get_audio_streams(self, filename_or_infos):
        """
        Return a list with the audio streams ``filename_or_infos`` or [] in case of error.

        **Example usage**

        >>> from nose.tools import eq_
        >>> ffmpeg = FFmpeg()

        >>> ffmpeg.stream_classes['audio'] = None
        >>> streams = ffmpeg.get_audio_streams('small.mp4')
        >>> assert isinstance(streams[0], dict)
        >>> eq_(streams[0]['avg_frame_rate'], '0/0')
        >>> eq_(streams[0]['channels'], 1)
        >>> eq_(streams[0]['codec_time_base'], '1/48000')

        >>> ffmpeg.stream_classes['audio'] = AudioStream
        >>> streams = ffmpeg.get_audio_streams('small.mp4')
        >>> assert isinstance(streams[0], AudioStream)
        >>> eq_(streams[0].avg_frame_rate, None)
        >>> eq_(streams[0].channels, 1)
        >>> eq_(streams[0].codec.time_base, 1 / 48000)
        """
        return self.get_streams(filename_or_infos, condition=lambda s: s['codec_type'] == 'audio')

    def get_video_streams(self, filename_or_infos):
        """
        Return a list with the video streams ``filename_or_infos`` or [] in case of error.

        **Example usage**

        >>> from nose.tools import eq_
        >>> ffmpeg = FFmpeg()

        >>> ffmpeg.stream_classes['video'] = None
        >>> streams = ffmpeg.get_video_streams('small.mp4')
        >>> assert isinstance(streams[0], dict)
        >>> eq_(streams[0]['avg_frame_rate'], '30/1')

        >>> ffmpeg.stream_classes['video'] = VideoStream
        >>> streams = ffmpeg.get_video_streams('small.mp4')
        >>> assert isinstance(streams[0], VideoStream)
        >>> eq_(streams[0].avg_frame_rate, 30.0)
        """
        return self.get_streams(filename_or_infos, condition=lambda s: s['codec_type'] == 'video')

    def get_video_framerate(self, filename_or_infos, index=0):
        """
        Return the frame rate of the video stream at ``index`` in ``filename_or_infos`` or None in case of error.

        **Example usage**

        >>> print(FFmpeg().get_video_framerate(3.14159265358979323846))
        None
        >>> print(FFmpeg().get_video_framerate({}))
        None
        >>> print(FFmpeg().get_video_framerate(FFmpeg().get_media_infos('small.mp4')))
        30.0
        >>> print(FFmpeg().get_video_framerate('small.mp4'))
        30.0
        >>> print(FFmpeg().get_video_framerate({'streams': [
        ...     {'codec_type': 'audio'},
        ...     {'codec_type': 'video', 'avg_frame_rate': '59000/1000'}
        ... ]}))
        59.0
        """
        video_streams = self.get_video_streams(filename_or_infos)
        try:
            return _to_framerate(video_streams[index]['avg_frame_rate'])
        except:
            return None

    def get_video_resolution(self, filename_or_infos, index=0):
        """
        Return [width, height] of the video stream at ``index`` in ``filename_or_infos`` or None in case of error.

        **Example usage**

        >>> print(FFmpeg().get_video_resolution(3.14159265358979323846))
        None
        >>> print(FFmpeg().get_video_resolution({}))
        None
        >>> print(FFmpeg().get_video_resolution(FFmpeg().get_media_infos('small.mp4')))
        [560, 320]
        >>> print(FFmpeg().get_video_resolution('small.mp4'))
        [560, 320]
        >>> print(FFmpeg().get_video_resolution('small.mp4', index=1))
        None
        >>> print(FFmpeg().get_video_resolution('small.mp4')[HEIGHT])
        320
        >>> print(FFmpeg().get_video_resolution({'streams': [
        ...     {'codec_type': 'audio'},
        ...     {'codec_type': 'video', 'width': '1920', 'height': '1080'}
        ... ]}))
        [1920, 1080]
        """
        video_streams = self.get_video_streams(filename_or_infos)
        try:
            video_stream = video_streams[index]
            return [int(video_stream['width']), int(video_stream['height'])]
        except:
            return None

    def get_now(self):
        return datetime_now()

    def get_size(self, path):
        return filesystem.get_size(path)

    def encode(self, inputs, outputs, options=None, base_track=0, create_directories=True):
        """
        Encode a set of input files input to a set of output files.

        .. note:: Current implementation only handles a unique output.

        **Example usage**

        >>> from ..filesystem import try_remove

        >>> encoder = FFmpeg()

        >>> results = list(encoder.encode(Media('small.mp4'), Media('ff_output.mp4', '-c:a copy -c:v copy')))
        >>> try_remove('ff_output.mp4')
        True
        >>> print(results[-1]['status'])
        SUCCESS

        >>> results = list(encoder.encode(Media('small.mp4'), Media('ff_output.mp4', 'crazy_option')))
        >>> try_remove('ff_output.mp4')
        False
        >>> print(results[-1]['status'])
        ERROR

        >>> results = list(encoder.encode([Media('missing.mp4')], Media('ff_output.mp4', '-c:a copy -c:v copy')))
        >>> try_remove('ff_output.mp4')
        False
        >>> print(results[-1]['status'])
        ERROR
        """
        arguments, inputs, outputs, _ = self._get_arguments(inputs, outputs, options)
        if len(outputs) != 1:
            raise NotImplementedError()

        # Create outputs directories
        if create_directories:
            for output in outputs:
                output.create_directory()

        process = self._get_process(arguments)
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
                            bitrate=stats['bitrate'], quality=stats.get('q'), sanity=None
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
                sanity=self.sanity_min_ratio <= ratio <= self.sanity_max_ratio
            )
        except Exception as exception:
            tb = sys.exc_info()[2]
            try:
                process.kill()
            except OSError as e:
                if e.errno != errno.ESRCH:
                    raise
            raise exception.with_traceback(tb) if hasattr(exception, 'with_traceback') else exception
