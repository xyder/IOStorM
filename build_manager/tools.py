import subprocess


def run_command(command):
    """ Runs a command with subprocess.run

    :type command: list|str
    :param command: the command that will be executed

    :rtype: CompletedProcess
    """

    return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
