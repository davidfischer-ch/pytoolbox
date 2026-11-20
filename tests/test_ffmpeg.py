"""Tests for the multimedia.ffmpeg module."""

# pylint:disable=protected-access,use-implicit-booleaness-not-comparison,too-few-public-methods
from __future__ import annotations

import concurrent.futures
import json
import shutil
import subprocess
import sys
import textwrap
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any, Final

import pytest

from pytoolbox import filesystem
from pytoolbox.multimedia import ffmpeg

MPD_TEST: Final[str] = """<?xml version="1.0"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT0H6M7.83S">
  <useless text="testing encoding : ça va ou bien ?" />
</MPD>
"""

# This is ffprobe's result on small.mp4 to reverse engineer tests in case we loose it!
SMALL_MP4_MEDIA_INFOS: Final[dict[str, Any]] = json.loads(
    (Path(__file__).parent / 'small.json').read_text(encoding='utf-8'),
)


def test_to_bit_rate() -> None:
    """to_bit_rate() converts bitrate strings to bits per second."""
    assert ffmpeg.to_bit_rate('231.5kbit/s') == 231500
    assert ffmpeg.to_bit_rate('3302.3kbits/s') == 3302300
    assert ffmpeg.to_bit_rate('1935.9kbits/s') == 1935900
    assert ffmpeg.to_bit_rate('N/A') is None


def test_to_frame_rate() -> None:
    """to_frame_rate() converts frame rate strings to float."""
    assert ffmpeg.to_frame_rate('10.5') == 10.5
    assert ffmpeg.to_frame_rate(25.0) == 25.0
    assert ffmpeg.to_frame_rate('59000/1000') == 59.0
    assert ffmpeg.to_frame_rate('10/0') is None


def test_to_size() -> None:
    """to_size() converts size strings to bytes."""
    assert ffmpeg.to_size('231.5kB') == 237056
    assert ffmpeg.to_size('3302.3MB') == 3462712524
    assert ffmpeg.to_size('1935.9KB') == 1982361
    assert ffmpeg.to_size('N/A') is None


def test_media(tmp_path: Path) -> None:
    """Media handles path, pipe, and directory creation correctly."""
    with pytest.raises(TypeError):
        ffmpeg.Media(None)  # type: ignore[arg-type]

    media = ffmpeg.Media('test-file.mp4')
    assert media.path == Path('test-file.mp4')
    assert media.is_pipe is False
    assert media.size == 0

    media = ffmpeg.Media(Path('other-file.mp4'))
    assert media.path == Path('other-file.mp4')
    assert media.is_pipe is False
    assert media.size == 0

    for path in '-', 'pipe:3':
        media = ffmpeg.Media(path)
        assert media.directory is None
        assert media.is_pipe is True
        assert media.size == 0
        assert media.create_directory() is False

    media_path = tmp_path / 'some/test.txt'
    media = ffmpeg.Media(media_path)
    assert media.directory == tmp_path / 'some'
    assert media.is_pipe is False
    assert media.path == media_path
    assert media.size == 0
    assert media.create_directory() is True
    assert (tmp_path / 'some').is_dir()
    assert media.create_directory() is False
    media_path.write_text('This is a text file.', encoding='utf-8')
    assert media.size == 20


def test_media_to_args_of_a_relative_path() -> None:
    """A relative path reaches FFmpeg as a file, never as an option or a protocol."""
    assert ffmpeg.Media('-y.mp4').to_args(is_input=False) == ['./-y.mp4']
    assert ffmpeg.Media('concat:a.ts|b.ts', '-f mpegts').to_args(is_input=True) == [
        '-f',
        'mpegts',
        '-i',
        './concat:a.ts|b.ts',
    ]
    assert ffmpeg.Media('/media/output.mp4').to_args(is_input=False) == ['/media/output.mp4']
    assert ffmpeg.Media('pipe:1').to_args(is_input=False) == ['pipe:1']


def test_statistics_compute_ratio(statistics: ffmpeg.EncodeStatistics) -> None:
    """_compute_ratio() returns correct ratio based on input/output duration."""
    statistics.input.duration = timedelta(seconds=0)
    statistics.output.duration = None
    assert statistics._compute_ratio() is None
    statistics.input.duration = timedelta(seconds=0)
    statistics.output.duration = timedelta(0)
    assert statistics._compute_ratio() is None
    statistics.input.duration = timedelta(seconds=1)
    assert statistics._compute_ratio() == 0.0
    statistics.input.duration = timedelta(seconds=60)
    statistics.output.duration = timedelta(seconds=30)
    assert statistics._compute_ratio() == 0.5


def test_statistics_compute_ratio_frame_based(
    frame_based_statistics: ffmpeg.EncodeStatistics,
) -> None:
    """_compute_ratio() uses frame counts when available."""
    assert frame_based_statistics.input.frame > 0
    frame_based_statistics.input.duration = timedelta(seconds=60)
    frame_based_statistics.output.duration = timedelta(seconds=30)
    frame_based_statistics.frame, frame_based_statistics.input.frame = 0, 100
    assert frame_based_statistics._compute_ratio() == 0.0
    frame_based_statistics.frame = 60
    frame_based_statistics.input.frame = 100
    assert frame_based_statistics._compute_ratio() == 0.6


def test_statistics_eta_time(statistics: ffmpeg.EncodeStatistics) -> None:
    """eta_time calculates remaining time based on elapsed and ratio."""
    statistics.elapsed_time = timedelta(seconds=60)
    assert statistics.eta_time is None
    statistics.ratio = 0.0
    assert statistics.eta_time is None
    statistics.ratio = 0.2
    assert statistics.eta_time == timedelta(seconds=240)
    statistics.ratio = 0.5
    assert statistics.eta_time == timedelta(seconds=60)
    statistics.ratio = 1.0
    assert statistics.eta_time == timedelta(0)


def test_statistics_parse_chunk(statistics: ffmpeg.EncodeStatistics) -> None:
    """_parse_chunk() extracts frame, time, size, and bitrate from ffmpeg output."""
    assert statistics._parse_chunk('Random stuff') is None
    assert statistics._parse_chunk(
        '   frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s  ',
    ), {
        'frame': 2071,
        'frame_rate': 0.0,
        'qscale': -1.0,
        'size': 34623 * 1024,
        'time': timedelta(minutes=1, seconds=25.89),
        'bit_rate': 3302300,
    }


def test_statistics_parse_chunk_size_not_available(statistics: ffmpeg.EncodeStatistics) -> None:
    """An output without a size (null muxer, first pass) keeps the progress line's statistics."""
    assert statistics._parse_chunk(
        'frame=  250 fps=0.0 q=-0.0 size=N/A time=00:00:10.00 bitrate=N/A speed= 500x',
    ) == {
        'frame': 250,
        'frame_rate': 0.0,
        'qscale': -0.0,
        'size': None,
        'time': timedelta(seconds=10),
        'bit_rate': None,
    }


def test_statistics_subclip_duration_and_size(statistics: ffmpeg.EncodeStatistics) -> None:
    """_get_subclip_duration_and_size() calculates duration/size from ffmpeg args."""
    subclip = statistics._get_subclip_duration_and_size
    size = 512 * 1024
    duration = timedelta(hours=1, minutes=30, seconds=36.5)
    sub_dur_1 = timedelta(seconds=3610.2)
    sub_dur_2 = timedelta(hours=1, minutes=20, seconds=15.8)
    sub_dur_3 = timedelta(minutes=40, seconds=36.3)
    sub_dur_4 = timedelta(0)
    assert subclip(duration, size, []) == (duration, size)
    assert subclip(duration, size, ['-t']) == (duration, size)
    assert subclip(duration, size, ['-t', '-t']) == (duration, size)
    assert subclip(duration, size, ['-t', '3610.2']) == (sub_dur_1, 348162)
    assert subclip(duration, size, ['-t', '01:20:15.8']) == (sub_dur_2, 464428)
    assert subclip(duration, size, ['-t', '01:20:15.8', '-ss', '00:50:00.2']) == (sub_dur_3, 234953)
    assert subclip(duration, size, ['-t', '01:20:15.8', '-ss', '01:30:36.5']) == (sub_dur_4, 0)
    assert subclip(duration, size, ['-ss', '01:30:53']) == (sub_dur_4, 0)
    assert subclip(duration, size, ['-t', '02:00:00.0']) == (duration, size)


def test_statistics_new_properties(statistics: ffmpeg.EncodeStatistics) -> None:
    """EncodeStatistics in NEW state has correct initial property values."""
    assert statistics.state == statistics.states.NEW
    assert isinstance(statistics.input.duration, timedelta)
    assert statistics.eta_time is None
    assert statistics.input == statistics.inputs[0]
    assert statistics.output == statistics.outputs[0]
    assert statistics.ratio is None
    assert statistics.input._size is not None


def test_statistics_started_properties(statistics: ffmpeg.EncodeStatistics) -> None:
    """EncodeStatistics in STARTED state has output duration set to zero."""
    statistics.start('process')
    assert statistics.state == statistics.states.STARTED
    assert statistics.output.duration == timedelta(0)
    assert statistics.eta_time is None
    assert statistics.ratio == 0.0


def test_statistics_success_properties(statistics: ffmpeg.EncodeStatistics) -> None:
    """EncodeStatistics in SUCCESS state has ratio 1.0 and matched durations."""
    statistics.start('process')
    statistics.progress('')
    shutil.copy(statistics.input.path, statistics.output.path)  # Generate output
    statistics.end(0)
    assert statistics.state == statistics.states.SUCCESS
    assert statistics.output.duration == statistics.input.duration
    assert statistics.eta_time == timedelta(0)
    assert statistics.ratio == 1.0
    assert statistics.output._size is None


def test_ffmpeg_call_output_not_utf8(tmp_path: Path) -> None:
    """The log of a process started by a call is text even where it is not valid UTF-8."""
    executable = _write_executable(
        tmp_path / 'ffmpeg',
        r"""
        import os

        os.write(2, b'Caf\xe9\n')
        """,
    )
    assert ffmpeg.FFmpeg(executable)('-version').communicate() == (None, 'Caf\ufffd\n')


def test_ffmpeg_clean_medias_argument() -> None:
    """_clean_medias_argument() normalizes input to a list of Media objects."""
    clean = ffmpeg.FFmpeg()._clean_medias_argument
    assert clean(None) == []
    assert clean([]) == []
    assert clean('a.mp4') == [ffmpeg.Media('a.mp4')]
    assert clean(['a.mp4', 'b.mp3']) == [ffmpeg.Media('a.mp4'), ffmpeg.Media('b.mp3')]
    assert clean(ffmpeg.Media('a', '-f mp4')) == [ffmpeg.Media('a', ['-f', 'mp4'])]
    assert clean([ffmpeg.Media('a', ['-f', 'mp4']), ffmpeg.Media('b.mp3')]) == [
        ffmpeg.Media('a', ['-f', 'mp4']),
        ffmpeg.Media('b.mp3'),
    ]


def test_ffmpeg_encode(
    static_ffmpeg: type[ffmpeg.FFmpeg],
    small_mp4: Path,
    tmp_path: Path,
) -> None:
    """FFmpeg.encode() handles success and failure cases correctly."""
    encoder = static_ffmpeg()

    results = list(
        encoder.encode(
            ffmpeg.Media(small_mp4),
            ffmpeg.Media(tmp_path / 'output.mp4', '-c:a copy -c:v copy'),
        ),
    )
    assert filesystem.remove(tmp_path / 'output.mp4') is True
    assert results[-1].state == ffmpeg.EncodeState.SUCCESS

    results = list(
        encoder.encode(
            ffmpeg.Media(small_mp4),
            ffmpeg.Media(tmp_path / 'output.mp4', 'crazy_option'),
        ),
    )
    assert filesystem.remove(tmp_path / 'output.mp4') is False
    assert results[-1].state == ffmpeg.EncodeState.FAILURE

    results = list(
        encoder.encode(
            [ffmpeg.Media('missing.mp4')],
            ffmpeg.Media(tmp_path / 'output.mp4', '-c:a copy -c:v copy'),
        ),
    )
    assert filesystem.remove(tmp_path / 'output.mp4') is False
    assert results[-1].state == ffmpeg.EncodeState.FAILURE


def test_ffmpeg_encode_output_not_utf8(
    static_ffmpeg: type[ffmpeg.FFmpeg],
    small_mp4: Path,
    tmp_path: Path,
) -> None:
    """Output that is not valid UTF-8, or a character split between two reads, keeps encoding."""
    encoder = static_ffmpeg(chunk_read_timeout=0.1, encode_poll_delay=0.1)
    encoder.executable = _write_executable(
        tmp_path / 'ffmpeg',
        r"""
        import os
        import time

        os.write(2, b'title : Caf\xe9\n')
        os.write(2, b'title : Caf\xc3')
        time.sleep(0.3)
        os.write(2, b'\xa9 au lait\n')
        """,
    )
    results = list(encoder.encode(small_mp4, tmp_path / 'output.mp4'))
    assert results[-1].state == ffmpeg.EncodeState.SUCCESS
    assert results[-1].process_output == 'title : Caf\ufffd\ntitle : Café au lait\n'


def test_ffmpeg_get_arguments() -> None:
    """_get_arguments() builds correct ffmpeg command-line arguments."""
    get = ffmpeg.FFmpeg()._get_arguments
    executable = Path('ffmpeg')

    # Using options (the legacy API, also simplify simple calls)
    in_o_str = '-strict experimental -vf "yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2"'

    args, inputs, outputs, in_options, out_options = get('input.mp4', 'output.mkv', in_o_str)
    assert inputs == [ffmpeg.Media('input.mp4')]
    assert outputs == [ffmpeg.Media('output.mkv')]
    assert in_options == [
        '-strict',
        'experimental',
        '-vf',
        'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2',
    ]
    assert args == [
        executable,
        '-y',
        *in_options,
        '-i',
        './input.mp4',
        *out_options,
        './output.mkv',
    ]

    args, _, outputs, in_options, out_options = get('input.mp4', None, in_o_str)
    assert args == [executable, '-y', *in_options, '-i', './input.mp4']
    assert outputs == []

    # Using instances of Media (the newest API, greater flexibility)
    args, inputs, outputs, in_options, out_options = get(
        ffmpeg.Media('in', '-f mp4'),
        ffmpeg.Media('out.mkv', '-acodec copy -vcodec copy'),
    )
    assert inputs == [ffmpeg.Media('in', ['-f', 'mp4'])]
    assert outputs == [ffmpeg.Media('out.mkv', ['-acodec', 'copy', '-vcodec', 'copy'])]
    assert in_options == []
    assert out_options == []
    assert args == [
        executable,
        '-y',
        '-f',
        'mp4',
        '-i',
        './in',
        '-acodec',
        'copy',
        '-vcodec',
        'copy',
        './out.mkv',
    ]


def test_ffmpeg_get_frames_md5_checksum_covers_every_frame(
    monkeypatch: pytest.MonkeyPatch,
    static_ffmpeg: type[ffmpeg.FFmpeg],
    tmp_path: Path,
) -> None:
    """Two medias sharing their first frame but not the next ones have different checksums."""
    executable = static_ffmpeg().executable
    monkeypatch.setattr(ffmpeg.FFmpeg, 'executable', executable)
    still = 'color=c=black:s=16x16:r=5:d=1'
    changing = rf'{still},drawbox=c=white:t=fill:enable=gte(n\,1)'
    checksums: set[str | None] = set()
    for name, video_filter in ('still.mkv', still), ('changing.mkv', changing):
        subprocess.run(
            [executable, '-v', 'error', '-f', 'lavfi', '-i', video_filter, tmp_path / name],
            check=True,
        )
        checksums.add(ffmpeg.FFmpeg.get_frames_md5_checksum(tmp_path / name))
    assert len(checksums) == 2
    assert None not in checksums


def test_ffmpeg_get_frames_md5_checksum_drains_the_log(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """
    A log longer than the pipe buffer cannot block FFmpeg while get_frames_md5_checksum() waits on
    the process.
    """
    executable = _write_executable(
        tmp_path / 'ffmpeg',
        f"""
        import pathlib
        import signal
        import sys

        signal.alarm(10)  # Ends a blocked stand-in, to keep a failing run from hanging.
        sys.stderr.write('frame=1 fps=0.0\\n' * 16_384)
        pathlib.Path(sys.argv[-1]).write_text('MD5={'0' * 32}\\n', encoding='utf-8')
        """,
    )
    monkeypatch.setattr(ffmpeg.FFmpeg, 'executable', executable)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(ffmpeg.FFmpeg.get_frames_md5_checksum, tmp_path / 'input.mkv')
        assert future.result(timeout=5) == '0' * 32


def test_ffmpeg_get_process(static_ffmpeg: type[ffmpeg.FFmpeg]) -> None:
    """_get_process() creates a subprocess with correct arguments."""
    get = ffmpeg.FFmpeg()._get_process
    executable = static_ffmpeg.executable
    options = [
        '-strict',
        'experimental',
        '-vf',
        'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2',
    ]
    process = get([executable, '-y', '-i', 'in.mp4', *options, 'out.mkv'])
    process.terminate()
    assert process.args == [str(executable), '-y', '-i', 'in.mp4', *options, 'out.mkv']


def test_ffmpeg_kill_process_handle_missing(
    static_ffmpeg: type[ffmpeg.FFmpeg],
    small_mp4: Path,
    tmp_path: Path,
) -> None:
    """FFmpeg handles exceptions during process cleanup gracefully."""

    class SomeError(Exception):
        """Test class."""

    class RaiseEncodeStatistics(static_ffmpeg.statistics_class):  # type: ignore[name-defined]
        """Test statistics class."""

        @staticmethod
        def end(returncode):
            """End method that raises SomeError."""
            raise SomeError('This is the error.')

    encoder = static_ffmpeg()
    encoder.statistics_class = RaiseEncodeStatistics
    with pytest.raises(SomeError):
        list(encoder.encode(small_mp4, tmp_path / 'out.mp4', out_options='-c:a copy -c:v copy'))
    assert filesystem.remove(tmp_path / 'out.mp4') is True


def test_ffprobe_call_drains_the_output(tmp_path: Path) -> None:
    """An output longer than the pipe buffer is returned whole, as text even where not UTF-8."""
    executable = _write_executable(
        tmp_path / 'ffprobe',
        r"""
        import signal
        import sys

        signal.alarm(10)  # Ends a blocked stand-in, to keep a failing run from hanging.
        sys.stdout.buffer.write(b'Caf\xe9\n' * 16_384)
        """,
    )
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(ffmpeg.FFprobe(executable), '-version')
        assert future.result(timeout=5) == 'Caf\ufffd\n' * 16_384


def test_ffprobe_get_audio_streams(static_ffmpeg: type[ffmpeg.FFmpeg], small_mp4: Path) -> None:
    """FFprobe.get_audio_streams() returns audio stream info as dict or AudioStream."""
    probe = static_ffmpeg.ffprobe_class()

    probe.stream_classes['audio'] = None
    (audio_stream,) = probe.get_audio_streams(small_mp4)
    assert isinstance(audio_stream, dict)
    assert audio_stream['avg_frame_rate'] == '0/0'
    assert audio_stream['channels'] == 1
    assert 'codec_time_base' not in audio_stream  # Missing in dump from ffprobe version 6.1

    probe.stream_classes['audio'] = ffmpeg.AudioStream
    (audio_stream,) = probe.get_audio_streams(small_mp4)
    assert isinstance(audio_stream, ffmpeg.AudioStream)
    assert audio_stream.avg_frame_rate is None
    assert audio_stream.channels == 1
    assert audio_stream.codec.time_base == 1 / 48000


def test_ffprobe_get_media_duration(
    static_ffmpeg: type[ffmpeg.FFmpeg],
    small_mp4: Path,
    tmp_path: Path,
) -> None:
    """FFprobe.get_media_duration() extracts duration from various media formats."""
    probe = static_ffmpeg.ffprobe_class()

    # Some random bad things
    assert probe.get_media_duration({}) is None

    # Bad file format
    txt_file = tmp_path / 'test.txt'
    txt_file.write_text('Hey, I am not a MPD nor a média', encoding='utf-8')
    assert probe.get_media_duration(txt_file) is None

    # A MPEG-DASH MPD
    mpd_file = tmp_path / 'test.mpd'
    mpd_file.write_text(MPD_TEST, encoding='utf-8')
    assert probe.get_media_duration(mpd_file).strftime('%H:%M:%S.%f') == '00:06:07.830000'
    assert probe.get_media_duration(mpd_file, as_delta=True) == timedelta(0, 367, 830000)

    # A MP4
    assert probe.get_media_duration(small_mp4).strftime('%H:%M:%S') == '00:00:05'
    assert (
        probe.get_media_duration(probe.get_media_info(small_mp4)).strftime('%H:%M:%S') == '00:00:05'
    )
    assert probe.get_media_duration(probe.get_media_info(small_mp4), as_delta=True).seconds == 5


def test_ffprobe_get_media_format(static_ffmpeg, small_mp4) -> None:
    """FFprobe.get_media_format() returns format info as dict or Format object."""
    probe = static_ffmpeg.ffprobe_class()

    probe.format_class = None
    media_format = probe.get_media_format(small_mp4, fail=True)
    assert isinstance(media_format, dict)
    assert media_format['bit_rate'] == '551193'
    assert media_format['format_long_name'] == 'QuickTime / MOV'
    assert media_format['probe_score'] == 100

    probe.format_class = ffmpeg.Format
    media_format = probe.get_media_format(small_mp4, fail=True)
    assert isinstance(media_format, ffmpeg.Format)
    assert media_format.bit_rate == 551193
    assert media_format.format_long_name == 'QuickTime / MOV'
    assert media_format.probe_score == 100


def test_ffprobe_get_media_info_errors_handling(static_ffmpeg: type[ffmpeg.FFmpeg]) -> None:
    """FFprobe.get_media_info() handles missing executable gracefully."""
    probe = static_ffmpeg.ffprobe_class()
    probe.executable = Path(str(uuid.uuid4()))
    with pytest.raises(OSError):
        probe.get_media_info('another.mp4', fail=False)


def test_ffprobe_get_media_info_of_a_name_like_an_option(
    monkeypatch: pytest.MonkeyPatch,
    static_ffmpeg: type[ffmpeg.FFmpeg],
    small_mp4: Path,
    tmp_path: Path,
) -> None:
    """A media named like an option, in the working directory, is probed as a file."""
    monkeypatch.chdir(tmp_path)
    shutil.copy(small_mp4, tmp_path / '-version.mp4')
    info = static_ffmpeg.ffprobe_class().get_media_info('-version.mp4', fail=True)
    assert info['format']['format_name'] == SMALL_MP4_MEDIA_INFOS['format']['format_name']


def test_ffprobe_get_media_info_output_not_utf8(tmp_path: Path) -> None:
    """A tag that is not valid UTF-8 keeps the information of the media."""
    executable = _write_executable(
        tmp_path / 'ffprobe',
        r"""
        import sys

        sys.stdout.buffer.write(b'{"format": {"tags": {"title": "Caf\xe9"}}}')
        """,
    )
    assert ffmpeg.FFprobe(executable).get_media_info('input.mkv') == {
        'format': {'tags': {'title': 'Caf\ufffd'}},
    }


def test_ffprobe_get_media_streams_errors_handling() -> None:
    """A stream that does not convert makes an empty list, or raises if asked to."""
    probe = ffmpeg.FFprobe()
    probe.stream_classes = {'audio': None, 'subtitle': None, 'video': ffmpeg.VideoStream}
    info = {'streams': [{'codec_type': 'video', 'width': 'wide'}]}
    assert probe.get_media_streams(info) == []
    with pytest.raises(ValueError):
        probe.get_media_streams(info, fail=True)


def test_ffprobe_get_media_streams_of_any_type() -> None:
    """A stream neither audio, subtitle nor video, or of no type, is listed and never fails."""
    probe = ffmpeg.FFprobe()
    probe.stream_classes = {'audio': None, 'subtitle': None, 'video': ffmpeg.VideoStream}
    video, data, untyped = {'codec_type': 'video'}, {'codec_type': 'data'}, {'index': 2}
    info = {'streams': [video, data, untyped]}
    streams = probe.get_media_streams(info, fail=True)
    assert [type(stream) for stream in streams] == [ffmpeg.VideoStream, dict, dict]
    assert streams[1:] == [data, untyped]
    assert probe.get_audio_streams(info, fail=True) == []
    assert len(probe.get_video_streams(info, fail=True)) == 1


def test_ffprobe_get_video_streams(static_ffmpeg: type[ffmpeg.FFmpeg], small_mp4: Path) -> None:
    """FFprobe.get_video_streams() returns video stream info as dict or VideoStream."""
    probe = static_ffmpeg.ffprobe_class()

    probe.stream_classes['video'] = None
    (video_stream,) = probe.get_video_streams(small_mp4)
    assert isinstance(video_stream, dict)
    assert video_stream['avg_frame_rate'] == '30/1'

    probe.stream_classes['video'] = ffmpeg.VideoStream
    (video_stream,) = probe.get_video_streams(small_mp4)
    assert isinstance(video_stream, ffmpeg.VideoStream)
    assert video_stream.avg_frame_rate == 30.0


def test_ffprobe_get_video_frame_rate(static_ffmpeg: type[ffmpeg.FFmpeg], small_mp4: Path) -> None:
    """FFprobe.get_video_frame_rate() extracts frame rate from video file."""
    probe = static_ffmpeg.ffprobe_class()
    assert probe.get_video_frame_rate(3.14159265358979323846) is None
    assert probe.get_video_frame_rate({}) is None
    assert probe.get_video_frame_rate(probe.get_media_info(small_mp4)) == 30.0
    assert probe.get_video_frame_rate(small_mp4) == 30.0


def test_ffprobe_get_video_resolution(static_ffmpeg: type[ffmpeg.FFmpeg], small_mp4: Path) -> None:
    """FFprobe.get_video_resolution() extracts video dimensions."""
    probe = static_ffmpeg.ffprobe_class()
    assert probe.get_video_resolution(3.14159265358979323846) is None
    assert probe.get_video_resolution({}) is None
    assert probe.get_video_resolution(probe.get_media_info(small_mp4)) == [560, 320]
    assert probe.get_video_resolution(small_mp4) == [560, 320]
    assert probe.get_video_resolution(small_mp4, index=1) is None
    assert probe.get_video_resolution(small_mp4)[ffmpeg.HEIGHT] == 320


# --- Internals ------------------------------------------------------------------------------------


def _write_executable(path: Path, script: str) -> Path:
    """Write *script* as a Python program at *path*, to stand in for FFmpeg or FFprobe."""
    path.write_text(f'#!{sys.executable}\n{textwrap.dedent(script)}', encoding='utf-8')
    path.chmod(0o755)
    return path
