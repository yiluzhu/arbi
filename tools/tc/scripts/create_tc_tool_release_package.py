"""
Create a zip file that contains the right files
"""

import os
import shutil
from arbi.tools.tc.main import TC_TOOL_VER

target_dir = '../../../../../sent/tc'
ignored_dirs = ['logs', 'playground', 'tests', '.idea', 'bookies', 'history',
                'stored_data', 'mock_data', 'oh']


if __name__ == '__main__':
    shutil.copytree('../../..', target_dir, ignore=lambda p, f: ignored_dirs)
    os.chdir(target_dir)

    ignored_py_modules = []
    for x in ['arbi_pro', 'main']:
        ignored_py_modules.append(x + '.py')
        ignored_py_modules.append(x + '.pyc')

    for filename in [ '.coveragerc', 'release_note.txt', 'pytest_coverage.py', 'pytest_coverage.pyc'] + ignored_py_modules:
        os.remove(filename)

    shutil.rmtree('scripts')

    os.chdir('..')

    shutil.make_archive('tc_tool_' + TC_TOOL_VER, 'zip', 'tc')

    shutil.rmtree('tc')
