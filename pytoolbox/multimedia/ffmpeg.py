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

import datetime, errno, json, math, os, re, select, shlex, sys, time
from subprocess import check_output, Popen, PIPE
from xml.dom import minidom

from .. import filesystem
from ..datetime import datetime_now, parts_to_time, secs_to_time, str2time, time_ratio
from ..encoding import string_types
from ..subprocess import make_async

__all__ = ('ENCODING_REGEX', 'DURATION_REGEX', 'WIDTH', 'HEIGHT', 'MPD_TEST', 'FFmpeg')

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


class FFmpeg(object):

    duration_regex = DURATION_REGEX
    encoding_regex = ENCODING_REGEX
    encoding_executable = 'ffmpeg'
    parsing_executable = 'ffprobe'

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

    def _get_arguments(self, in_filenames, out_filename, options):
        """
        Return the arguments for the encoding process.

        * Set in_filenames to a string or a "list" with the input filenames.
        * Set out_filename to a string.
        * Set argument to a string or a list with the options for the process (except ones related to input(s)/output).

        In return you will get a tuple with (arguments, in_filenames -> list, out_filename -> str, options -> list).

        **Example usage**

        >>> from nose.tools import assert_list_equal as leq_
        >>> options_string = '-strict experimental -vf "yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2"'
        >>> get_args = FFmpeg()._get_arguments

        >>> args, in_filenames, out_filename, options = get_args('input.mp4', 'output.mkv', options_string)
        >>> leq_(in_filenames, ['input.mp4'])
        >>> leq_(options, ['-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'])
        >>> leq_(args, ['ffmpeg', '-y', '-i', 'input.mp4'] + options + ['output.mkv'])

        >>> args, in_filenames, out_filename, options = get_args({'input.avi'}, 'output.mp4', options_string)
        >>> leq_(in_filenames, ['input.avi'])
        >>> leq_(options, ['-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'])
        >>> leq_(args, ['ffmpeg', '-y', '-i', 'input.avi'] + options + ['output.mp4'])

        >>> args, in_filenames, out_filename, options = get_args(('video.h264', 'audio.mp3'), 'output.mp4', options)
        >>> leq_(sorted(in_filenames), ['audio.mp3', 'video.h264'])
        >>> leq_(options, ['-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'])
        >>> leq_(args, ['ffmpeg', '-y', '-i', 'video.h264', '-i', 'audio.mp3'] + options + ['output.mp4'])
        """
        in_filenames = [f for f in ([in_filenames] if isinstance(in_filenames, string_types) else in_filenames)]
        options = (shlex.split(options) if isinstance(options, string_types) else options) or []

        args = [self.encoding_executable, '-y']
        for in_filename in in_filenames:
            args.extend(['-i', in_filename])
        args.extend(options + [out_filename])
        return args, in_filenames, out_filename, options

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
        out_duration = str2time(stats['time'])
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

    def get_media_resolution(self, filename_or_infos):
        """
        Return [width, height] of the first video stream in ``filename_or_infos`` or None in case of error.

        **Example usage**

        >>> print(FFmpeg().get_media_resolution(3.14159265358979323846))
        None
        >>> print(FFmpeg().get_media_resolution({}))
        None
        >>> print(FFmpeg().get_media_resolution(FFmpeg().get_media_infos('small.mp4')))
        [560, 320]
        >>> print(FFmpeg().get_media_resolution('small.mp4'))
        [560, 320]
        >>> print(FFmpeg().get_media_resolution('small.mp4')[HEIGHT])
        320
        >>> print(FFmpeg().get_media_resolution({'streams': [
        ...     {'codec_type': 'audio'},
        ...     {'codec_type': 'video', 'width': '1920', 'height': '1080'}
        ... ]}))
        [1920, 1080]
        """
        if not isinstance(filename_or_infos, dict):
            filename_or_infos = self.get_media_infos(filename_or_infos)
        try:
            first_video_stream = next(s for s in filename_or_infos['streams'] if s['codec_type'] == 'video')
            return [int(first_video_stream['width']), int(first_video_stream['height'])]
        except:
            return None

    def get_now(self):
        return datetime_now()

    def get_size(self, path):
        return filesystem.get_size(path)

    def encode(self, in_filenames, out_filename, options, base_track=0, create_out_directory=True):
        """
        Encode a set of input files input an output file.

        **Example usage**

        >>> from ..filesystem import try_remove

        >>> encoder = FFmpeg()

        >>> results = list(encoder.encode('small.mp4', 'ff_output.mp4', '-c:a copy -c:v copy'))
        >>> try_remove('ff_output.mp4')
        True
        >>> print(results[-1]['status'])
        SUCCESS

        >>> results = list(encoder.encode('small.mp4', 'ff_output.mp4', 'crazy_option'))
        >>> try_remove('ff_output.mp4')
        False
        >>> print(results[-1]['status'])
        ERROR

        >>> results = list(encoder.encode({'missing.mp4'}, 'ff_output.mp4', '-c:a copy -c:v copy'))
        >>> try_remove('ff_output.mp4')
        False
        >>> print(results[-1]['status'])
        ERROR
        """
        arguments, in_filenames, out_filename, options = self._get_arguments(in_filenames, out_filename, options)

        # Create output directory
        if create_out_directory:
            directory = os.path.dirname(out_filename)
            if directory:
                filesystem.try_makedirs(directory)

        process = self._get_process(arguments)
        try:
            # Get input media duration and size to be able to estimate ETA
            in_duration = self.get_media_duration(in_filenames[base_track]) or self.default_in_duration
            in_size = self.get_size(in_filenames[base_track])

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
                            in_duration=in_duration, out_size=self.get_size(out_filename), out_duration=out_duration,
                            frame=int(stats['frame']), fps=float(stats['fps']), bitrate=stats['bitrate'],
                            quality=stats.get('q'), sanity=None
                        )
                returncode = process.poll()
                if returncode is not None:
                    break

            # Output media file sanity check
            out_duration = self.get_media_duration(out_filename)
            ratio = time_ratio(out_duration, in_duration) if out_duration else 0.0
            frame = int(stats.get('frame', 0))  # FIXME compute latest frame based on output infos
            fps = float(stats.get('fps', 0))  # FIXME compute average fps
            yield self._clean_statistics(
                stats=stats, status='ERROR' if returncode else 'SUCCESS', output=output, returncode=returncode,
                start_date=start_date, elapsed_time=datetime.timedelta(seconds=elapsed_time),
                eta_time=datetime.timedelta(0), ratio=ratio if returncode else 1.0, in_size=in_size,
                in_duration=in_duration, out_size=self.get_size(out_filename), out_duration=out_duration, frame=frame,
                fps=fps, bitrate=stats.get('bitrate'), quality=stats.get('q'),
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
