"""
Create a zip file that contains the right files
"""

import os
import shutil
from arbi.constants import VERSION

target_dir = '../../../sent/arbi'
ignored_dirs = ['logs', 'playground', 'tests', '.idea', 'bookies', 'history',
                'stored_data', 'mock_data', 'scripts', 'tools', 'web_scrapers']


if __name__ == '__main__':
    shutil.copytree('../', target_dir, ignore=lambda p, f: ignored_dirs)
    os.chdir(target_dir)
    os.mkdir('logs')

    for filename in ['.coverage', '.coveragerc', 'pytest_coverage.py']:
        os.remove(filename)

    os.chdir('..')

    shutil.make_archive('arbi' + VERSION, 'zip', 'arbi')

    shutil.rmtree('arbi')
