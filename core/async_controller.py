from tornado import concurrent
from tornado import gen
from tornado.ioloop import IOLoop

from core.libs.exceptions import MissingArgsException


def run_async(func, *args, **kwargs):
    """ Return the future of a sync function.

    :type func: collections.abc.Callable
    :param func: the function to be called

    :type args: list
    :param args: the args used in the function call

    :type kwargs: dict
    :param kwargs: the kwargs used in the function call
    """

    return gen.Task(func=lambda callback: callback(func(*args, **kwargs)))


def run_sync(func=None, future=None, *args, **kwargs):
    """ Return the results from an async function or a future, synchronously.

    :type func: collections.abc.Callable
    :param func: the function to be called

    :type future: concurrent.Future
    :param future: a future which, if specified, will be used instead of `func`
        and all other arguments will be ignored

    :type args: list
    :param args: the arguments to be passed to the function

    :type kwargs: dict
    :param kwargs: the keyword arguments to be passed to the function

    :return: the result of the function call
    """

    if not func and not future:
        raise MissingArgsException('Callable or Future')

    ioloop = IOLoop.instance()
    future = future or func(*args, **kwargs)  # type: concurrent.Future
    ioloop.add_future(future, lambda _: ioloop.stop())
    ioloop.start()

    return future.result()
