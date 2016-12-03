import unittest

from core.db_access_control.sql_query_builder import SQLQueryBuilder


class TestSQLQueryBuilder(unittest.TestCase):
    def test_delete_element(self):
        """ Tests the construction of a delete SQL query. """
        test_params = {
            'schema_name': 'test_schema',
            'table_name': 'test_table',
            'cond_dict': {
                'id': '1234',
                'title': 'a test title'
            }
        }

        result = SQLQueryBuilder.delete_element(**test_params)

        self.assertEqual(result, (
            'DELETE FROM test_schema.test_table WHERE id = %(id)s AND title = %(title)s;',
            test_params['cond_dict']
        ))

    def test_delete_element_by_id(self):
        """ Tests the construction of a delete SQL query filtered by id. """
        test_params = {
            'schema_name': 'test_schema',
            'table_name': 'test_table',
            'id_value': '1234'
        }

        result = SQLQueryBuilder.delete_element_by_id(**test_params)

        self.assertEqual(result, (
            'DELETE FROM test_schema.test_table WHERE id = %(id)s;',
            {'id': '1234'}
        ))

    def test_get_element(self):
        """ Tests the construction of an element select SQL query. """
        test_params = {
            'schema_name': 'test_schema',
            'table_name': 'test_table',
            'cond_dict': {
                'id': '1234',
                'title': 'a test title'
            }
        }

        result = SQLQueryBuilder.get_element(**test_params)

        self.assertEqual(result, (
            'SELECT * FROM test_schema.test_table WHERE id = %(id)s AND title = %(title)s;',
            test_params['cond_dict']
        ))

    def test_get_element_by_id(self):
        """ Tests the construction of an element select SQL query filtered by id. """
        test_params = {
            'schema_name': 'test_schema',
            'table_name': 'test_table',
            'id_value': '1234'
        }

        result = SQLQueryBuilder.get_element_by_id(**test_params)

        self.assertEqual(result, (
            'SELECT * FROM test_schema.test_table WHERE id = %(id)s;',
            {'id': '1234'}
        ))
