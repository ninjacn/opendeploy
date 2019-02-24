import unittest
from django.test import TestCase, Client

# Create your tests here.


class HttpCheckTest(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_details(self):
        response = self.client.post('/accounts/login/', {'username': 'admin', 'password': 'opendeploy'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')
