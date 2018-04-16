import sys
from unittest2 import defaultTestLoader
from nose.core import run


if __name__ == '__main__':
    sys.argv = ['nosetests', '-v', '--with-coverage',
                '--cover-inclusive', '--cover-erase', '--cover-package=arbi']
    run(suite=defaultTestLoader.discover('.', pattern='test_*.py'))