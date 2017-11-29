import unittest
import json
import time
from tests.base import BaseTestCase
from mock import patch, Mock
from app import TOKEN_DURATION

class TestTripStarting(BaseTestCase):

    rider_joe_auth_token = ''
    rider_will_auth_token = ''
    driver_auth_token = ''
    request_id = 0

    def setUp(self):
        BaseTestCase.setUp(self)
        with self.client:
            with patch('requests.post') as mock_post:
                mock_post.return_value = Mock()
                mock_post.return_value.json.return_value = {'id': "1"}
                mock_post.return_value.ok = True
                mock_post.return_value.status_code = 201
                response = self.client.post(
                    '/users',
                    data=json.dumps(dict(
                        username='joe_smith',
                        password='123456',
                        type='rider'
                    )),
                    content_type='application/json'
                )
                data = json.loads(response.data.decode())
                self.rider_joe_auth_token = data['auth_token']

                mock_post.return_value.json.return_value = {'id': "2"}
                response = self.client.post(
                    '/users',
                    data=json.dumps(dict(
                        username='william_dafoe',
                        password='123456',
                        type='rider'
                    )),
                    content_type='application/json'
                )
                data = json.loads(response.data.decode())
                self.rider_will_auth_token = data['auth_token']

                mock_post.return_value.json.return_value = {'id': "3"}
                response = self.client.post(
                    '/users',
                    data=json.dumps(dict(
                        username='johny',
                        password='123456',
                        type='driver'
                    )),
                    content_type='application/json'
                )
                data = json.loads(response.data.decode())
                self.driver_auth_token = data['auth_token']

                self.client.put(
                    '/users/johny/coordinates',
                    data=json.dumps(dict(
                        latitude=30.12,
                        longitude=42.03
                    )),
                    headers=dict(
                        Authorization='Bearer ' + self.driver_auth_token
                    ),
                    content_type='application/json'
                )

                self.client.patch(
                    '/drivers/johny',
                    data=json.dumps(dict(
                        duty=True
                    )),
                    headers=dict(
                        Authorization='Bearer ' + self.driver_auth_token
                    ),
                    content_type='application/json'
                )

                with patch('src.handlers.RequestHandler.DriversMixin') as mock_mixin:
                    with patch('src.handlers.RequestHandler.get_directions') as mock_directions:

                        mock_mixin.get_closer_driver = Mock()
                        mock_mixin.get_closer_driver.return_value = 'johny'

                        mock_directions.return_value = Mock()
                        mock_directions.return_value.ok = True
                        mock_directions.return_value.json.return_value = {
                            'routes': [
                                {
                                    'overview_polyline': {
                                        'points':   "fe}qEbtwcJsBhBmBsD}BkEcBkDc@cAYa@jC{E`@}@"
                                                    "jBwDl@wBh@yBHQNa@r@_B|@eBZi@d@kAfBmFXuA^q"
                                                    "B^qBd@{Cl@_GDu@L}BCQKc@V{BL}@\\aBZmAt@qBx"
                                                    "GwMbC{E|BwE~A"
                                    }
                                }
                            ]
                        }

                        response = self.client.post(
                            '/riders/joe_smith/request',
                            data=json.dumps(dict(
                                latitude_initial=30.00,
                                latitude_final=31.32,
                                longitude_initial=42,
                                longitude_final=43.21
                            )),
                            headers=dict(
                                Authorization='Bearer ' + self.rider_joe_auth_token
                            ),
                            content_type='application/json'
                        )
                        data = json.loads(response.data.decode())
                    self.request_id = data['id']

    def test_start_trip_without_token(self):

        with self.client:
            response = self.client.post(
                '/drivers/johny/trip',
                data=json.dumps(dict(
                    request_id=self.request_id
                )),
                headers=dict(
                    Authorization='Bearer'
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertEqual(data['message'], 'missing_token')
            self.assertEqual(data['status'], 'fail')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 401)

    def test_start_trip_invalid_token(self):

        with self.client:
            response = self.client.post(
                '/drivers/johny/trip',
                data=json.dumps(dict(
                    request_id=self.request_id
                )),
                headers=dict(
                    Authorization='Bearer asaf847jrfn'
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertEqual(data['message'], 'invalid_token')
            self.assertEqual(data['status'], 'fail')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 401)

    def test_start_trip_expired_token(self):

        time.sleep(TOKEN_DURATION + 1)
        with self.client:
            response = self.client.post(
                '/drivers/johny/trip',
                data=json.dumps(dict(
                    request_id=self.request_id
                )),
                headers=dict(
                    Authorization='Bearer ' + self.driver_auth_token
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertEqual(data['message'], 'expired_token')
            self.assertEqual(data['status'], 'fail')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 401)

    def test_start_trip_not_a_driver_in_url(self):

        with self.client:
            response = self.client.post(
                '/drivers/william_dafoe/trip',
                data=json.dumps(dict(
                    request_id=self.request_id
                )),
                headers=dict(
                    Authorization='Bearer ' + self.driver_auth_token
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertEqual(data['message'], 'driver_not_found')
            self.assertEqual(data['status'], 'fail')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 404)

    def test_start_trip_token_username_different_to_url_username(self):
        with self.client:
            response = self.client.post(
                '/drivers/johny/trip',
                data=json.dumps(dict(
                    request_id=self.request_id
                )),
                headers=dict(
                    Authorization='Bearer ' + self.rider_joe_auth_token
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertEqual(data['message'], 'unauthorized_action')
            self.assertEqual(data['status'], 'fail')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 401)

    def test_start_trip_request_id_not_valid(self):
        with self.client:
            response = self.client.post(
                '/drivers/johny/trip',
                data=json.dumps(dict(
                    request_id="dansjc8384331c"
                )),
                headers=dict(
                    Authorization='Bearer ' + self.driver_auth_token
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertEqual(data['message'], 'bad_request_data')
            self.assertEqual(data['status'], 'fail')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 400)

    def test_start_trip_request_not_found_non_existent_id(self):
        with self.client:
            response = self.client.post(
                '/drivers/johny/trip',
                data=json.dumps(dict(
                    request_id="54f0e5aa313f5d824680d6c9"
                )),
                headers=dict(
                    Authorization='Bearer ' + self.driver_auth_token
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertEqual(data['message'], 'request_not_found')
            self.assertEqual(data['status'], 'fail')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 404)

    def test_start_trip_token_username_different_to_request_driver_username(self):
        with self.client:
            driver2_auth_token = ''
            with patch('requests.post') as mock_post:
                mock_post.return_value = Mock()
                mock_post.return_value.json.return_value = {'id': "4"}
                mock_post.return_value.ok = True
                mock_post.return_value.status_code = 201
                response = self.client.post(
                    '/users',
                    data=json.dumps(dict(
                        username='johny2',
                        password='123456',
                        type='driver'
                    )),
                    content_type='application/json'
                )
                data = json.loads(response.data.decode())
                driver2_auth_token = data['auth_token']

            response = self.client.post(
                '/drivers/johny2/trip',
                data=json.dumps(dict(
                    request_id=self.request_id
                )),
                headers=dict(
                    Authorization='Bearer ' + driver2_auth_token
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertEqual(data['message'], 'unauthorized_for_request')
            self.assertEqual(data['status'], 'fail')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 401)

    def test_start_trip_succesfully(self):
        with self.client:
            response = self.client.post(
                '/drivers/johny/trip',
                data=json.dumps(dict(
                    request_id=self.request_id
                )),
                headers=dict(
                    Authorization='Bearer ' + self.driver_auth_token
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertEqual(data['message'], 'trip_started')
            self.assertEqual(data['status'], 'success')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 201)

    def test_start_trip_already_started(self):
        with self.client:
            response = self.client.post(
                '/drivers/johny/trip',
                data=json.dumps(dict(
                    request_id=self.request_id
                )),
                headers=dict(
                    Authorization='Bearer ' + self.driver_auth_token
                ),
                content_type='application/json'
            )
            response = self.client.post(
                '/drivers/johny/trip',
                data=json.dumps(dict(
                    request_id=self.request_id
                )),
                headers=dict(
                    Authorization='Bearer ' + self.driver_auth_token
                ),
                content_type='application/json'
            )
            data = json.loads(response.data.decode())
            self.assertEqual(data['message'], 'request_not_found')
            self.assertEqual(data['status'], 'fail')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, 404)
