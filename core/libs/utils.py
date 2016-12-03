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

    :param str path: the path to be processed
    :param int levels_count: the number of levels to go
    :return: the parent directory path
    :rtype: str
    """

    if not levels_count:
        return path

    return get_parent_directory(os.path.dirname(path), levels_count=levels_count - 1)
