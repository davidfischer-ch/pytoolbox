# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime, errno, itertools, json, math, os, re, subprocess

from xml.dom import minidom

from pytoolbox import module
from pytoolbox.datetime import parts_to_time, secs_to_time
from pytoolbox.encoding import string_types
from pytoolbox.subprocess import raw_cmd

from . import miscellaneous, utils

_all = module.All(globals())

DURATION_REGEX = re.compile(r'PT(?P<hours>\d+)H(?P<minutes>\d+)M(?P<seconds>[^S]+)S')


class FFprobe(object):

    executable = 'ffprobe'
    duration_regex = DURATION_REGEX
    format_class = None
    media_class = miscellaneous.Media
    stream_classes = {'audio': None, 'subtitle': None, 'video': None}

    def __init__(self, executable=None):
        self.executable = executable or self.executable

    def __call__(self, *arguments):
        """Call FFprobe with given arguments and return the output (unicode string)."""
        process = raw_cmd(itertools.chain([self.executable], arguments), stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, universal_newlines=True)
        process.wait()
        return process.stdout.read()

    def get_media_duration(self, media, as_delta=False, options=None, fail=False):
        """
        Returns the duration of a media as an instance of time or None in case of error.

        Set `media` to an instance of `self.media_class`, a path or the output of
        `get_media_info()`. If `media` is the path to a MPEG-DASH MPD, then duration will be parser
        from value of key *mediaPresentationDuration*.
        """
        if isinstance(media, string_types) and os.path.splitext(media)[1] == '.mpd':
            mpd = minidom.parse(media)
            if mpd.firstChild.nodeName == 'MPD':
                match = self.duration_regex.search(
                    mpd.firstChild.getAttribute('mediaPresentationDuration'))
                if match is not None:
                    hours, minutes = int(match.group('hours')), int(match.group('minutes'))
                    microseconds, seconds = math.modf(float(match.group('seconds')))
                    microseconds, seconds = int(1000000 * microseconds), int(seconds)
                    return parts_to_time(hours, minutes, seconds, microseconds, as_delta=as_delta)
        else:
            info = self.get_media_info(media, fail)
            try:
                duration = secs_to_time(
                    float(info['format']['duration']), as_delta=as_delta) if info else None
            except KeyError:
                return None
            # ffmpeg may return this so strange value, 00:00:00.04, let it being None
            if duration and (duration >= datetime.timedelta(seconds=1) if as_delta else
                             duration >= datetime.time(0, 0, 1)):
                return duration

    def get_media_info(self, media, fail=False):
        """
        Return a Python dictionary containing information about the media or None in case of error.
        Set `media` to an instance of `self.media_class` or a path.
        If `media` is a Python dictionary, then it is returned.
        """
        if isinstance(media, dict):
            return media
        media = self.to_media(media)
        if not utils.is_pipe(media.path):  # Read media information from a PIPE not yet implemented
            try:
                return json.loads(
                    subprocess.check_output([
                        self.executable, '-v', 'quiet', '-print_format', 'json', '-show_format',
                        '-show_streams', media.path
                    ]).decode('utf-8'))
            except OSError as e:
                # Executable does not exist
                if fail or e.errno == errno.ENOENT:
                    raise
            except:
                if fail:
                    raise

    def get_media_format(self, media, fail=False):
        """
        Return information about the container (and file) or None in case of error.
        Set `media` to an instance of `self.media_class`, a path or the output of
        `get_media_info()`.
        """
        info = self.get_media_info(media, fail)
        try:
            cls, the_format = self.format_class, info['format']
            if cls and not isinstance(the_format, cls):
                return cls(the_format)  # pylint:disable=not-callable
            else:
                return the_format
        except:
            if fail:
                raise

    def get_media_streams(self, media, condition=lambda stream: True, fail=False):
        """
        Return a list with the media streams of `media` or [] in case of error.
        Set `media` to an instance of `self.media_class`, a path or the output of
        `get_media_info()`.
        """
        info = self.get_media_info(media, fail)
        try:
            raw_streams = (s for s in info['streams'] if condition(s))
        except:
            if fail:
                raise
            return []
        streams = []
        for stream in raw_streams:
            stream_class = self.stream_classes[stream['codec_type']]
            streams.append(
                stream_class(stream) if stream_class and not isinstance(stream, stream_class)
                else stream)
        return streams

    def get_audio_streams(self, media, fail=False):
        """
        Return a list with the audio streams of `media` or [] in case of error.
        Set `media` to an instance of `self.media_class`, a path or the output of
        `get_media_info()`.
        """
        return self.get_media_streams(
            media, condition=lambda s: s['codec_type'] == 'audio', fail=fail)

    def get_subtitle_streams(self, media, fail=False):
        """
        Return a list with the subtitle streams of `media` or [] in case of error.
        Set `media` to an instance of `self.media_class`, a path or the output of
        `get_media_info()`.
        """
        return self.get_media_streams(
            media, condition=lambda s: s['codec_type'] == 'subtitle', fail=fail)

    def get_video_streams(self, media, fail=False):
        """
        Return a list with the video streams of `media` or [] in case of error.
        Set `media` to an instance of `self.media_class`, a path or the output of
        `get_media_info()`.
        """
        return self.get_media_streams(
            media, condition=lambda s: s['codec_type'] == 'video', fail=fail)

    def get_video_frame_rate(self, media, index=0, fail=False):
        """
        Return the frame rate of the video stream at `index` in `media` or None in case of error.
        Set `media` to an instance of `self.media_class`, a path or the output of
        `get_media_info()`.
        """
        try:
            stream = self.get_video_streams(media)[index]
            if isinstance(stream, dict):
                return utils.to_frame_rate(stream['avg_frame_rate'])
            else:
                return stream.avg_frame_rate
        except:
            if fail:
                raise

    def get_video_resolution(self, media, index=0, fail=False):
        """
        Return [width, height] of the video stream at `index` in `media` or None in case of error.
        Set `media` to an instance of `self.media_class`, a path or the output of
        `get_media_info()`.
        """
        try:
            stream = self.get_video_streams(media)[index]
            is_dict = isinstance(stream, dict)
            if is_dict:
                return [int(stream['width']), int(stream['height'])]
            else:
                return [stream.width, stream.height]
        except:
            if fail:
                raise

    def to_media(self, media):
        return media if isinstance(media, self.media_class) else self.media_class(media)


__all__ = _all.diff(globals())
