'''
    Command Line Test
    ~~~~~~~~~~~~~~~~~

    Tests Tinkerer command line (setup, post, page and build)

    :copyright: Copyright 2011-2018 by Vlad Riscutia and contributors (see
    CONTRIBUTORS file)
    :license: FreeBSD, see LICENSE file
'''
import datetime
import logging
import os
from io import StringIO
from unittest import mock
import tinkerer
from tinkerer import cmdline, output, paths, post
from tinkertest import utils


# test tinkerer command line
class TestCmdLine(utils.BaseTinkererTest):
    # these tests cause lots of output, disable logging while they are running
    def setUp(self):
        logging.disable(logging.CRITICAL)
        utils.setup_TEST_ROOT()

    # re-enable logging
    def tearDown(self):
        logging.disable(logging.NOTSET)
        utils.cleanup()

    # test blog setup
    def test_setup(self):
        # blog is setup as part of test setup, tear it down and
        # re-create it via cmdline
        self.tearDown()
        cmdline.main(["--setup", "--quiet"])

        self.assertEqual(
            set(os.listdir(utils.TEST_ROOT)),
            set([
                "_static",
                "_templates",
                "drafts",
                "conf.py",
                "index.html",
                tinkerer.master_doc + ".rst"
            ]))

        # favicon should be copied to the blog _static folder
        self.assertTrue(os.path.exists(
            os.path.join(utils.TEST_ROOT, "_static", paths.favicon)
            ))

    # test post from title
    def test_post_from_title(self):
        cmdline.main(["--post", "My Test Post", "--quiet"])

        # this might fail at midnight :P
        year, month, day = tinkerer.utils.split_date()

        file_path = os.path.join(utils.TEST_ROOT, year, month, day,
                                 "my_test_post.rst")

        # assert file exists
        self.assertTrue(os.path.exists(file_path))

    # test post from existing file
    def test_post_from_path(self):
        # create file
        draft_file = os.path.join(utils.TEST_ROOT, "drafts", "draft_post.rst")

        with open(draft_file, "w") as f:
            f.write("Content")

        cmdline.main(["--post", draft_file, "--quiet"])

        # this might also fail at midnight :P
        year, month, day = tinkerer.utils.split_date()

        file_path = os.path.join(utils.TEST_ROOT, year, month, day,
                                 "draft_post.rst")

        # assert file exists and check content
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r") as f:
            self.assertEqual("Content", f.read())

    # test post with explicit date
    def test_post_with_date(self):
        cmdline.main(["--post", "Dated Post", "--date", "2011/11/20"])

        file_path = os.path.join(utils.TEST_ROOT, "2011/11/20",
                                 "dated_post.rst")

        # assert file exists
        self.assertTrue(os.path.exists(file_path))

    # test date is only allowed with post argument
    def test_date_only_on_post(self):
        self.assertNotEqual(
            0,
            cmdline.main(["--page", "Test Page", "--date", "2011/11/20"]))

        self.assertNotEqual(
            0,
            cmdline.main(["--draft", "Test Draft", "--date", "2011/11/20"]))

        self.assertNotEqual(
            0,
            cmdline.main(["--build", "--date", "2011/11/20"]))

    def test_invalid_post_date(self):
        self.assertNotEqual(
            0, cmdline.main(["--post", "Invalid Date", "--date", "bad"]))

    @mock.patch("tinkerer.cmdline.setup")
    def test_main_setup_dispatch(self, setup):
        self.assertEqual(0, cmdline.main(["--setup"]))
        setup.assert_called_once_with()

    @mock.patch("tinkerer.cmdline.build", return_value=0)
    def test_main_build_dispatch(self, build):
        self.assertEqual(0, cmdline.main(["--build"]))
        build.assert_called_once_with()

    # test page from title
    def test_page_from_title(self):
        cmdline.main(["--page", "My Test Page", "--quiet"])

        file_path = os.path.join(utils.TEST_ROOT, "pages", "my_test_page.rst")

        # assert file exsits
        self.assertTrue(os.path.exists(file_path))

    # test page from existing file
    def test_post_from_existing_file(self):
        # create file
        draft_file = os.path.join(utils.TEST_ROOT, "drafts", "draft_page.rst")

        with open(draft_file, "w") as f:
            f.write("Content")

        cmdline.main(["--page", draft_file, "--quiet"])

        file_path = os.path.join(utils.TEST_ROOT, "pages", "draft_page.rst")

        # assert file exists and check content
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r") as f:
            self.assertEqual("Content", f.read())

    # test draft
    def test_draft(self):
        cmdline.main(["--draft", "My Draft", "--quiet"])

        file_path = os.path.join(utils.TEST_ROOT, "drafts", "my_draft.rst")

        # assert draft was created
        self.assertTrue(os.path.exists(file_path))

    def test_draft_from_path(self):
        source_path = os.path.join(utils.TEST_ROOT, "source.rst")
        with open(source_path, "w") as source_file:
            source_file.write("Content")

        self.assertEqual(0, cmdline.main(["--draft", source_path, "--quiet"]))
        self.assertTrue(os.path.exists(
            os.path.join(utils.TEST_ROOT, "drafts", "source.rst")))

    # test missing template
    def test_missing_template(self):
        # creating a post with a missing template file should fail
        self.assertNotEqual(
            0,
            cmdline.main(["--post", "test", "--template", "missing",
                          "--quiet"])
        )

    # test build
    def test_build(self):
        # create a new post
        post.create("My Post", datetime.date(2010, 10, 1))

        self.build()

        # assert html is produced
        self.assertTrue(os.path.exists(
            os.path.join(utils.TEST_ROOT, "blog", "html", "2010",
                         "10", "01", "my_post.html")))

    @mock.patch("tinkerer.cmdline.subprocess.call", return_value=7)
    @mock.patch("sphinx.cmd.build.build_main", return_value=9)
    @mock.patch("tinkerer.cmdline.shutil.copytree")
    @mock.patch("tinkerer.cmdline.shutil.rmtree")
    @mock.patch("tinkerer.cmdline.os.path.exists")
    def test_build_modes(self, exists, rmtree, copytree, build_main,
                         subprocess_call):
        exists.side_effect = lambda path: path in (paths.blog, "_copy")

        with mock.patch.object(output, "quiet", True):
            self.assertEqual(7, cmdline.build(in_subprocess=True, pdb=False))

        build_flags = ["sphinx-build", "-d", paths.doctree, "-b", "html",
                       paths.root, paths.html]
        subprocess_call.assert_called_once_with(
            ["sphinx-build", "-q"] + build_flags[1:])
        rmtree.assert_called_once_with(paths.blog)
        copytree.assert_called_once_with("_copy/", paths.html)

        exists.reset_mock()
        rmtree.reset_mock()
        copytree.reset_mock()
        with mock.patch.object(output, "quiet", False):
            self.assertEqual(9, cmdline.build(in_subprocess=False, pdb=True))

        build_main.assert_called_once_with(build_flags[1:] + ["--pdb"])
        rmtree.assert_called_once_with(paths.blog)
        copytree.assert_called_once_with("_copy/", paths.html)

    @mock.patch("sphinx.cmd.build.build_main", return_value=0)
    @mock.patch("tinkerer.cmdline.shutil.copytree")
    @mock.patch("tinkerer.cmdline.shutil.rmtree")
    @mock.patch("tinkerer.cmdline.os.path.exists", return_value=False)
    def test_build_without_optional_paths(self, exists, rmtree, copytree,
                                          build_main):
        with mock.patch.object(output, "quiet", False):
            self.assertEqual(0, cmdline.build(pdb=False))

        build_main.assert_called_once_with(
            ["-d", paths.doctree, "-b", "html", paths.root, paths.html])
        rmtree.assert_not_called()
        copytree.assert_not_called()

    def test_main_root_path(self):
        with mock.patch.object(cmdline.os, "chdir") as chdir:
            with mock.patch.object(paths, "set_paths") as set_paths:
                self.assertEqual(
                    0, cmdline.main(["--root", utils.TEST_ROOT, "--version"]))

        chdir.assert_called_once_with(utils.TEST_ROOT)
        set_paths.assert_called_once_with()

    def test_set_paths_with_existing_extensions_path(self):
        mock_sys = mock.Mock()
        with mock.patch.object(paths, "_exts", "extension-path"):
            with mock.patch.object(paths, "sys", mock_sys):
                paths.set_paths(utils.TEST_ROOT)

        mock_sys.path.remove.assert_called_once_with("extension-path")
        mock_sys.path.append.assert_called_once_with(os.path.abspath("./_exts"))

    def test_main_valid_template(self):
        template = "custom-template.rst"
        with mock.patch("tinkerer.cmdline.os.path.exists", return_value=True):
            with mock.patch("tinkerer.cmdline.create_post") as create_post:
                self.assertEqual(
                    0,
                    cmdline.main(["--post", "Test", "--template", template]))

        create_post.assert_called_once_with("Test", None, template)

    def test_preview_missing(self):
        with self.assertRaisesRegex(Exception, "does not exist"):
            cmdline.preview_draft("missing-draft.rst")

    def test_main_without_command(self):
        with mock.patch("argparse.ArgumentParser.print_help") as print_help:
            self.assertEqual(0, cmdline.main([]))

        print_help.assert_called_once_with()

    # ensure tinkerer only runs from blog root (dir containing conf.py) except
    # when running setup
    def test_root_only(self):
        # remove "conf.py" created by test setup
        os.remove(os.path.join(paths.root, "conf.py"))

        self.assertNotEqual(
            0,
            cmdline.main(["--page", "Test Post", "--quiet"]))

        self.assertNotEqual(
            0,
            cmdline.main(["--post", "Test Page", "--quiet"]))

        self.assertNotEqual(
            0,
            cmdline.main(["--build", "--quiet"]))

        # setup should work fine from anywhere
        self.assertEqual(
            0,
            cmdline.main(["--setup", "--quiet"]))

    def test_filename_only(self):
        # hook up test log handler
        test_stream = StringIO()

        # restore logging for this particular test
        logging.disable(logging.NOTSET)

        output.filename.addHandler(logging.StreamHandler(test_stream))

        # setup new blog with --filename flag
        cmdline.main(["--setup", "--filename"])

        # output should be `conf.py`
        self.assertEqual("conf.py", test_stream.getvalue().strip())
