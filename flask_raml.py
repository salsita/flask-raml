"""Flask-RAML (REST API Markup Language) API server with parameter conversion, response encoding, and examples."""

__all__ = 'API Loader Converter MimeEncoders RequestError ParameterError'.split()
__version__ = '0.1.4'

from flask import abort, request, has_request_context, Response
from flask.ext.mime_encoders import MimeEncoders as _MimeEncoders
from werkzeug.datastructures import MultiDict

from functools import wraps, partial
from operator import itemgetter

import raml
from raml import ApiError, RequestError, ParameterError  #export exceptions


class MimeEncoders(_MimeEncoders):
    default = _MimeEncoders.json


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

    decode_request = True
    encode_response = True
    convert_query_params = True
    convert_uri_params = True
    endpoint_template = '{api}{resource}_{methods}'
    requested_response_status_header = 'X-Test-Response-Status'

    config_exclude = raml.API.config_exclude.union('unhandled_uris unhandled_methods'.split())

    def __init__(self, app, path, uri=None, id=None, log=None, **options):
        self.app = app
        self.views = {}

        if log is None or isinstance(log, basestring):
            log = app.logger.manager.getLogger(log or 'raml')

        super(API, self).__init__(path, uri, id, log, **options)

        self.default_mimetype = self.encoders.default.mimetype

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

    def abort(self, status, error, encoder=True):
        return abort(self.encoders[encoder].make_response(dict(status=status, error=error), status=status))

    def add_route(self, resource, view, methods=None, endpoint=None, **options):
        return self.route(resource, methods, endpoint, **options)(view)

    def route(self, resource, methods=None, endpoint=None, **options):
        resource = self.get_resource(resource)
        uri = resource['uri']
        config = dict(self.config, **options) if options else self.config
        methods = self.get_resource_methods(resource, methods)

        if endpoint is None:
            endpoint = self.get_endpoint(resource, methods, self.endpoint_template)

        def decorator(view):
            self.log.debug('map %s %s %s', self.id, '/'.join(sorted(methods)), uri)

            decode_request = self.encoders['decode_request']
            encode_response = self.encoders['encode_response']
            convert_uri_params = config['convert_uri_params']
            convert_query_params = config['convert_query_params']

            @wraps(view)
            def decorated_view(**uri_params):
                try:
                    self.log.info('{} {} {}'.format(request.method, uri, uri_params))
                    method = self.get_method_spec(resource, request.method)

                    if convert_uri_params:
                        uri_params = self.converter.convert_params(resource['allUriParameters'], uri_params)

                    if convert_query_params:
                        if 'queryParameters' in method:
                            uri_params.update(self.converter.convert_params(method['queryParameters'], request.args))
                        elif request.args:
                            self.abort(400, 'resource does not accept query parameters')

                    if decode_request:
                        uri_params.update(decode_request.get_request_data())

                    self.log.info('{} {} {}'.format(request.method, resource['uri'], uri_params))
                    response = view(**uri_params)

                    if encode_response and not isinstance(response, (Response, basestring)):
                        response = encode_response.make_response(response)

                    return response

                except ApiError as error:
                    self.abort(error.status, error.message)

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

        def serve(method_spec, **params):
            return self.serve(self.get_example, method_spec)

        for method in self.get_resource_methods(resource, methods):
            method_spec = self.get_method_spec(resource, method)
            view = partial(serve, method_spec)
            self.route(resource, method, **options)(view)

    def get_example(self, method_spec, status=None, mimetype=None):
        response = self.get_response(method_spec, status)
        body = self.get_example_body(response, mimetype)
        headers = self.get_example_headers(response)

        self.log.info('%s %s: %d %s (%d bytes, %d headers)', method_spec['method'].upper(), method_spec['uri'],
            response['status'], body.mimetype, len(body), len(headers))

        return Response(body.content, status=response['status'], headers=headers, mimetype=body.mimetype)
