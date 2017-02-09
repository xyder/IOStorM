import unittest

from core.db_access_control import QueryBuilder


class ColumnsToDictTestCase(unittest.TestCase):
    def test_happy_flow(self):
        # build test resources
        test_columns = [
            ('test_attr_1', None),  # simulating a Column object from SQLA
            ('test_attr_2', None),
            ('test_attr_3', None),
        ]

        test_object = type('', (object,), {
            'test_attr_1': 'test_val_1',
            'test_attr_2': 'test_val_2',
            'test_attr_3': ''  # empty string to check filtering
        })()

        # run test
        result = QueryBuilder.columns_to_dict(test_object, test_columns)
        self.assertDictEqual(result, {
            'test_attr_1': 'test_val_1',
            'test_attr_2': 'test_val_2'
        })

    def test_with_no_filtering(self):
        # build test resources
        test_columns = [
            ('test_attr_1', None),  # simulating a Column object from SQLA
            ('test_attr_2', None),
            ('test_attr_3', None),
        ]

        test_object = type('', (object,), {
            'test_attr_1': 'test_val_1',
            'test_attr_2': 'test_val_2',
            'test_attr_3': ''
        })()

        # run test
        result = QueryBuilder.columns_to_dict(test_object, test_columns, filtered=False)
        self.assertDictEqual(result, {
            'test_attr_1': 'test_val_1',
            'test_attr_2': 'test_val_2',
            'test_attr_3': '',
        })

    def test_non_existent_column(self):
        # build test resources
        test_columns = [
            ('test_attr_1', None),  # simulating a Column object from SQLA
            ('test_attr_2', None),
            ('test_attr_3', None),
            ('test_attr_4', None),  # non-existent column to test exception
        ]

        test_object = type('', (object,), {
            'test_attr_1': 'test_val_1',
            'test_attr_2': 'test_val_2',
            'test_attr_3': ''
        })()

        # run test
        self.assertRaises(AttributeError, QueryBuilder.columns_to_dict, test_object, test_columns)


class BuildClauseTestCase(unittest.TestCase):
    # TODO: implement test case
    pass


class BuildPkClause(unittest.TestCase):
    # TODO: implement test case
    pass


class ListMapperTestCase(unittest.TestCase):
    # TODO: implement test case
    pass


class GetCompiledCommand(unittest.TestCase):
    # TODO: implement test case
    pass
