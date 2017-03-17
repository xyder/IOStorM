import inspect
import os


def to_string_hex(data):
    """
    Returns binary data as readable string hex codes.
    :param bytes data: the data to be returned
    :return: a string with the hex codes of the bytes in the input data.
    """

    return ' '.join('{:02x}'.format(x) for x in data)


def get_parent_directory(path, levels_count=1):
    """ Retrieves the directory path up to `levels_count` levels up.
    Examples:
        >>> get_parent_directory('/test/dir/level1/level2/level3', levels_count=3)
        '/test/dir'
        >>> get_parent_directory('/l1/l2/l3', levels_count=5)
        '/'
        >>> get_parent_directory('/l1/l2/l3')
        '/l1/l2'

    :param str path: the path to be processed
    :param int levels_count: the number of levels to go
    :return: the parent directory path
    :rtype: str
    """

    if not levels_count:
        return path

    return get_parent_directory(os.path.dirname(path), levels_count=levels_count - 1)


def get_func_args():
    """ Returns a dictonary with the arguments passed to the calling function.

    :rtype dict
    :return: a dictionary with arguments
    """

    # get calling function frame
    calling_frame = inspect.stack()[1][0]

    try:
        args = inspect.getargvalues(calling_frame)
    finally:
        # explicit cleanup to make sure reference cycles are broken
        del calling_frame

    keys = getattr(args, 'args', [])
    values_dict = getattr(args, 'locals', {})

    # build dictionary with the calling function args and values
    return {k: values_dict[k] for k in keys}
