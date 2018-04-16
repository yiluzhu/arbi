"""
Create a zip file that contains the right files
"""

import os
import shutil
from arbi.tools.oh.constants import OH_TOOL_VER

target_dir = '../../../../../sent/oh/'

if __name__ == '__main__':
    shutil.copytree('../../../tools', target_dir + 'tools', ignore=lambda p, f: ['tc'])
    for dirname in ['feeds', 'models']:
        shutil.copytree('../../../' + dirname, target_dir + dirname)
    for filename in ['__init__', 'arbi_summary', 'constants', 'utils']:
        shutil.copy('../../../{}.py'.format(filename), target_dir + '{}.py'.format(filename))

    os.chdir(target_dir + '..')

    shutil.make_archive('oh_tool_' + OH_TOOL_VER, 'zip', 'oh')

    shutil.rmtree('oh')
