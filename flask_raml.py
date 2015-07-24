"""Flask-RAML (REST API Markup Language) API server with parameter conversion, response encoding, and examples."""

__all__ = 'MimeEncoders API Loader Converter Content ApiError RequestError ParameterError AuthError'.split()

__version__ = '0.2.2'

from sys import exc_info
from operator import itemgetter
from functools import wraps

from flask import abort, request, has_request_context, Response
from flask.app import HTTPException
from werkzeug.http import HTTP_STATUS_CODES
from werkzeug.datastructures import MultiDict

import flask.ext.mime_encoders
import flask.ext.mime_encoders.json

import raml
from raml import Content, ApiError, RequestError, ParameterError, AuthError
   # Export raml module properties.


class MimeEncoders(flask.ext.mime_encoders.MimeEncoders):
    default = flask.ext.mime_encoders.MimeEncoders.json


class Converter(raml.Converter):
    log = True

    def convert_params(self, specification, params):
        if isinstance(params, MultiDict):
            params, multidict = {}, params
            for key, values in multidict.iteritems():
                params[key] = values[0] if len(values) == 1 else values

        return super(Converter, self).convert_params(specification, params)


class Loader(raml.Loader):
    log = True

    spec_param_template = '{{{name}}}'
    flask_param_template = '<{flask_type}:{name}>'

    flask_types = {
        'integer': 'int',
        'number': 'float',
        'string': 'string',
        'boolean': 'bool',
        'date': 'date',
    }

    def get_resource_uri(self, resource):
        uri = resource['relativeUri']
        if 'uriParameters' in resource:
            spec_format, flask_format = self.spec_param_template.format, self.flask_param_template.format
            for name, param in resource['uriParameters'].items():
                param['name'] = name
                param['flask_type'] = self.flask_types[param['type']]
                uri = uri.replace(spec_format(**param), flask_format(**param))
            resource['allUriParameters'].update(resource['uriParameters'])
        return uri


class API(raml.API):
    """Flask API.
    """
    plugins = dict(raml.API.plugins, loader=Loader, encoders=MimeEncoders, converter=Converter)

    auth = None
    logger_name = '{app}:api'
    decode_request = True
    encode_response = True
    convert_query_params = True
    convert_uri_params = True
    endpoint_template = '{api}{resource}_{methods}'
    requested_response_status_header = 'X-Test-Response-Status'
    default_error_status = 500
    default_error_message = 'internal server error'

    config_exclude = raml.API.config_exclude.union('unhandled_uris unhandled_methods'.split())

    def __init__(self, app, path, uri=None, id=None, log=None, **options):
        self.app = app
        self.views = {}

        if log is None or isinstance(log, basestring):
            log = app.logger.manager.getLogger(log or options.get('logger_name', self.logger_name).format(app=app.name))

        super(API, self).__init__(path, uri, id, log, **options)

        self.default_mimetype = self.encoders.default.mimetype

        if self.auth and getattr(self.auth, 'log', None) is True:
            self.auth.log = log

        if log:
            log.debug(repr(self))

    @property
    def unhandled_uris(self):
        return [uri for uri in self.api if uri not in self.views]

    @property
    def unhandled_methods(self):
        result = []
        for uri, resource in self.api.iteritems():
            methods = self.views.get(uri, ())
            result.extend((uri, method) for method in resource['methodsByName'] if method.upper() not in methods)
        return result

    def abort(self, status, error=None, encoder=True):
        (self.log.exception if self.app.debug and exc_info()[0] else self.log.error)(
             '%r %s %s >> %s', status, request.method, request.path,
             error or HTTP_STATUS_CODES.get(status, 'Unknown Error'))

        if error:
            return abort(status, description=error, response = self.encoders[encoder].make_response(
                dict(status=status, error=error), status=status))
        else:
            return abort(status)

    def add_route(self, resource, view, methods=None, endpoint=None, **options):
        return self.route(resource, methods, endpoint, **options)(view)

    def route(self, resource, methods=None, endpoint=None, **options):
        resource = self.get_resource(resource)
        uri = resource['uri']
        config = dict(self.config, **options) if options else self.config
        methods = self.get_resource_methods(resource, methods)

        if endpoint is None:
            endpoint = self.get_endpoint(resource, methods, self.endpoint_template)

        auth = config['auth']
        decorate = config.get('decorate', None)
        decode_request = self.encoders[config['decode_request']]
        encode_response = self.encoders[config['encode_response']]
        convert_uri_params = config['convert_uri_params']
        convert_query_params = config['convert_query_params']

        def decorator(view):
            self.log.debug('map %s %s %s', self.id, '/'.join(sorted(methods)), uri)

            @wraps(view)
            def decorated_view(**uri_params):
                try:
                    url = request.path

                    self.log.info('%s %s << %s [%s|%s|%s]', request.method, url,
                        uri_params if self.app.debug or not uri_params else '{...}',
                        len(uri_params) or '-', len(request.args) or '-', len(request.data) or '-')

                    if auth:
                        auth.authorize(uri_params, request)

                    method = self.get_method_spec(resource, request.method)

                    if convert_uri_params:
                        uri_params = self.converter.convert_params(resource['allUriParameters'], uri_params)

                    if convert_query_params:
                        if 'queryParameters' in method:
                            uri_params.update(self.converter.convert_params(method['queryParameters'], request.args))
                        elif request.args:
                            self.abort(400, 'resource does not accept query parameters')

                    if uri_params:
                        self.log.debug('%s %s << args: %s [%s]', request.method, url, uri_params,
                            len(uri_params) or '-')

                    if decode_request:
                        self.log.debug('%s %s << data: %s [%s]', request.method, url, decode_request.name,
                            len(request.data))

                        uri_params.update(decode_request.get_request_data())

                    response = view(**uri_params)

                    if encode_response and not isinstance(response, (Response, basestring)):
                        response = encode_response.make_response(response)

                        self.log.debug('%s %s >> %s [%s:%s] (%s)', request.method, url, encode_response.name,
                            type(response.response), len(response.response), response.status)

                    return response

                except HTTPException as error:
                    if error.response:
                        # Use exception response if it was already created, either by API.abort(), or custom way.
                        raise
                    else:
                        # Otherwise, create a custom response via API.abort().
                        self.abort(error.code, error.description)
                except ApiError as error:
                    self.abort(error.status, error.message)
                except Exception as error:
                    msg =  str(error) if self.app.debug else self.default_error_message
                    self.abort(self.default_error_status, msg)

            if decorate:
                decorated_view = decorate(decorated_view)

            self.app.add_url_rule(uri, endpoint, decorated_view, methods=methods)

            for method in methods:
                self.views.setdefault(uri, {})[method] = decorated_view

            return decorated_view

        return decorator

    def serve(self, view, *args, **kwargs):
        try:
            return view(*args, **kwargs)
        except ApiError as error:
            self.abort(error.status, error.message)

    def get_endpoint(self, resource, methods=None, template=None):
        return (template or self.endpoint_template).format(
            api=self.id,
            resource=resource['uniqueId'],
            methods='+'.join(methods) if methods else 'any',
            )

    def get_response_mimetype(self, response, accept=None, request=request):
        if accept is None:
            if request and has_request_context():
                accept = map(itemgetter(0), request.accept_mimetypes)
        return super(API, self).get_response_mimetype(response, accept)

    def get_default_status(self, status=None, request=request):
        try:
            return request.headers[self.requested_response_status_header]
        except (KeyError, RuntimeError):
            return super(API, self).get_default_status()

    def serve_examples(self, **options):
        for uri, method in self.unhandled_methods:
            self.serve_example(uri, method)

    def serve_example(self, resource, methods=None, **options):
        resource = self.get_resource(resource)

        for method in self.get_resource_methods(resource, methods):
            method_spec = self.get_method_spec(resource, method)
            self.route(resource, method, **options)(self.create_example_view(method_spec))

    def create_example_view(self, method_spec):
        def view(**params):
            return self.serve(self.get_example, method_spec)
        return view

    def get_example(self, method_spec, status=None, mimetype=None):
        response = self.get_response(method_spec, status)
        body = self.get_example_body(response, mimetype)
        headers = self.get_example_headers(response)

        self.log.info('%s %s: %s %s (%d bytes, %d headers)', method_spec['method'].upper(), method_spec['uri'],
            response['status'], body.mimetype, len(body), len(headers))

        return Response(body.content, status=response['status'], headers=headers, mimetype=body.mimetype)
