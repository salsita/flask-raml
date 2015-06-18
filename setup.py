#!/usr/bin/env python

import re
__src__ = file('flask_raml.py').read()
__doc__ = re.search('^(["\']{3})(.*?)\\1', __src__, re.M|re.S).group(2).strip()
__version__ = re.search('^__version__\s*=\s*(["\'])(.*?)\\1\s*$', __src__, re.M).group(2).strip()

options = dict(
    minver = '2.6',     # Min Python version required.
    maxver = None,      # Max Python version required.
    use_stdeb = False,  # Use stdeb for building deb packages.
    use_markdown_readme = True, # Use markdown README.md.
    )

properties = dict(
    name = 'Flask-RAML',
    version = __version__,
    url = 'https://github.com/salsita/flask-raml',
    download_url = 'https://github.com/salsita/flask-raml/tarball/v{}'.format(__version__),
    description = __doc__.strip().split('\n', 1)[0].strip('.'),
        # First non-empty line of module doc
    long_description = (__doc__.strip() + '\n').split('\n', 1)[1].strip(),
        # Module doc except first non-empty line
    author = 'Salsita Software',
    author_email = 'python@salsitasoft.com',
    license = 'MIT',
    zip_safe = True,
    platforms = 'any',
    keywords = [
        'Flask',
        'RAML',
        'REST',
        'API',
        ],
    py_modules = [
        'flask_raml',
        ],
    packages = [
        ],
    namespace_packages = [
        ],
    include_package_data = False,
    install_requires = [
        'Flask>=0.5',
        'Flask-MIME-encoders>=0.1.2',
        'PyRAML>=0.2.0',
        ],
    extras_require = {
        'raml': [
            'pyraml-parser>=0.1.5',
            ],
        'yaml': [
            'PyYAML>=3.11',
            ],
        },
    dependency_links=[
        ],
    entry_points = {
        },
    scripts=[
        ],
    classifiers = [
        # See http://pypi.python.org/pypi?:action=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'License :: OSI Approved :: MIT License',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Text Processing :: Markup',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    )

def main(properties=properties, options=options, **custom_options):
    """Imports and runs setup function with given properties."""
    return init(**dict(options, **custom_options))(**properties)

def init(
    dist='dist',
    minver=None,
    maxver=None,
    use_markdown_readme=True,
    use_stdeb=False,
    use_distribute=False,
    ):
    """Imports and returns a setup function.

    If use_markdown_readme is set,
    then README.md is added to setuptools READMES list.

    If use_stdeb is set on a Debian based system,
    then module stdeb is imported.
    Stdeb supports building deb packages on Debian based systems.
    The package should only be installed on the same system version
    it was built on, though. See http://github.com/astraw/stdeb.

    If use_distribute is set, then distribute_setup.py is imported.
    """
    if not minver == maxver == None:
        import sys
        if not minver <= sys.version < (maxver or 'Any'):
            sys.stderr.write(
                '%s: requires python version in <%s, %s), not %s\n' % (
                sys.argv[0], minver or 'any', maxver or 'any', sys.version.split()[0]))
            sys.exit(1)

    if use_distribute:
        from distribute_setup import use_setuptools
        use_setuptools(to_dir=dist)
        from setuptools import setup
    else:
        try:
            from setuptools import setup
        except ImportError:
            from distutils.core import setup

    if use_markdown_readme:
        try:
            import setuptools.command.sdist
            setuptools.command.sdist.READMES = tuple(list(getattr(setuptools.command.sdist, 'READMES', ()))
                + ['README.md'])
        except ImportError:
            pass

    if use_stdeb:
        import platform
        if 'debian' in platform.dist():
            try:
                import stdeb
            except ImportError:
                pass

    return setup

if __name__ == '__main__':
    main()
