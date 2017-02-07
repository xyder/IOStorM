
class CertificateNotGeneratedException(Exception):
    """ Raised to signal a certificate was not previously generated. """

    def __init__(self, certificate_name):
        self.args = ('{} certificate is not generated.'.format(certificate_name),)
        super(CertificateNotGeneratedException, self).__init__(*self.args)


class MissingArgsException(Exception):
    """ Raised when a function arguments are missing or not specified. """

    def __init__(self, *args):
        super(MissingArgsException, self).__init__(*args)

        if len(args) != 1:
            return

        self.args = ('Missing function arguments: {}'.format(args[0]),)
