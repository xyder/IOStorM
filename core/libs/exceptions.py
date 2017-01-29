import logging


class IncorrectResultSizeException(Exception):
    """ Raised to signal an incorrect number of items in a result set. """

    def __init__(self, *args):
        super(IncorrectResultSizeException, self).__init__(*args)

        if len(args) != 1:
            return

        try:
            count = int(args[0])
        except ValueError:
            return

        self.args = ('Result set does not contain exactly {} result(s).'.format(count),)


class CertificateNotGeneratedException(Exception):
    """ Raised to signal a certificate was not previously generated. """

    def __init__(self, *args):
        super(CertificateNotGeneratedException, self).__init__(*args)

        if len(args) != 1:
            return

        self.args = ('{} certificate is not generated.'.format(args[0]),)


class MissingArgsException(Exception):
    """ Raised when a function arguments are missing or not specified. """

    def __init__(self, *args):
        super(MissingArgsException, self).__init__(*args)

        if len(args) != 1:
            return

        self.args = ('Missing function arguments: {}'.format(args[0]),)
