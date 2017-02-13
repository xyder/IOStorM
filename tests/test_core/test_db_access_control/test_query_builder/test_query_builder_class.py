import unittest

import sqlalchemy
import sqlalchemy.dialects
import sqlalchemy.sql.elements

import core.db_access_control.query_builder as qb


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
        test_columns = self.test_columns.copy()
        test_columns.append(('test_attr_4', None))

        # run test
        self.assertRaises(AttributeError, qb.QueryBuilder.columns_to_dict, self.test_object, test_columns)


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

        # compile results
        compiled_result = result.compile(
            dialect=sqlalchemy.dialects.postgresql.dialect(),
            compile_kwargs={'literal_binds': True}
        )

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

        # compile results
        compiled_result = result.compile(
            dialect=sqlalchemy.dialects.postgresql.dialect(),
            compile_kwargs={'literal_binds': True}
        )

        self.assertEqual(type(result), sqlalchemy.sql.elements.BooleanClauseList)
        self.assertEqual(
            str(compiled_result),
            "column_1 = 3 OR column_2 = 'test_string' OR column_3 IS NULL"
        )


class BuildPkClause(unittest.TestCase):
    # TODO: implement test case
    pass


class ListMapperTestCase(unittest.TestCase):
    # TODO: implement test case
    pass


class GetCompiledCommand(unittest.TestCase):
    # TODO: implement test case
    pass
