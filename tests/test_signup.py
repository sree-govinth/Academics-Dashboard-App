import unittest
from app import app

class TestSignup(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.secret_key = 'test_key'
        self.client = app.test_client()

    def test_signup_page_loads(self):
        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign Up', response.data)

    def test_signup_submission_success(self):
        response = self.client.post('/signup', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass',
            'confirm_password': 'testpass',
            'role': 'student'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Signup successful', response.data)

    def test_signup_password_mismatch(self):
        response = self.client.post('/signup', data={
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'pass1',
            'confirm_password': 'pass2',
            'role': 'student'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Passwords do not match', response.data)

if __name__ == '__main__':
    unittest.main()
