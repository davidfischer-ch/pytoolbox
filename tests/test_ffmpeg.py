# pylint:disable=too-few-public-methods
import datetime, shutil, uuid
from pathlib import Path

import pytest
from pytoolbox import filesystem
from pytoolbox.multimedia import ffmpeg

MPD_TEST = """<?xml version="1.0"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT0H6M7.83S">
  <useless text="testing encoding : ça va ou bien ?" />
</MPD>
"""

# This is ffprobe's result on small.mp4 to reverse engineer tests in case we loose it!
SMALL_MP4_MEDIA_INFOS = {
    'format': {
        'bit_rate': '551193',
        'duration': '5.568000',
        'filename': 'small.mp4',
        'format_long_name': 'QuickTime / MOV',
        'format_name': 'mov,mp4,m4a,3gp,3g2,mj2',
        'nb_programs': 0,
        'nb_streams': 2,
        'probe_score': 100,
        'size': '383631',
        'start_time': '0.000000',
        'tags': {
            'compatible_brands': 'mp42isomavc1',
            'creation_time': '2010-03-20 21:29:11',
            'encoder': 'HandBrake 0.9.4 2009112300',
            'major_brand': 'mp42',
            'minor_version': '0'
        }
    },
    'streams': [
        {
            'avg_frame_rate': '30/1',
            'bit_rate': '465641',
            'codec_long_name': 'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10',
            'codec_name': 'h264',
            'codec_tag': '0x31637661',
            'codec_tag_string': 'avc1',
            'codec_time_base': '1/60',
            'codec_type': 'video',
            'display_aspect_ratio': '0:1',
            'disposition': {
                'attached_pic': 0,
                'clean_effects': 0,
                'comment': 0,
                'default': 1,
                'dub': 0,
                'forced': 0,
                'hearing_impaired': 0,
                'karaoke': 0,
                'lyrics': 0,
                'original': 0,
                'visual_impaired': 0
            },
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
            'tags': {
                'creation_time': '2010-03-20 21:29:11',
                'language': 'und'
            },
            'time_base': '1/90000',
            'width': 560
        },
        {
            'avg_frame_rate': '0/0',
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
            'disposition': {
                'attached_pic': 0,
                'clean_effects': 0,
                'comment': 0,
                'default': 1,
                'dub': 0,
                'forced': 0,
                'hearing_impaired': 0,
                'karaoke': 0,
                'lyrics': 0,
                'original': 0,
                'visual_impaired': 0
            },
            'duration': '5.568000',
            'duration_ts': 267264,
            'index': 1,
            'nb_frames': '261',
            'r_frame_rate': '0/0',
            'sample_fmt': 'fltp',
            'sample_rate': '48000',
            'start_pts': 0,
            'start_time': '0.000000',
            'tags': {
                'creation_time': '2010-03-20 21:29:11',
                'language': 'eng'
            },
            'time_base': '1/48000'
        }
    ]
}


def test_to_bit_rate():
    assert ffmpeg.to_bit_rate('231.5kbit/s') == 231500
    assert ffmpeg.to_bit_rate('3302.3kbits/s') == 3302300
    assert ffmpeg.to_bit_rate('1935.9kbits/s') == 1935900
    assert ffmpeg.to_bit_rate('N/A') is None


def test_to_frame_rate():
    assert ffmpeg.to_frame_rate('10.5') == 10.5
    assert ffmpeg.to_frame_rate(25.0) == 25.0
    assert ffmpeg.to_frame_rate('59000/1000') == 59.0
    assert ffmpeg.to_frame_rate('10/0') is None


def test_to_size():
    assert ffmpeg.to_size('231.5kB') == 237056
    assert ffmpeg.to_size('3302.3MB') == 3462712524
    assert ffmpeg.to_size('1935.9KB') == 1982361


def test_media_pipe():
    assert ffmpeg.Media(None).is_pipe is False
    assert ffmpeg.Media('test-file.mp4').is_pipe is False
    assert ffmpeg.Media(Path('other-file.mp4')).is_pipe is False
    for path in '-', 'pipe:3':
        media = ffmpeg.Media(path)
        assert media.directory is None
        assert media.is_pipe is True
        assert media.size == 0


def test_statistics_compute_ratio(statistics):
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


def test_statistics_compute_ratio_frame_based(frame_based_statistics):
    assert frame_based_statistics.input.frame > 0
    frame_based_statistics.input.duration = datetime.timedelta(seconds=60)
    frame_based_statistics.output.duration = datetime.timedelta(seconds=30)
    frame_based_statistics.frame, frame_based_statistics.input.frame = 0, 100
    assert frame_based_statistics._compute_ratio() == 0.0  # pylint:disable=protected-access
    frame_based_statistics.frame = 60
    frame_based_statistics.input.frame = 100
    assert frame_based_statistics._compute_ratio() == 0.6  # pylint:disable=protected-access


def test_statistics_eta_time(statistics):
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


def test_statistics_parse_chunk(statistics):
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


def test_statistics_subclip_duration_and_size(statistics):
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


def test_statistics_new_properties(statistics):
    assert statistics.state == statistics.states.NEW
    assert isinstance(statistics.input.duration, datetime.timedelta)
    assert statistics.eta_time is None
    assert statistics.input == statistics.inputs[0]
    assert statistics.output == statistics.outputs[0]
    assert statistics.ratio is None
    assert statistics.input._size is not None  # pylint:disable=protected-access


def test_statistics_started_properties(statistics):
    statistics.start('process')
    assert statistics.state == statistics.states.STARTED
    assert statistics.output.duration == datetime.timedelta(0)
    assert statistics.eta_time is None
    assert statistics.ratio == 0.0


def test_statistics_success_properties(statistics):
    statistics.start('process')
    statistics.progress('')
    shutil.copy(statistics.input.path, statistics.output.path)  # Generate output
    statistics.end(0)
    assert statistics.state == statistics.states.SUCCESS
    assert statistics.output.duration == statistics.input.duration
    assert statistics.eta_time == datetime.timedelta(0)
    assert statistics.ratio == 1.0
    assert statistics.output._size is None  # pylint:disable=protected-access


def test_ffmpeg_clean_medias_argument():
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


def test_ffmpeg_encode(static_ffmpeg, small_mp4, tmp_path):
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


def test_ffmpeg_get_arguments():
    get = ffmpeg.FFmpeg()._get_arguments  # pylint:disable=protected-access

    # Using options (the legacy API, also simplify simple calls)
    in_o_str = '-strict experimental -vf "yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2"'

    args, inputs, outputs, in_options, out_options = get('input.mp4', 'output.mkv', in_o_str)
    assert inputs == [ffmpeg.Media('input.mp4')]
    assert outputs == [ffmpeg.Media('output.mkv')]
    assert in_options == [
        '-strict', 'experimental',
        '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'
    ]
    assert args == ['ffmpeg', '-y', *in_options, '-i', 'input.mp4', *out_options, 'output.mkv']

    args, _, outputs, in_options, out_options = get('input.mp4', None, in_o_str)
    assert outputs == []
    assert args == ['ffmpeg', '-y', *in_options, '-i', 'input.mp4']

    # Using instances of Media (the newest API, greater flexibility)
    args, inputs, outputs, in_options, out_options = get(
        ffmpeg.Media('in', '-f mp4'),
        ffmpeg.Media('out.mkv', '-acodec copy -vcodec copy'))
    assert inputs == [ffmpeg.Media('in', ['-f', 'mp4'])]
    assert outputs == [ffmpeg.Media('out.mkv', ['-acodec', 'copy', '-vcodec', 'copy'])]
    assert in_options == []
    assert out_options == []
    assert args == [
        'ffmpeg', '-y', '-f', 'mp4', '-i', 'in', '-acodec', 'copy', '-vcodec', 'copy', 'out.mkv'
    ]


def test_ffmpeg_get_process(static_ffmpeg):
    get = ffmpeg.FFmpeg()._get_process  # pylint:disable=protected-access
    executable = static_ffmpeg.executable
    options = [
        '-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'
    ]
    process = get([executable, '-y', '-i', 'in.mp4', *options, 'out.mkv'])
    process.terminate()
    assert process.args == [str(executable), '-y', '-i', 'in.mp4', *options, 'out.mkv']


def test_ffmpeg_kill_process_handle_missing(static_ffmpeg, small_mp4, tmp_path):

    class SomeError(Exception):
        pass

    class RaiseEncodeStatistics(static_ffmpeg.statistics_class):
        @staticmethod
        def end(returncode):
            raise SomeError('This is the error.')

    encoder = static_ffmpeg()
    encoder.statistics_class = RaiseEncodeStatistics
    with pytest.raises(SomeError):
        list(encoder.encode(small_mp4, tmp_path / 'out.mp4', out_options='-c:a copy -c:v copy'))
    assert filesystem.remove(tmp_path / 'out.mp4') is True


def test_ffprobe_get_audio_streams(static_ffmpeg, small_mp4):
    probe = static_ffmpeg.ffprobe_class()

    probe.stream_classes['audio'] = None
    streams = probe.get_audio_streams(small_mp4)
    assert isinstance(streams[0], dict)
    assert streams[0]['avg_frame_rate'] == '0/0'
    assert streams[0]['channels'] == 1
    assert streams[0]['codec_time_base'] == '1/48000'

    probe.stream_classes['audio'] = ffmpeg.AudioStream
    streams = probe.get_audio_streams(small_mp4)
    assert isinstance(streams[0], ffmpeg.AudioStream)
    assert streams[0].avg_frame_rate is None
    assert streams[0].channels == 1
    assert streams[0].codec.time_base == 1 / 48000


def test_ffprobe_get_media_duration(static_ffmpeg, small_mp4, tmp_path):
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


def test_ffprobe_get_media_format(static_ffmpeg, small_mp4):
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


def test_ffprobe_get_media_info_errors_handling(static_ffmpeg):
    probe = static_ffmpeg.ffprobe_class()

    probe.executable = str(uuid.uuid4())
    with pytest.raises(OSError):
        probe.get_media_info('another.mp4', fail=False)


def test_ffprobe_get_video_streams(static_ffmpeg, small_mp4):
    probe = static_ffmpeg.ffprobe_class()

    probe.stream_classes['video'] = None
    streams = probe.get_video_streams(small_mp4)
    assert isinstance(streams[0], dict)
    assert streams[0]['avg_frame_rate'] == '30/1'

    probe.stream_classes['video'] = ffmpeg.VideoStream
    streams = probe.get_video_streams(small_mp4)
    assert isinstance(streams[0], ffmpeg.VideoStream)
    assert streams[0].avg_frame_rate == 30.0


def test_ffprobe_get_video_frame_rate(static_ffmpeg, small_mp4):
    probe = static_ffmpeg.ffprobe_class()
    assert probe.get_video_frame_rate(3.14159265358979323846) is None
    assert probe.get_video_frame_rate({}) is None
    assert probe.get_video_frame_rate(probe.get_media_info(small_mp4)) == 30.0
    assert probe.get_video_frame_rate(small_mp4) == 30.0


def test_ffprobe_get_video_resolution(static_ffmpeg, small_mp4):
    probe = static_ffmpeg.ffprobe_class()
    assert probe.get_video_resolution(3.14159265358979323846) is None
    assert probe.get_video_resolution({}) is None
    assert probe.get_video_resolution(probe.get_media_info(small_mp4)) == [560, 320]
    assert probe.get_video_resolution(small_mp4) == [560, 320]
    assert probe.get_video_resolution(small_mp4, index=1) is None
    assert probe.get_video_resolution(small_mp4)[ffmpeg.HEIGHT] == 320
