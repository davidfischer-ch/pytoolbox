from __future__ import annotations

from pathlib import Path
from typing import Final
import configparser
import os
import re

__all__ = ['CONFIG_PREFIX', 'DRIVER_IN_KERNEL', 'DRIVER_HAS_MODULE', 'get_kernel_config']

CONFIG_PREFIX: Final[re.Pattern] = re.compile(r'^config_')
DRIVER_IN_KERNEL: Final[str] = 'y'
DRIVER_HAS_MODULE: Final[str] = 'm'


def get_kernel_config(release: str | None = None, *, fail: bool = True) -> dict[str, str]:
    """
    Return a JSON string with the GNU/Linux Kernel configuration.

    **Example usage**

    >>> config = get_kernel_config(fail=False)
    >>> type(config)
    <class 'dict'>
    >>> not config or 'memory' in config
    True

    Error handling:

    >>> get_kernel_config('0.0.1-generic', fail=False)
    {}
    """
    try:
        content = Path(f'/boot/config-{release or os.uname().release}').read_text(encoding='utf-8')
        config = configparser.ConfigParser()
        config.read_string(f'[kernel]{content}')
    except IOError:
        if fail:
            raise
        return {}
    return {CONFIG_PREFIX.sub('', k): v for k, v in config.items('kernel')}
