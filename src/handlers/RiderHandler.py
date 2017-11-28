"""Handlers related with rider's specific functionality"""

from flask import Blueprint, request, make_response, jsonify
from flask.views import MethodView
from schema import Schema, And, Use, SchemaError

from app import db, application
from src.mixins.AuthenticationMixin import Authenticator
from src.services.google_maps import get_directions
from src.services.push_notifications import send_push_notifications
from src.mixins.DriversMixin import DriversMixin

RIDERS_BLUEPRINT = Blueprint('riders', __name__)


class RidersAPI(MethodView):
    """Handler for riders related API"""

    @staticmethod
    def post(username):
        """Endpoint for requesting a ride"""

        try:
            data = request.get_json()
            schema = Schema([{'latitude_initial': And(Use(float), lambda x: -90 < x < 90),
                              'latitude_final': And(Use(float), lambda x: -90 < x < 90),
                              'longitude_initial': And(Use(float), lambda x: -180 < x < 180),
                              'longitude_final': And(Use(float), lambda x: -180 < x < 180)}])

            # IMPORTANTE: el 0 es para que devuelva el diccionario dentro y no una lista
            data = schema \
                .validate([data])[0]
            application.logger.info("{} asked to submit a request for a trip".format(username))
            if db.riders.count({'username': username}) == 0:
                response = {
                    'status': 'fail',
                    'message': 'rider_not_found'
                }
                return make_response(jsonify(response)), 404
            application.logger.info("rider {} exists".format(username))
            auth_header = request.headers.get('Authorization')
            token_username, error_message = Authenticator.authenticate(auth_header)
            if error_message:
                response = {
                    'status': 'fail',
                    'message': error_message
                }
                return make_response(jsonify(response)), 401
            application.logger.info("Submitting trip request w/ Auth: {}".format(token_username))
            application.logger.info("Token decoded: {}".format(token_username))
            if token_username == username:
                application.logger.info("Permission granted")
                application.logger.info("Rider submitting request: {}".format(token_username))

                assigned_driver = DriversMixin.get_closer_driver((data['latitude_initial'],                                                                  data['longitude_initial']))

                if assigned_driver:
                    application.logger.info("driver assigned")
                    directions_response = get_directions(data)
                    if not directions_response.ok:
                        raise Exception('failed_to_get_directions')
                    application.logger.info("google directions response:")
                    application.logger.info(directions_response)
                    if directions_response.json()['routes']:
                        directions = directions_response.json()['routes'][0]['overview_polyline']['points']
                    else:
                        raise Exception('unreachable_destination')
                    result = db.trips.insert_one(
                                                {'rider': username, 'driver': assigned_driver, 'coordinates': data,
                                                 'started': False, 'finished': False})
                    message = "A trip was assigned to you"
                    data = {
                        'rider': username,
                        'directions': directions,
                        'id': str(result.inserted_id)
                    }
                    send_push_notifications(assigned_driver, message, data)
                    response = {
                        'status': 'success',
                        'message': 'request_submitted',
                        'id': str(result.inserted_id),
                        'directions': directions,
                        'driver': assigned_driver
                    }
                    status_code = 201
                else:
                    response = {
                        'status': 'fail',
                        'message': 'no_driver_available'
                    }
                    status_code = 404
            else:
                response = {
                    'status': 'fail',
                    'message': 'unauthorized_request'
                }
                status_code = 401
            return make_response(jsonify(response)), status_code
        except SchemaError:
            application.logger.error("Request data error")
            response = {
                'status': 'fail',
                'message': 'bad_request_data'
            }
            return make_response(jsonify(response)), 400
        except Exception as exc:  # pragma: no cover
            application.logger.error('Error msg: {0}. Error doc: {1}'
                                     .format(exc.message, exc.__doc__))
            response = {
                'status': 'fail',
                'message': 'internal_error',
                'error_description': exc.message
            }
            return make_response(jsonify(response)), 500



# define the API resources
RIDERS_VIEW = RidersAPI.as_view('riders_api')

# add Rules for API Endpoints
RIDERS_BLUEPRINT.add_url_rule(
    '/riders/<username>/request',
    view_func=RIDERS_VIEW,
    methods=['POST']
)
