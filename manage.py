"""
Module that defines and performs frequently used build actions.
"""

import os

import click

from build_manager import Requirements
from build_manager.tools import run_command


# CONSTANTS
REQS_DIR = 'requirements'
REQS_IN_DIR = os.path.join(REQS_DIR, 'in_files')
REQS_OUT_DIR = os.path.join(REQS_DIR, 'out_files')
REQS = {
    'live': Requirements(
        env='live',
        in_dir=REQS_IN_DIR,
        in_files=['requirements.live.in'],
        out_dir=REQS_OUT_DIR,
        out_file='requirements.live.txt'
    ),
    'dev': Requirements(
        env='dev',
        in_dir=REQS_IN_DIR,
        in_files=['requirements.dev.in', 'requirements.live.in'],
        out_dir=REQS_OUT_DIR,
        out_file='requirements.dev.txt'
    )
}


def build_requirements(key):
    """ Builds a requirements file using the given key.

    :type key: str
    :param key: the key corresponding to the requirements file info in the REQS dict.

    :rtype: bool
    :return: True - the command was executed succesfully
    """

    reqs_obj = REQS[key]
    # check that all files exist
    missing_files = reqs_obj.get_missing_in_files()
    for file in missing_files:
        click.echo(f'Error: File "{file}" does not exist.', err=True)

    if missing_files:
        return False

    # execute the command
    result = run_command(reqs_obj.get_compile_command())

    # check for successful execution
    if result.returncode != 0:
        click.echo(f'Error: {result.stderr}', err=True)
        return False

    click.echo(f'Build requirements for "{key}" environment.')
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

    reqs_obj = REQS[key]

    # check that out file exists
    if not reqs_obj.check_missing_out_file():
        click.echo(f'Error: File "{reqs_obj.out_file}" does not exist.', err=True)
        return False

    # execute the command
    result = run_command(reqs_obj.get_sync_command())

    # check for successful execution
    if result.returncode != 0:
        click.echo(f'Error: {result.stderr}', err=True)
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
@click.option('--all', 'env', flag_value='all', default=True)
@click.option('--sync', 'sync_action', is_flag=True, default=False)
@click.option('--build', 'build_action', is_flag=True, default=False)
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
