'''
    Post Creation Test
    ~~~~~~~~~~~~~~~~~~

    Tests creating posts.

    :copyright: Copyright 2011-2018 by Vlad Riscutia and contributors (see
    CONTRIBUTORS file)
    :license: FreeBSD, see LICENSE file
'''
import datetime
import os

from tinkerer import post
import tinkerer
from tinkerer import paths

from tinkertest import utils

from unittest import mock
import pytest


# test creating new post
class TestPost(utils.BaseTinkererTest):
    # test create call
    def test_create(self):
        # create post with current date
        new_post = post.create("My Post")

        year, month, day = tinkerer.utils.split_date()
        self.assertEqual(year, new_post.year)
        self.assertEqual(month, new_post.month)
        self.assertEqual(day, new_post.day)

        self.assertEqual(
            os.path.abspath(os.path.join(
                utils.TEST_ROOT,
                year,
                month,
                day,
                "my_post.rst")),
            new_post.path)

        self.assertTrue(os.path.exists(new_post.path))

        # create post with given date
        new_post = post.create("Date Post", datetime.date(2010, 10, 1))
        self.assertEqual("2010", new_post.year)
        self.assertEqual("10", new_post.month)
        self.assertEqual("01", new_post.day)

        self.assertEqual(
            os.path.abspath(os.path.join(
                utils.TEST_ROOT,
                "2010",
                "10",
                "01",
                "date_post.rst")),
            new_post.path)

        self.assertTrue(os.path.exists(new_post.path))
        self.assertEqual("2010/10/01/date_post", new_post.docname)

    def test_create_dashed(self):
        # chdir to test root and create a dummy conf.py to set the
        # slug_word_separator
        cwd = os.getcwd()
        os.chdir(utils.TEST_ROOT)

        with open("conf.py", "w") as f:
            f.write("slug_word_separator = '-'")

        # create post with current date and dash as word separator
        new_post = post.create("My __Second  Post.")

        os.chdir(cwd)

        year, month, day = tinkerer.utils.split_date()
        self.assertEqual(year, new_post.year)
        self.assertEqual(month, new_post.month)
        self.assertEqual(day, new_post.day)

        self.assertEqual(
            os.path.abspath(os.path.join(
                utils.TEST_ROOT,
                year,
                month,
                day,
                "my-second-post.rst")),
            new_post.path)

        self.assertTrue(os.path.exists(new_post.path))

    # test moving existing file to post
    def test_move(self):
        # create a "pre-existing" file
        draft_file = os.path.join(utils.TEST_ROOT, "drafts", "afile.rst")

        with open(draft_file, "w") as f:
            f.write("Content")

        # move file to post
        moved_post = post.move(draft_file, datetime.date(2010, 10, 1))
        self.assertEqual("2010", moved_post.year)
        self.assertEqual("10", moved_post.month)
        self.assertEqual("01", moved_post.day)

        self.assertEqual(
            os.path.abspath(os.path.join(
                utils.TEST_ROOT,
                "2010",
                "10",
                "01",
                "afile.rst")),
            moved_post.path)

        self.assertTrue(os.path.exists(moved_post.path))
        self.assertFalse(os.path.exists(draft_file))
        self.assertEqual("2010/10/01/afile", moved_post.docname)

    # test updating master document
    def test_master_update(self):
        post.create("Post 1", datetime.date(2010, 10, 1))
        post.create("Post 2", datetime.date(2010, 11, 2))

        with open(tinkerer.paths.master_file, "r") as f:
            lines = f.readlines()

            for lineno, line in enumerate(lines):
                if "maxdepth" in line:
                    break

            self.assertEqual("\n", lines[lineno+1])
            self.assertEqual("   2010/11/02/post_2\n", lines[lineno+2])
            self.assertEqual("   2010/10/01/post_1\n", lines[lineno+3])
            self.assertEqual("\n", lines[lineno+4])

    # test content
    def test_content(self):
        # create post with no content
        new_post = post.create("My Post")

        year, month, day = tinkerer.utils.split_date()

        # check expected empty post content
        with open(new_post.path) as f:
            self.assertEqual(
                f.readlines(),
                ["My Post\n",
                 "=======\n",
                 "\n",
                 "\n",
                 "\n",
                 ".. author:: default\n",
                 ".. categories:: none\n",
                 ".. tags:: none\n",
                 ".. comments::\n"])

        # update post
        new_post.write(author="Mr. Py", categories="category 1, category 2",
                       tags="tag 1, tag 2", content="Lorem ipsum")

        with open(new_post.path) as f:
            self.assertEqual(
                f.readlines(),
                ["My Post\n",
                 "=======\n",
                 "\n",
                 "Lorem ipsum\n",
                 "\n",
                 ".. author:: Mr. Py\n",
                 ".. categories:: category 1, category 2\n",
                 ".. tags:: tag 1, tag 2\n",
                 ".. comments::\n"])

    # test that create duplicate post raises exception
    def test_create_duplicate(self):
        # create initial post
        post.create("Post1")

        with pytest.raises(Exception):
            # should raise
            post.create("Post1")

    @mock.patch("tinkerer.writer.render")
    @mock.patch("tinkerer.master.exists_doc", return_value=True)
    def test_create_already_in_master(self, exists_doc, render):
        new_post = post.create("Existing Entry", datetime.date(2010, 10, 1))

        exists_doc.assert_called_once_with(new_post.docname)
        render.assert_called_once()

    # test that moving post to existing post raises exception
    def test_move_duplicate(self):
        # create initial post
        post.create("Post1")

        with pytest.raises(Exception):
            # should raise
            post.move("Post1")

    def test_non_string_post_name(self):
        with mock.patch("tinkerer.post.utils.name_from_title", return_value=1):
            with self.assertRaisesRegex(TypeError, "self.name should be a str"):
                post.Post("Invalid name")

    @mock.patch("tinkerer.post.os.path.exists", return_value=True)
    def test_move_existing_destination(self, exists):
        with self.assertRaisesRegex(Exception, "already exists"):
            post.move("source.rst", datetime.date(2010, 10, 1))

    @mock.patch("tinkerer.master.prepend_doc")
    @mock.patch("tinkerer.master.exists_doc", return_value=True)
    def test_move_already_in_master(self, exists_doc, prepend_doc):
        source_path = os.path.join(utils.TEST_ROOT, "drafts", "mastered.rst")
        with open(source_path, "w") as source_file:
            source_file.write("Content")

        moved_post = post.move(source_path, datetime.date(2010, 10, 1))

        self.assertTrue(os.path.exists(moved_post.path))
        exists_doc.assert_called_once_with(moved_post.docname)
        prepend_doc.assert_not_called()

    # test creating post with no template
    @mock.patch("tinkerer.writer.render")
    def test_create_without_template(self, render):
        post.create("no-template")
        render.assert_called_once_with(
            paths.post_template,
            mock.ANY,
            mock.ANY,
        )

    # test creating post with given template
    @mock.patch("tinkerer.writer.render")
    def test_create_with_template(self, render):
        post.create("with-template", template="the_template.rst")
        render.assert_called_once_with(
            "the_template.rst",
            mock.ANY,
            mock.ANY,
        )
