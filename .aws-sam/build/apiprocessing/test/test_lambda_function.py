import unittest
from lambda_function import lambda_handler

class TestLambdaFunction(unittest.TestCase):

    def test_status_check(self):
        event = {
            'httpMethod': 'GET',
            'path': '/status'
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], '"Service is operational"')

    def test_get_all_products(self):
        event = {
            'httpMethod': 'GET',
            'path': '/products'
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)

if __name__ == '__main__':
    unittest.main()
