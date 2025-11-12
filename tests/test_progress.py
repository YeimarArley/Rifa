import unittest
from server import app


class ProgressTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_progress_endpoint(self):
        resp = self.client.get('/progress')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('assigned', data)
        self.assertIn('total', data)
        self.assertIn('percentage', data)

    def test_simulate_purchase(self):
        # Simula una compra admin
        resp = self.client.post('/admin/simulate_purchase', data={
            'key': 'CLAVEADMIN',
            'amount': 4,
            'email': 'test@demo.com'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertTrue('invoice_id' in data)
        self.assertTrue('numbers' in data)


if __name__ == '__main__':
    unittest.main()
import unittest
from server import app

class ProgressTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_progress_endpoint(self):
        resp = self.client.get('/progress')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('assigned', data)
        self.assertIn('total', data)
        self.assertIn('percentage', data)

    def test_simulate_purchase(self):
        # Simula una compra admin
        resp = self.client.post('/admin/simulate_purchase', data={
            'key': 'CLAVEADMIN',
            'amount': 4,
            'email': 'test@demo.com'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertTrue('invoice_id' in data)
        self.assertTrue('numbers' in data)

if __name__ == '__main__':
    unittest.main()
