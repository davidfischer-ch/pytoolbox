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
    # On Python<2.3.3 os.uname returns a tuple, so we stuck with it
    try:
        with open(f'/boot/config-{release or os.uname()[2]}') as f:
            config = configparser.ConfigParser()
            config_string = f'[kernel]{f.read()}'
            try:
                config.read_string(config_string)
            except AttributeError:
                import io
                config.readfp(io.StringIO(config_string))
    except IOError:
        if fail:
            raise
        return {}
    return {CONFIG_PREFIX.sub('', k): v for k, v in config.items('kernel')}
