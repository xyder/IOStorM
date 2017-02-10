import unittest

from core.db_access_control import QueryBuilder


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
        """ Test most common successfull flow. """

        result = QueryBuilder.columns_to_dict(self.test_object, self.test_columns)
        self.assertDictEqual(result, {
            'test_attr_1': 'test_val_1',
            'test_attr_2': 'test_val_2'
        })

    def test_with_no_filtering(self):
        """ Test successfull flow with filtering disabled. """

        result = QueryBuilder.columns_to_dict(self.test_object, self.test_columns, filtered=False)
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
        self.assertRaises(AttributeError, QueryBuilder.columns_to_dict, self.test_object, test_columns)


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
