import os


class Requirements(object):
    """ Defines a Requirements object that holds in/out paths for generation of requirements files. """

    @property
    def in_files(self):
        """ The files used as source. """
        return [os.path.join(self.in_dir, f) for f in self._in_files]

    @in_files.setter
    def in_files(self, val):
        """ The files used as source. """
        self._in_files = val

    @property
    def out_file(self):
        """ The file used as destination. """
        return os.path.join(self.out_dir, self._out_file)

    @out_file.setter
    def out_file(self, val):
        """ The file used as destination. """
        self._out_file = val

    def __init__(self, **kwargs):
        self.env = kwargs.get('env', '')
        self.out_dir = kwargs.get('out_dir', '')
        self._out_file = kwargs.get('out_file', '')
        self.in_dir = kwargs.get('in_dir', '')
        self._in_files = kwargs.get('in_files', [])

    def get_compile_command(self, in_files=(), out_file=''):
        """ Returns the compiled command for pip-compile. If no files are provided, the instance files will be used.

        :type in_files: Iterable
        :param in_files: a list of paths that represent the input files for the pip-compile command

        :type out_file: str
        :param out_file: a path representing the file that the pip-compile command will use as destination
        """

        return 'pip-compile --output-file {out_file} {in_files}'.format(
            out_file=out_file or self.out_file,
            in_files=' '.join(in_files or self.in_files)
        )

    def get_sync_command(self, reqs_file=''):
        """ Returns the compiled command for pip-sync. If no requirements file is provided, the out_file will be used.

        :type reqs_file: str
        :param reqs_file: the requirements file
        """

        return 'pip-sync {reqs_file}'.format(
            reqs_file=reqs_file or self.out_file
        )

    def check_missing_out_file(self):
        """ Checks if the out file is missing. This should be relevant only after creating it.

        :rtype: bool
        :return: True - file exists
        """

        return self._check_file_exists(self.out_file)

    def get_missing_in_files(self):
        """ Returns a list of all missing input files.

        :rtype: list[str]
        :return: a list of all missing input files
        """
        return [f for f in self.in_files if not self._check_file_exists(f)]

    @staticmethod
    def _check_file_exists(file):
        """ Checks if a path is an existing file.

        :type file: str
        :param file: the path of the file

        :rtype: bool
        :return: True - the file exists
        """

        return os.path.isfile(file)

    @staticmethod
    def _check_dir_exists(directory):
        """ Checks if a path is an existing directory.

        :type directory: str
        :param directory: the path of the directory

        :return: True - the directory exists
        """

        return os.path.isdir(directory)
