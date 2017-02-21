import unittest

import mock
import sqlalchemy
import sqlalchemy.dialects
import sqlalchemy.sql.elements

import core.db_access_control.db_exceptions as db_exceptions
import core.db_access_control.ddl_utils.query_builder as qb


class ColumnsToDictTestCase(unittest.TestCase):

    def setUp(self):
        self.test_columns = [
            ('test_attr_1', None),  # simulating a Column object from SQLA
            ('test_attr_2', None),
            ('test_attr_3', None),
        ]

        self.test_object = type('', (object,), {
            'test_attr_1': 'test_val_1',
            'test_attr_2': 'test_val_2',
            'test_attr_3': ''  # empty string to check filtering
        })()

    def test_happy_flow(self):
        """ Test most common successful flow. """

        result = qb.QueryBuilder.columns_to_dict(self.test_object, self.test_columns)
        self.assertDictEqual(result, {
            'test_attr_1': 'test_val_1',
            'test_attr_2': 'test_val_2'
        })

    def test_with_no_filtering(self):
        """ Test successful flow with filtering disabled. """

        result = qb.QueryBuilder.columns_to_dict(self.test_object, self.test_columns, filtered=False)
        self.assertDictEqual(result, {
            'test_attr_1': 'test_val_1',
            'test_attr_2': 'test_val_2',
            'test_attr_3': '',
        })

    def test_non_existent_column(self):
        """ Test exception when a non-existent column is requested. """

        # customize test resources
        self.test_columns.append(('test_attr_4', None))

        # run test
        self.assertRaises(AttributeError, qb.QueryBuilder.columns_to_dict, self.test_object, self.test_columns)


class BuildClauseTestCase(unittest.TestCase):
    def test_happy_flow(self):
        """ Test successful flow. """

        # build test resources
        test_comparator = sqlalchemy.and_
        test_column_1 = sqlalchemy.Column('column_1')
        test_column_2 = sqlalchemy.Column('column_2')

        # run test
        result = qb.QueryBuilder.build_clause(
            comparator=test_comparator,
            columns=[test_column_1, test_column_2],
            column_1=3,
            column_2='test_string'
        )
        compiled_result = qb.QueryBuilder.get_compiled_command(result)

        self.assertEqual(type(result), sqlalchemy.sql.elements.BooleanClauseList)
        self.assertEqual(str(compiled_result), "column_1 = 3 AND column_2 = 'test_string'")

    def test_happy_flow_2(self):
        """ Test succesful flow. """

        # build test resources
        test_comparator = sqlalchemy.or_
        test_column_1 = sqlalchemy.Column('column_1')
        test_column_2 = sqlalchemy.Column('column_2')
        test_column_3 = sqlalchemy.Column('column_3')

        # run test
        result = qb.QueryBuilder.build_clause(
            comparator=test_comparator,
            columns=[test_column_1, test_column_2, test_column_3],
            column_1=3,
            column_2='test_string',
            column_3=None
        )
        compiled_result = qb.QueryBuilder.get_compiled_command(result)

        self.assertEqual(type(result), sqlalchemy.sql.elements.BooleanClauseList)
        self.assertEqual(
            str(compiled_result),
            "column_1 = 3 OR column_2 = 'test_string' OR column_3 IS NULL"
        )


class BuildPkClause(unittest.TestCase):
    def test_happy_flow(self):
        """ Test succesful flow. """

        table = mock.MagicMock()  # type: sqlalchemy.Table
        table.primary_key.columns = [
            sqlalchemy.Column('pk_part_1'),
            sqlalchemy.Column('pk_part_2'),
            sqlalchemy.Column('pk_part_3')
        ]

        result = qb.QueryBuilder.build_pk_clause(
            table,
            pk_part_1=11,
            pk_part_2=12,
            pk_part_3='13'
        )
        compiled_result = qb.QueryBuilder.get_compiled_command(result)

        self.assertEqual(type(result), sqlalchemy.sql.elements.BooleanClauseList)
        self.assertEqual(
            str(compiled_result),
            "pk_part_1 = 11 AND pk_part_2 = 12 AND pk_part_3 = '13'"
        )

    def test_partial_key_provided(self):
        """ Test if exception is raised when some pks are not received. """

        table = mock.MagicMock()  # type: sqlalchemy.Table
        table.primary_key.columns = [
            sqlalchemy.Column('pk_part_1'),
            sqlalchemy.Column('pk_part_2'),
            sqlalchemy.Column('pk_part_3'),
            sqlalchemy.Column('pk_part_4')
        ]

        with self.assertRaises(db_exceptions.PartialPrimaryKeyException):
            qb.QueryBuilder.build_pk_clause(
                table,
                pk_part_1=11,
                pk_part_3='13'
            )


class ListMapperTestCase(unittest.TestCase):
    # TODO: implement test case
    pass


class GetCompiledCommand(unittest.TestCase):
    # TODO: implement test case
    pass
