# [Flask-RAML](https://github.com/salsita/flask-raml) <a href='https://github.com/salsita'><img align='right' title='Salsita' src='https://www.google.com/a/cpanel/salsitasoft.com/images/logo.gif?alpha=1' /></a>

Flask-RAML (REST API Markup Language) API server with parameter conversion, response encoding, and examples.

[![Latest Version](https://pypip.in/version/Flask-RAML/badge.svg)]
(https://pypi.python.org/pypi/Flask-RAML/)
[![Downloads](https://pypip.in/download/Flask-RAML/badge.svg)]
(https://pypi.python.org/pypi/Flask-RAML/)
[![Supported Python versions](https://pypip.in/py_versions/Flask-RAML/badge.svg)]
(https://pypi.python.org/pypi/Flask-RAML/)
[![License](https://pypip.in/license/Flask-RAML/badge.svg)]
(https://pypi.python.org/pypi/Flask-RAML/)


## Supported Platforms

* [Python](http://www.python.org/) >= 2.6, 3.3
* [Flask](http://flask.pocoo.org/) >= 0.5


## Get Started

Install using [pip](https://pip.pypa.io/) or [easy_install](http://pythonhosted.org/setuptools/easy_install.html):
```bash
pip install Flask-RAML
easy_install Flask-RAML
```

Optionally, you can specify `yaml` or `raml` extras to install related dependencies:
```bash
pip install "Flask-RAML[yaml,raml]"
easy_install "Flask-RAML[yaml,raml]"
```


## Features

- Load [RAML](http://raml.org/) API specification stored in any of supported markup languages using [PyDataLoader](https://github.com/salsita/pydataloader).
  - Support [YAML](http://yaml.org/) using [PyYAML](http://pyyaml.org/wiki/PyYAML).
  - Support [RAML](http://raml.org/) using [pyraml-parser](https://github.com/an2deg/pyraml-parser).
  - Support [JSON](http://json.org/) using [Python 2.6+ json module](https://docs.python.org/2/library/json.html), or [Python 3.x json module](https://docs.python.org/3/library/json.html).
- Provide enhanced [PyRAML](https://github.com/salsita/pyraml) API model.
  - Reuse PyRAML extensible API spec loader and parameter converters.
  - Use extensible [flask-mime-encoders](https://github.com/salsita/flask-mime-encoders) for request/response body decoding/encoding.
- Provide enhanced route decorator with optional API request/response middleware layers.
  - Auto-decode request body based on `Content-Type` header (for JSON, it reuses Flask auto-decoding).
  - Convert and validate URI/query parameters.
  - Auto-encode response with specified route encoders mimetype.
- Make it simple to serve API example response of requested/default MIME type.
  - Make also simple to serve example responses for all unhandled API resources and methods.


## Tasks

- [ ] Release example API spec and Flask API server.
  - [x] Create repository [flask-raml-example](https://github.com/salsita/flask-raml-example).
  - [ ] Design a modular sample API spec with examples and reusable schemas, types, traits and markdown docs.
  - [x] Add gulp tasks to generate HTML docs and YAML spec from the sample RAML API specs.
  - [ ] Add gulp tasks for API testing using [abao](https://github.com/cybertk/abao/).
  - [ ] Add example app deployment from Github via API yaml/html build on CircleCI to uWSGI/Flask site on Heroku.
  - [ ] Extend [raml2html](https://github.com/kevinrenskers/raml2html) API docs generator.
    - [ ] Add parameter details (min/max lenght/value, pattern).
    - [ ] Add API console for testing.
- [ ] Add autoselect encoder (based on request `Accept` header) to [flask-mime-encoders](https://github.com/salsita/flask-mime-encoders).
- [ ] Add request body JSON schema validation.
  - [ ] Extend [raml-js-parser](https://github.com/raml-org/raml-js-parser) to embed local JSON schema references for validation.
  - [ ] Optionally extend [pyraml-parser](https://github.com/an2deg/pyraml-parser) too.
  - [ ] Add optional request body JSON schema validation to the route decorator.

## Changelog

### 0.2.0

#### Features

- Add custom logger name support.
- Add view decorator support.
- Return default http 500 error on any exception.
- Add authorization support.

#### Fixes

- Update dependencies to support Python 3.
- Fix package setup on Python 3.

### 0.1.7

#### Fixes

- Fix logging http status passed as string.
- Fix Python 2.6 support with updated PyRAML 0.1.9.

### 0.1.6

#### Features

- Allow custom route request/response decoders/encoders.
- Allow abort without response body.
- Enhance logging.

### 0.1.5

#### Fixes

- Fix broken example view function attributes.
- Fix broken mime encoders import.

### 0.1.4

#### Fixes

- Fix PEP-8 style and method spec in view serving decorator.

### 0.1.3

#### Features

- Update PyRAML dependency to add default option to ignore empty parameters unless '' is specified in enum.

### 0.1.2

#### Fixes

- Fix package setup to not require dependencies preinstalled.

### 0.1.0

#### Features

- Initial release.
