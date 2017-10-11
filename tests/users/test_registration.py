# project/tests/test_auth.py

import unittest
import json
import time
from src.models import User
from tests.base import BaseTestCase
from app import application, TOKEN_DURATION

class TestRegistration(BaseTestCase):
    def test_registration(self):
        """ Test for user registration """
        with self.client:
            response = self.client.post(
                '/users',
                data=json.dumps(dict(
                    email='joe@gmail.com',
                    password='123456'
                )),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['status'] == 'success')
            self.assertTrue(data['message'] == 'user_registered')
            self.assertTrue(data['auth_token'])
            self.assertTrue(response.content_type == 'application/json')
            self.assertEqual(response.status_code, 201)


    def test_registered_with_already_registered_user(self):
        """ Test registration with already registered email"""
        with self.client:
            response = self.client.post(
                '/users',
                data=json.dumps(dict(
                    email='joe@gmail.com',
                    password='123456'
                )),
                content_type='application/json'
            )
            response = self.client.post(
                '/users',
                data=json.dumps(dict(
                    email='joe@gmail.com',
                    password='123456'
                )),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['status'] == 'fail')
            self.assertTrue(
                data['message'] == 'user_email_already_exists')
            self.assertTrue(response.content_type == 'application/json')
            self.assertEqual(response.status_code, 409)

    def test_register_with_missing_email(self):
        """ Test registration without an email"""
        
        with self.client:
            
            response = self.client.post(
                '/users',
                data=json.dumps(dict(
                    emal='joe@gmail.com',
                    password='123456'
                )),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['status'] == 'fail')
            self.assertTrue(
                data['message'] == 'invalid_email')
            self.assertTrue(response.content_type == 'application/json')
            self.assertEqual(response.status_code, 400)
    
    def test_register_with_missing_password(self):
        """ Test registration without password"""
        
        with self.client:
            
            response = self.client.post(
                '/users',
                data=json.dumps(dict(
                    email='joe@gmail.com',
                    pssword='123456'
                )),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['status'] == 'fail')
            self.assertTrue(
                data['message'] == 'missing_password')
            self.assertTrue(response.content_type == 'application/json')
            self.assertEqual(response.status_code, 400)




class TestDelete(BaseTestCase):
    def test_delete_user_correctly(self):
        """ Test for user delete, correct case """
        with self.client:
            response = self.client.post(
                '/users',
                data=json.dumps(dict(
                    email='joe@gmail.com',
                    password='123456'
                )),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['status'] == 'success')
            self.assertTrue(data['message'] == 'user_registered')
            self.assertTrue(data['auth_token'])
            self.assertTrue(response.content_type == 'application/json')
            self.assertEqual(response.status_code, 201)
            response = self.client.delete(
                '/users',
                headers=dict(
                    Authorization='Bearer ' + data['auth_token']
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['status'] == 'success')
            self.assertTrue(data['message'] == 'user_deleted')
            self.assertTrue(response.content_type == 'application/json')
            self.assertEqual(response.status_code, 200)

    def test_delete_without_token(self):
        """ Test for trying to delete user without loging in """
        with self.client:
            response = self.client.post(
                '/users',
                data=json.dumps(dict(
                    email='joe@gmail.com',
                    password='123456'
                )),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            response = self.client.delete(
                '/users',
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['status'] == 'fail')
            self.assertTrue(data['message'] == 'missing_token')
            self.assertTrue(response.content_type == 'application/json')
            self.assertEqual(response.status_code, 401)

    def test_delete_with_expired_token(self):
        """ Test for trying to delete user with expired token """
        with self.client:
            response = self.client.post(
                '/users',
                data=json.dumps(dict(
                    email='joe@gmail.com',
                    password='123456'
                )),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            time.sleep(TOKEN_DURATION+1)
            response = self.client.delete(
                '/users',
                headers=dict(
                    Authorization='Bearer ' + data['auth_token']
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['status'] == 'fail')
            self.assertTrue(data['message'] == 'expired_token')
            self.assertTrue(response.content_type == 'application/json')
            self.assertEqual(response.status_code, 401)
    def test_delete_with_invalid_token(self):
        """ Test for trying to delete user with invalid token """
        with self.client:
            response = self.client.post(
                '/users',
                data=json.dumps(dict(
                    email='joe@gmail.com',
                    password='123456'
                )),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())

            response = self.client.delete(
                '/users',
                headers=dict(
                    Authorization='Bearer ' + u'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2dnZWRJbkFzIjoiYWRtaW4iLCJpYXQiOjE0MjI3Nzk2Mzh9.gzSraSYS8EXBxLN_oWnFSRgCzcmJmMjLiuyu5CSpyHI'
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['status'] == 'fail')
            self.assertTrue(data['message'] == 'invalid_token')
            self.assertTrue(response.content_type == 'application/json')
            self.assertEqual(response.status_code, 401)


    def test_delete_already_deleted_user(self):
        """ Test for trying to delete user which was already deleted """
        with self.client:
            response = self.client.post(
                '/users',
                data=json.dumps(dict(
                    email='joe@gmail.com',
                    password='123456'
                )),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            auth_token = data['auth_token']
            response = self.client.delete(
                '/users',
                headers=dict(
                    Authorization='Bearer ' + auth_token
                ),
                content_type='application/json'
            )
            response = self.client.delete(
                '/users',
                headers=dict(
                    Authorization='Bearer ' + auth_token
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertTrue(data['status'] == 'fail')
            self.assertTrue(data['message'] == 'no_user_found')
            self.assertTrue(response.content_type == 'application/json')
            self.assertEqual(response.status_code, 404)
  
if __name__ == '__main__':
    unittest.main()
