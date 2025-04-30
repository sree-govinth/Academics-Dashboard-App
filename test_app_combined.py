import unittest
from app import app

class TestLogin(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_login_page_loads(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

class TestDashboards(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def login_as(self, role):
        with self.client.session_transaction() as sess:
            sess['user'] = {'username': 'testuser', 'role': role}

    def test_student_dashboard_access(self):
        self.login_as('student')
        response = self.client.get('/student_dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Student Dashboard', response.data)

    def test_admin_dashboard_access(self):
        self.login_as('admin')
        response = self.client.get('/admin_dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin Dashboard', response.data)

    def test_faculty_dashboard_access(self):
        self.login_as('faculty')
        response = self.client.get('/faculty_dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Faculty Dashboard', response.data)

    def test_staff_dashboard_access(self):
        self.login_as('staff')
        response = self.client.get('/staff_dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Staff Dashboard', response.data)

class TestChatbot(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def login_as_user(self):
        with self.client.session_transaction() as sess:
            sess['user'] = {'username': 'anyuser', 'role': 'student'}

    def test_chatbot_access_logged_in(self):
        self.login_as_user()
        response = self.client.get('/chatbot')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Chatbot', response.data)

    def test_chatbot_access_guest(self):
        response = self.client.get('/chatbot', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

if __name__ == '__main__':
    unittest.main()
