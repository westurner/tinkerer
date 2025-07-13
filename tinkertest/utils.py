'''
    Test utilities
    ~~~~~~~~~~~~~~

    Base test case class inherited by all test cases. Utility functions.

    :copyright: Copyright 2011-2018 by Vlad Riscutia and contributors (see
    CONTRIBUTORS file)
    :license: FreeBSD, see LICENSE file
'''
import logging
import os
import shutil
import sphinx.cmd.build
import subprocess
import sys
from tinkerer import output, paths, writer
import types
import unittest


# test root directory
TEST_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "root"))


# stored test instance to assert from extensions while running Sphinx build
test = None

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def subprocess_call(cmd, *args, **kwargs):
    kwargs['stdout'] = sys.stderr
    print('#', cmd, file=sys.stderr)
    print('+', ' '.join(cmd), file=sys.stderr)
    log.debug(('subprocess_call', cmd))
    return subprocess.call(cmd, *args, **kwargs)


# base tinkerer test case
class BaseTinkererTest(unittest.TestCase):
    # common setup
    def setUp(self):
        output.quiet = True
        setup_TEST_ROOT()

    # invoke build
    def build(self, expected_return=0):
        print("")
        # call sphinx-build
        sys.argv = ["-q", "-d", paths.doctree, "-b",
                    "html", paths.root, paths.html]
        print(('sphinx-build', sys.argv), file=sys.stderr)
        print('+', ' '.join(['sphinx-build', *sys.argv]), file=sys.stderr)

        cmd = ["ls", "-l", paths.root]
        subprocess_call(cmd)

        sphinx.cmd.build.main(sys.argv)

    # common teardown - cleanup working directory
    def tearDown(self):
        cleanup()


# hook extension to conf.py
def hook_extension(ext):
    writer.write_conf_file(extensions=["tinkerer.ext.blog", ext])


def setup_TEST_ROOT():
    """setup blog using TEST_ROOT working directory"""
    # create path
    if not os.path.exists(TEST_ROOT):
        os.mkdir(TEST_ROOT)

    paths.set_paths(TEST_ROOT)

    # setup blog
    writer.setup_blog()


def cleanup():
    """cleanup test directory"""
    if os.path.exists(TEST_ROOT):
        cmd = ["ls", "-l", paths.root, paths.html]
        subprocess_call(cmd, stdout=2)
        shutil.rmtree(TEST_ROOT)


def update_conf(settings):
    """update conf.py given a dictionary of strings to replace (from -> to)"""
    conf_path = os.path.join(TEST_ROOT, "conf.py")
    with open(conf_path, "r") as conf_file:
        conf_text = conf_file.read()

    for setting in settings:
        conf_text = conf_text.replace(setting, settings[setting])

    with open(conf_path, "w") as conf_file:
        conf_file.write(conf_text)


# nose mistakenly calls Sphinx extension setup functions thinking they are
# test setups with a module parameter
def is_module(m):
    return isinstance(m, types.ModuleType)


# used by Sphinx to lookup extensions
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
