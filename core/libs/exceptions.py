

class DBAccessException(Exception):
    """ Generic DB Access Exception """
    pass


class IncorrectResultCount(DBAccessException):
    """ Raised to signal an incorrect number of items in a result set. """

    def __init__(self, *args):
        self.args = args
        if len(args) != 1:
            return

        try:
            count = int(args[0])
        except ValueError:
            return

        self.args = ('Result set does not contain exactly {} result(s).'.format(count),)
