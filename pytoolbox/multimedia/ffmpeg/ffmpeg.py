from __future__ import annotations

from pathlib import Path
from typing import Final
import errno
import itertools
import re
import select
import subprocess
import sys
import time

from pytoolbox import filesystem, subprocess as py_subprocess

from . import encode, ffprobe  # pylint:disable=unused-import

__all__ = ['FRAME_MD5_REGEX', 'FFmpeg']

FRAME_MD5_REGEX: Final[re.Pattern] = re.compile(r'[a-z0-9]{32}', re.MULTILINE)


class FFmpeg(object):
    """
    Encode a set of input files input to a set of output files and yields statistics about the
    encoding.
    """
    executable: Path = Path('ffmpeg')
    ffprobe_class: type[ffprobe.FFprobe] = ffprobe.FFprobe
    statistics_class: type[encode.EncodeStatistics] = encode.EncodeStatistics

    def __init__(
        self,
        executable: Path | None = None,
        *,
        chunk_read_timeout: float = 0.5,
        encode_poll_delay: float = 0.5,
        encoding: str = 'utf-8'
    ) -> None:
        self.executable = executable or self.executable
        self.chunk_read_timeout = chunk_read_timeout
        self.encode_poll_delay = encode_poll_delay
        self.encoding = encoding
        self.ffprobe = self.ffprobe_class()

    def __call__(self, *arguments) -> subprocess.Popen:
        """Call FFmpeg with given arguments (connect stderr to a PIPE)."""
        return py_subprocess.raw_cmd(
            itertools.chain([self.executable], arguments),
            stderr=subprocess.PIPE,
            universal_newlines=True)

    def encode(  # pylint:disable=too-many-locals
        self,
        inputs,
        outputs,
        in_options=None,
        out_options=None,
        create_directories=True,
        process_poll=True,
        process_kwargs=None,
        statistics_kwargs=None
    ):
        """
        Encode a set of input files input to a set of output files and yields statistics about the
        encoding.
        """
        arguments, inputs, outputs, in_options, out_options = \
            self._get_arguments(inputs, outputs, in_options, out_options)

        # Create outputs directories
        if create_directories:
            for output in outputs:
                output.create_directory()

        statistics = self.statistics_class(
            inputs,
            outputs,
            in_options,
            out_options,
            **(statistics_kwargs or {}))

        process = self._get_process(arguments, **(process_kwargs or {}))
        try:
            yield statistics.start(process)
            while True:
                chunk = self._get_chunk(process)
                yield statistics.progress(chunk or '')
                if process_poll:
                    if (returncode := process.poll()) is not None:
                        break
                if self.encode_poll_delay:
                    time.sleep(self.encode_poll_delay)
            yield statistics.end(returncode)
        except Exception as ex:
            traceback = sys.exc_info()[2]
            py_subprocess.kill(process)
            raise ex.with_traceback(traceback) if hasattr(ex, 'with_traceback') else ex

    @staticmethod
    def get_frames_md5_checksum(filename: Path) -> str | None:
        with filesystem.TempStorage() as tmp:
            checksum_filename = tmp.create_tmp_file(return_file=False)
            FFmpeg()('-y', '-i', filename, '-f', 'framemd5', checksum_filename).wait()
            with open(checksum_filename, encoding='utf-8') as f:
                match = FRAME_MD5_REGEX.search(f.read())
            return match.group() if match else None

    def _clean_medias_argument(self, value):
        """
        Return a list of Media instances from passed value.
        Value can be one or multiple instances of string or Media.
        """
        values = [value] if isinstance(value, (str, Path, self.ffprobe.media_class)) else value
        return [self.ffprobe.to_media(v) for v in values] if values else []

    def _get_arguments(self, inputs, outputs, in_options=None, out_options=None):
        """
        Return the arguments for the encoding process.

        * Set inputs to one or multiple strings (paths) or Media instances (with options).
        * Set outputs to one or multiple strings (paths) or Media instances (with options).
        * Set options to a string or a list with the options to put in-between the inputs and
          outputs (legacy API).

        In return you will get a tuple with (arguments, inputs -> list Media, outputs -> list Media,
        options -> list).
        """
        inputs = self._clean_medias_argument(inputs)
        outputs = self._clean_medias_argument(outputs)
        in_options = py_subprocess.to_args_list(in_options)
        out_options = py_subprocess.to_args_list(out_options)
        args = [self.executable, '-y']
        args.extend(in_options)
        for the_input in inputs:
            args.extend(the_input.to_args(is_input=True))
        args.extend(out_options)
        for output in outputs:
            args.extend(output.to_args(is_input=False))
        return args, inputs, outputs, in_options, out_options

    def _get_chunk(self, process):
        select.select([process.stderr], [], [], self.chunk_read_timeout)
        try:
            chunk = process.stderr.read()
            if chunk is None or isinstance(chunk, str):
                return chunk
            return chunk.decode(self.encoding)
        except IOError as ex:
            if ex.errno != errno.EAGAIN:
                raise
        return None

    @staticmethod
    def _get_process(arguments, **process_kwargs):
        """Return an encoding process with stderr made asynchronous."""
        process = py_subprocess.raw_cmd(
            arguments,
            stderr=subprocess.PIPE,
            close_fds=True,
            **process_kwargs)
        py_subprocess.make_async(process.stderr)
        return process
