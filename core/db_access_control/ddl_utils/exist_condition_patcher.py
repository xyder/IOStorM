"""
Module that provides functions to patch the existing DDL Elements by adding conditions that
take into account the pre-existence of elements in the databased.

-- based on gist https://gist.github.com/eirnym/afe8afb772a79407300a
-- by Arseny Nasokin
"""

import re
from copy import copy
from enum import Enum

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import CreateTable, DropTable, CreateIndex, DropIndex
from sqlalchemy.sql.ddl import CreateSchema, DropSchema


# these will be the DDL statements to be patched by default
ELEMENTS_TO_PATCH = {
    CreateTable,
    CreateIndex,
    CreateSchema,
    DropTable,
    DropIndex,
    DropSchema
}


class ConditionVariants(Enum):
    if_not_exists = 'IF NOT EXISTS'
    if_exists = 'IF EXISTS'


class ExistConditionPatcher(object):
    @staticmethod
    def set_build_condition(self, value=True):
        """ Sets the build condition to True which will enable the patcher to augment
        the DDL statement.

        :param self: the DDL statement instance

        :type value: bool
        :param value: if True, on compilation the patcher will augment the output

        :return: a DDL statement with the build condition set to true. This is a
        shallow copy that will enable chained calls such as:
            connection.execute(CreateTable(table).if_not_exists())
        """

        augmented_self = copy(self)
        augmented_self._build_condition = value
        return augmented_self

    def append_condition_setter(self):
        """ Appends a setter for the build condition boolean to the element. """

        setattr(self.element, 'check_first', self.set_build_condition)

    def inject_condition(self, command):
        """ Injects the condition in the given command.

        :type command: str
        :param command: the command to be augmented

        :rtype: str
        :return: the modified command
        """

        return re.sub(self.regex, self.condition, command, re.S)

    @staticmethod
    def split_camel_case(input_text):
        """ Splits a string by the capital letters in it. Ex:
            'CamelCaseString' --> ['Camel', 'Case', 'String']

        :type input_text: str
        :param input_text: the text to be processed

        :rtype: list[str]
        :return: the result of the split
        """

        return re.findall('[A-Z][a-z]*', input_text)

    def __init__(self, element, variant=None, method='', regex='', replacement=''):
        """ Creates a patcher to augment DDL statements.

        :param element: the DDL element to be augmented.

        :type variant: ConditionVariants
        :param variant: the type of injection to be made.

        :type method: str
        :param method: the compiler method

        :type regex: str
        :param regex: search string to identify the substring to be replaced

        :type replacement: str
        :param replacement: replacement string to be injected
        """

        self.element = element
        element_name = getattr(element, '__name__', '')

        if not element_name and (not method or not regex or not replacement):
            raise Exception('Operation type could not be determined.')

        if variant:
            self.variant = variant
        elif 'Drop' in element_name:
            self.variant = ConditionVariants.if_exists
        elif 'Create' in element_name:
            self.variant = ConditionVariants.if_not_exists

        if not self.variant:
            raise Exception('Variant could not be determined')

        name_parts = self.split_camel_case(element_name)
        self.method = method or 'visit_{}'.format('_'.join(name_parts).lower())
        self.regex = regex or '{}'.format(' '.join(name_parts).upper())
        self.condition = replacement or '{} {}'.format(' '.join(name_parts).upper(), self.variant.value)

        self.append_condition_setter()


def create_patch(patcher, if_always=False):
    """ Patches and compiles the statement using the specified patcher.

    :type patcher: ExistConditionPatcher
    :param patcher: a patcher used to patch and compile the statement.

    :type if_always: bool
    :param if_always: if True, the patch will always be in effect.

    :rtype: collections.abc.Callable
    :return: a function that compiles over the statement.
    """

    @compiles(patcher.element)
    def _if_exists_(element, compiler, **kw):

        # get the original compiled statement
        output = getattr(compiler, patcher.method)(element, **kw)

        if if_always or getattr(element, '_build_condition', False):
            # patch the statement
            output = patcher.inject_condition(output)

        return output

    return _if_exists_


def enable_patches(statements=ELEMENTS_TO_PATCH, if_always=False):
    """ Function that patches the default set of statements or a given set of statements.

    :type statements: set
    :param statements: the statements that will be patched

    :type if_always: bool
    :param if_always: if True, the condition will always be set to true.
    """

    for statement in statements:
        create_patch(ExistConditionPatcher(statement), if_always=if_always)
