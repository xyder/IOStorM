from psycopg2 import ProgrammingError
from tornado import gen


class IncorrectResultSizeException(Exception):
    """ Raised to signal an incorrect number of items in a result set. """

    def __init__(self, received, expected):
        """
        :type received: int
        :param received: the actual size of the result

        :type expected: int
        :param expected: the expected size of the result
        """

        self.args = (
            'Result set does not contain exactly {} result(s). Received {} items.'.format(
                expected, received),
        )
        super(IncorrectResultSizeException, self).__init__(*self.args)


class PartialPrimaryKeyException(Exception):
    """ Raised when some of the primary keys from a multi-field primary key were not provided. """

    def __init__(self, missing_keys):
        self.args = ('Missing primary key fields: {}'.format(', '.join(missing_keys)),)

        super(PartialPrimaryKeyException, self).__init__(*self.args)


class SaveEntityFailedException(Exception):
    """ Called when the creation of an entity failed. """

    def __init__(self, reason):
        self.args = ('Entity creation failed. Reason: {}'.format(reason),)

        super(SaveEntityFailedException, self).__init__(*self.args)


@gen.coroutine
def exception_wrapper(
        function, exception_type=ProgrammingError, message_validator=lambda s: False, **kwargs):
    """ Wraps a function execution and consumes an exception which matches the type
    and the condition specified.

    :param function: the function to call

    :param exception_type: the type of the exception to be consumed

    :type message_validator: collections.abc.Callable
    :param message_validator: the condition for the exception message for which the exception
        is ignored

    :type kwargs: dict
    :param kwargs: keyword arguments that will be passed to the function

    :rtype: list
    :return: the result of the command execution
    """

    result = []
    try:
        result = yield function(**kwargs)
    except exception_type as e:
        s = str(e.args[0]).strip()

        if not message_validator(s):
            raise

    return result
