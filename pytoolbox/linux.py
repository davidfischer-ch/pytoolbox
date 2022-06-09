import configparser, os, re

__all__ = ['CONFIG_PREFIX', 'DRIVER_IN_KERNEL', 'DRIVER_HAS_MODULE', 'get_kernel_config']

CONFIG_PREFIX = re.compile(r'^config_')
DRIVER_IN_KERNEL = 'y'
DRIVER_HAS_MODULE = 'm'


def get_kernel_config(release=None, fail=True):
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
        with open(f'/boot/config-{release or os.uname().release}', encoding='utf-8') as f:
            config = configparser.ConfigParser()
            config.read_string(f'[kernel]{f.read()}')
    except IOError:
        if fail:
            raise
        return {}
    return {CONFIG_PREFIX.sub('', k): v for k, v in config.items('kernel')}
