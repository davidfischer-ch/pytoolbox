# pylint:disable=too-few-public-methods
from __future__ import annotations

from pathlib import Path
from typing import Any, Final
import datetime
import json
import shutil
import uuid

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
    (Path(__file__).parent / 'small.json').read_text(encoding='utf-8'))


def test_to_bit_rate() -> None:
    assert ffmpeg.to_bit_rate('231.5kbit/s') == 231500
    assert ffmpeg.to_bit_rate('3302.3kbits/s') == 3302300
    assert ffmpeg.to_bit_rate('1935.9kbits/s') == 1935900
    assert ffmpeg.to_bit_rate('N/A') is None


def test_to_frame_rate() -> None:
    assert ffmpeg.to_frame_rate('10.5') == 10.5
    assert ffmpeg.to_frame_rate(25.0) == 25.0
    assert ffmpeg.to_frame_rate('59000/1000') == 59.0
    assert ffmpeg.to_frame_rate('10/0') is None


def test_to_size() -> None:
    assert ffmpeg.to_size('231.5kB') == 237056
    assert ffmpeg.to_size('3302.3MB') == 3462712524
    assert ffmpeg.to_size('1935.9KB') == 1982361


def test_media(tmp_path: Path) -> None:
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


def test_statistics_compute_ratio(statistics: ffmpeg.EncodeStatistics) -> None:
    statistics.input.duration = datetime.timedelta(seconds=0)
    statistics.output.duration = None
    assert statistics._compute_ratio() is None  # pylint:disable=protected-access
    statistics.input.duration = datetime.timedelta(seconds=0)
    statistics.output.duration = datetime.timedelta(0)
    assert statistics._compute_ratio() is None  # pylint:disable=protected-access
    statistics.input.duration = datetime.timedelta(seconds=1)
    assert statistics._compute_ratio() == 0.0  # pylint:disable=protected-access
    statistics.input.duration = datetime.timedelta(seconds=60)
    statistics.output.duration = datetime.timedelta(seconds=30)
    assert statistics._compute_ratio() == 0.5  # pylint:disable=protected-access


def test_statistics_compute_ratio_frame_based(
    frame_based_statistics: ffmpeg.EncodeStatistics
) -> None:
    assert frame_based_statistics.input.frame > 0
    frame_based_statistics.input.duration = datetime.timedelta(seconds=60)
    frame_based_statistics.output.duration = datetime.timedelta(seconds=30)
    frame_based_statistics.frame, frame_based_statistics.input.frame = 0, 100
    assert frame_based_statistics._compute_ratio() == 0.0  # pylint:disable=protected-access
    frame_based_statistics.frame = 60
    frame_based_statistics.input.frame = 100
    assert frame_based_statistics._compute_ratio() == 0.6  # pylint:disable=protected-access


def test_statistics_eta_time(statistics: ffmpeg.EncodeStatistics) -> None:
    statistics.elapsed_time = datetime.timedelta(seconds=60)
    assert statistics.eta_time is None
    statistics.ratio = 0.0
    assert statistics.eta_time is None
    statistics.ratio = 0.2
    assert statistics.eta_time == datetime.timedelta(seconds=240)
    statistics.ratio = 0.5
    assert statistics.eta_time == datetime.timedelta(seconds=60)
    statistics.ratio = 1.0
    assert statistics.eta_time == datetime.timedelta(0)


def test_statistics_parse_chunk(statistics: ffmpeg.EncodeStatistics) -> None:
    assert statistics._parse_chunk('Random stuff') is None  # pylint:disable=protected-access
    assert statistics._parse_chunk(                         # pylint:disable=protected-access
        '   frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s  '), {
            'frame': 2071,
            'frame_rate': 0.0,
            'qscale': -1.0,
            'size': 34623 * 1024,
            'time': datetime.timedelta(minutes=1, seconds=25.89),
            'bit_rate': 3302300
    }


def test_statistics_subclip_duration_and_size(statistics: ffmpeg.EncodeStatistics) -> None:
    subclip = statistics._get_subclip_duration_and_size  # pylint:disable=protected-access
    size = 512 * 1024
    duration = datetime.timedelta(hours=1, minutes=30, seconds=36.5)
    sub_dur_1 = datetime.timedelta(seconds=3610.2)
    sub_dur_2 = datetime.timedelta(hours=1, minutes=20, seconds=15.8)
    sub_dur_3 = datetime.timedelta(minutes=40, seconds=36.3)
    sub_dur_4 = datetime.timedelta(0)
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
    assert statistics.state == statistics.states.NEW
    assert isinstance(statistics.input.duration, datetime.timedelta)
    assert statistics.eta_time is None
    assert statistics.input == statistics.inputs[0]
    assert statistics.output == statistics.outputs[0]
    assert statistics.ratio is None
    assert statistics.input._size is not None  # pylint:disable=protected-access


def test_statistics_started_properties(statistics: ffmpeg.EncodeStatistics) -> None:
    statistics.start('process')
    assert statistics.state == statistics.states.STARTED
    assert statistics.output.duration == datetime.timedelta(0)
    assert statistics.eta_time is None
    assert statistics.ratio == 0.0


def test_statistics_success_properties(statistics: ffmpeg.EncodeStatistics) -> None:
    statistics.start('process')
    statistics.progress('')
    shutil.copy(statistics.input.path, statistics.output.path)  # Generate output
    statistics.end(0)
    assert statistics.state == statistics.states.SUCCESS
    assert statistics.output.duration == statistics.input.duration
    assert statistics.eta_time == datetime.timedelta(0)
    assert statistics.ratio == 1.0
    assert statistics.output._size is None  # pylint:disable=protected-access


def test_ffmpeg_clean_medias_argument() -> None:
    # pylint:disable=use-implicit-booleaness-not-comparison
    clean = ffmpeg.FFmpeg()._clean_medias_argument  # pylint:disable=protected-access
    assert clean(None) == []
    assert clean([]) == []
    assert clean('a.mp4') == [ffmpeg.Media('a.mp4')]
    assert clean(['a.mp4', 'b.mp3']) == [ffmpeg.Media('a.mp4'), ffmpeg.Media('b.mp3')]
    assert clean(ffmpeg.Media('a', '-f mp4')) == [ffmpeg.Media('a', ['-f', 'mp4'])]
    assert clean([ffmpeg.Media('a', ['-f', 'mp4']), ffmpeg.Media('b.mp3')]) == [
        ffmpeg.Media('a', ['-f', 'mp4']),
        ffmpeg.Media('b.mp3')
    ]


def test_ffmpeg_encode(
    static_ffmpeg: type[ffmpeg.FFmpeg],
    small_mp4: Path,
    tmp_path: Path
) -> None:
    encoder = static_ffmpeg()

    results = list(encoder.encode(
        ffmpeg.Media(small_mp4),
        ffmpeg.Media(tmp_path / 'output.mp4', '-c:a copy -c:v copy')))
    assert filesystem.remove(tmp_path / 'output.mp4') is True
    assert results[-1].state == ffmpeg.EncodeState.SUCCESS

    results = list(encoder.encode(
        ffmpeg.Media(small_mp4),
        ffmpeg.Media(tmp_path / 'output.mp4', 'crazy_option')))
    assert filesystem.remove(tmp_path / 'output.mp4') is False
    assert results[-1].state == ffmpeg.EncodeState.FAILURE

    results = list(encoder.encode(
        [ffmpeg.Media('missing.mp4')],
        ffmpeg.Media(tmp_path / 'output.mp4', '-c:a copy -c:v copy')))
    assert filesystem.remove(tmp_path / 'output.mp4') is False
    assert results[-1].state == ffmpeg.EncodeState.FAILURE


def test_ffmpeg_get_arguments() -> None:
    get = ffmpeg.FFmpeg()._get_arguments  # pylint:disable=protected-access
    executable = Path('ffmpeg')

    # Using options (the legacy API, also simplify simple calls)
    in_o_str = '-strict experimental -vf "yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2"'

    args, inputs, outputs, in_options, out_options = get('input.mp4', 'output.mkv', in_o_str)
    assert inputs == [ffmpeg.Media('input.mp4')]
    assert outputs == [ffmpeg.Media('output.mkv')]
    assert in_options == [
        '-strict', 'experimental',
        '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'
    ]
    assert args == [executable, '-y', *in_options, '-i', 'input.mp4', *out_options, 'output.mkv']

    args, _, outputs, in_options, out_options = get('input.mp4', None, in_o_str)
    assert args == [executable, '-y', *in_options, '-i', 'input.mp4']
    assert outputs == []

    # Using instances of Media (the newest API, greater flexibility)
    args, inputs, outputs, in_options, out_options = get(
        ffmpeg.Media('in', '-f mp4'),
        ffmpeg.Media('out.mkv', '-acodec copy -vcodec copy'))
    assert inputs == [ffmpeg.Media('in', ['-f', 'mp4'])]
    assert outputs == [ffmpeg.Media('out.mkv', ['-acodec', 'copy', '-vcodec', 'copy'])]
    assert in_options == []
    assert out_options == []
    assert args == [
        executable, '-y', '-f', 'mp4', '-i', 'in', '-acodec', 'copy', '-vcodec', 'copy', 'out.mkv'
    ]


def test_ffmpeg_get_process(static_ffmpeg: type[ffmpeg.FFmpeg]) -> None:
    get = ffmpeg.FFmpeg()._get_process  # pylint:disable=protected-access
    executable = static_ffmpeg.executable
    options = [
        '-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'
    ]
    process = get([executable, '-y', '-i', 'in.mp4', *options, 'out.mkv'])
    process.terminate()
    assert process.args == [str(executable), '-y', '-i', 'in.mp4', *options, 'out.mkv']


def test_ffmpeg_kill_process_handle_missing(
    static_ffmpeg: type[ffmpeg.FFmpeg],
    small_mp4: Path,
    tmp_path: Path
) -> None:

    class SomeError(Exception):
        pass

    class RaiseEncodeStatistics(static_ffmpeg.statistics_class):  # type: ignore[name-defined]
        @staticmethod
        def end(returncode):
            raise SomeError('This is the error.')

    encoder = static_ffmpeg()
    encoder.statistics_class = RaiseEncodeStatistics
    with pytest.raises(SomeError):
        list(encoder.encode(small_mp4, tmp_path / 'out.mp4', out_options='-c:a copy -c:v copy'))
    assert filesystem.remove(tmp_path / 'out.mp4') is True


def test_ffprobe_get_audio_streams(static_ffmpeg: type[ffmpeg.FFmpeg], small_mp4: Path) -> None:
    probe = static_ffmpeg.ffprobe_class()

    probe.stream_classes['audio'] = None
    audio_stream, = probe.get_audio_streams(small_mp4)
    assert isinstance(audio_stream, dict)
    assert audio_stream['avg_frame_rate'] == '0/0'
    assert audio_stream['channels'] == 1
    assert 'codec_time_base' not in audio_stream  # Missing in dump from ffprobe version 6.1

    probe.stream_classes['audio'] = ffmpeg.AudioStream
    audio_stream, = probe.get_audio_streams(small_mp4)
    assert isinstance(audio_stream, ffmpeg.AudioStream)
    assert audio_stream.avg_frame_rate is None
    assert audio_stream.channels == 1
    assert audio_stream.codec.time_base == 1 / 48000


def test_ffprobe_get_media_duration(
    static_ffmpeg: type[ffmpeg.FFmpeg],
    small_mp4: Path,
    tmp_path: Path
) -> None:
    probe = static_ffmpeg.ffprobe_class()

    # Some random bad things
    assert probe.get_media_duration({}) is None

    # Bad file format
    txt_file = tmp_path / 'test.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write('Hey, I am not a MPD nor a média')
    assert probe.get_media_duration(txt_file) is None

    # A MPEG-DASH MPD
    mpd_file = tmp_path / 'test.mpd'
    with open(mpd_file, 'w', encoding='utf-8') as f:
        f.write(MPD_TEST)
    assert probe.get_media_duration(mpd_file).strftime('%H:%M:%S.%f') == '00:06:07.830000'
    assert probe.get_media_duration(mpd_file, as_delta=True) == datetime.timedelta(0, 367, 830000)

    # A MP4
    assert probe.get_media_duration(small_mp4).strftime('%H:%M:%S') == '00:00:05'
    assert probe.get_media_duration(probe.get_media_info(small_mp4)).strftime('%H:%M:%S') == \
        '00:00:05'
    assert probe.get_media_duration(probe.get_media_info(small_mp4), as_delta=True).seconds == 5


def test_ffprobe_get_media_format(static_ffmpeg, small_mp4) -> None:
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
    probe = static_ffmpeg.ffprobe_class()
    probe.executable = Path(str(uuid.uuid4()))
    with pytest.raises(OSError):
        probe.get_media_info('another.mp4', fail=False)


def test_ffprobe_get_video_streams(static_ffmpeg: type[ffmpeg.FFmpeg], small_mp4: Path) -> None:
    probe = static_ffmpeg.ffprobe_class()

    probe.stream_classes['video'] = None
    video_stream, = probe.get_video_streams(small_mp4)
    assert isinstance(video_stream, dict)
    assert video_stream['avg_frame_rate'] == '30/1'

    probe.stream_classes['video'] = ffmpeg.VideoStream
    video_stream, = probe.get_video_streams(small_mp4)
    assert isinstance(video_stream, ffmpeg.VideoStream)
    assert video_stream.avg_frame_rate == 30.0


def test_ffprobe_get_video_frame_rate(static_ffmpeg: type[ffmpeg.FFmpeg], small_mp4: Path) -> None:
    probe = static_ffmpeg.ffprobe_class()
    assert probe.get_video_frame_rate(3.14159265358979323846) is None
    assert probe.get_video_frame_rate({}) is None
    assert probe.get_video_frame_rate(probe.get_media_info(small_mp4)) == 30.0
    assert probe.get_video_frame_rate(small_mp4) == 30.0


def test_ffprobe_get_video_resolution(static_ffmpeg: type[ffmpeg.FFmpeg], small_mp4: Path) -> None:
    probe = static_ffmpeg.ffprobe_class()
    assert probe.get_video_resolution(3.14159265358979323846) is None
    assert probe.get_video_resolution({}) is None
    assert probe.get_video_resolution(probe.get_media_info(small_mp4)) == [560, 320]
    assert probe.get_video_resolution(small_mp4) == [560, 320]
    assert probe.get_video_resolution(small_mp4, index=1) is None
    assert probe.get_video_resolution(small_mp4)[ffmpeg.HEIGHT] == 320
