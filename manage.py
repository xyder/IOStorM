"""
Module that defines and performs frequently used build actions.
"""

import os

import click
import subprocess


# TODO: add setup.py and entry points
# TODO: add click-shell support

# CONSTANTS
REQS_DIR = 'requirements'
REQS_IN_DIR = os.path.join(REQS_DIR, 'in_files')
REQS_OUT_DIR = os.path.join(REQS_DIR, 'out_files')


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
        self.out_dir = kwargs.get('out_dir', REQS_OUT_DIR)
        self._out_file = kwargs.get('out_file', '')
        self.in_dir = kwargs.get('in_dir', REQS_IN_DIR)
        self._in_files = kwargs.get('in_files', [])

    def get_compile_command(self):
        """ Returns the compiled command for pip-compile. """

        raise NotImplementedError

    def get_sync_command(self):
        """ Returns the compiled command for pip-sync. """

        raise NotImplementedError


# CONSTANTS
REQS = {
    'live': Requirements(
        env='live',
        in_files=['requirements.live.in'],
        out_file='requirements.live.txt'
    ),
    'dev': Requirements(
        env='dev',
        in_files=['requirements.dev.in', 'requirements.live.in'],
        out_file='requirements.dev.txt'
    )
}


def run_command(command):
    """ Runs a command with subprocess.run

    :type command: list|str
    :param command: the command that will be executed

    :rtype: CompletedProcess
    """

    return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)


def build_requirements(key):
    """ Builds a requirements file using the given key.

    :type key: str
    :param key: the key corresponding to the requirements file info in the REQS dict.

    :rtype: bool
    :return: True - the command was executed succesfully
    """

    command = 'pip-compile --output-file {out_file} {in_files}'

    # check that all files exist
    for f in REQS[key].in_files:
        if not os.path.isfile(f):
            click.echo('Error: File "{}" does not exist.'.format(f), err=True)
            return False

    # execute the command
    result = run_command(command.format(
        out_file=REQS[key].out_file,
        in_files=' '.join(REQS[key].in_files)))

    # check for successful execution
    if result.returncode != 0:
        click.echo('Error: {}'.format(result.stderr), err=True)
        return False

    return True


def sync_venv(key, print_output=True):
    """ Syncs the python virtual env using the given requirements file key.

    :type key: str
    :param key: the key corresponding to a requirements object in REQS dict

    :type print_output: bool
    :param print_output: if True it will print the output through click.echo

    :rtype: bool
    :return: True - command was executed succesfully
    """

    command = 'pip-sync {reqs_file}'

    f = REQS[key].out_file

    # check that out file exists
    if not os.path.isfile(f):
        click.echo('Error: File "{}" does not exist.'.format(f), err=True)
        return False

    # execute the command
    result = run_command(command.format(reqs_file=f))

    # check for successful execution
    if result.returncode != 0:
        click.echo('Error: {}'.format(result.stderr), err=True)
        return False

    # print the output if needed
    if print_output:
        click.echo(result.stdout)

    return True


@click.group()
def cli():
    """ Defines a group of click commands. """
    pass


@cli.command()
@click.option('--dev', 'env', flag_value='dev')
@click.option('--live', 'env', flag_value='live')
@click.option('--all', 'env', flag_value='all')
@click.option('--sync', 'sync_action', is_flag=True)
@click.option('--build', 'build_action', default=False)
def reqs(sync_action=False, build_action=False, env='all'):
    """ Command for managing requirements files.

    :type sync_action: bool
    :param sync_action: if True, it will perform a pip-sync call

    :type build_action: bool
    :param build_action: if True, it will perform a pip-compile call

    :type env: str
    :param env: Possible values: `dev`, `live`
    """

    env = env or 'all'

    if not build_action and not sync_action:
        build_action = True

    if env == 'all':
        if build_action:
            build_requirements('live')
            build_requirements('dev')
        if sync_action:
            click.echo('Error: An environment must be specified to run sync.', err=True)
    else:
        if build_action:
            build_requirements(env)
        if sync_action:
            sync_venv(env)


if __name__ == '__main__':
    cli()
