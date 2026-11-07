"""Focused tests for extension branch behavior."""
import builtins
import runpy
from types import SimpleNamespace
import unittest
from unittest import mock

from docutils import nodes
from sphinx.writers.html import HTMLTranslator

import tinkerer
from tinkerer.ext import aggregator, author, blog, html5, metadata, uistr


class TestExtensionBranches(unittest.TestCase):
    def depart_title(self, parent, close_tag, enabled):
        translator = SimpleNamespace(
            context=[close_tag],
            config=SimpleNamespace(html_permalinks=enabled,
                                   html_permalinks_icon="link"),
            builder=SimpleNamespace(add_permalinks=True),
            body=[],
            add_permalink_ref=mock.Mock(),
        )
        node = nodes.title("Heading")
        parent += node

        with mock.patch.object(HTMLTranslator, "_depart_title", create=True):
            with mock.patch("tinkerer.ext.html5._", return_value="Link",
                            create=True):
                html5.depart_title(translator, node)

        return translator

    def test_depart_title_heading_permalink(self):
        translator = self.depart_title(
            nodes.section(ids=["heading"]), "</h2>", True)

        translator.add_permalink_ref.assert_called_once()
        self.assertEqual([], translator.body)

    def test_depart_title_linked_heading_permalink(self):
        translator = self.depart_title(
            nodes.section(ids=["heading"]), "</a></h2>", True)

        self.assertIn('href="#heading"', translator.body[0])

    def test_depart_title_table_permalink(self):
        translator = self.depart_title(
            nodes.table(ids=["table"]), "</p>", True)

        self.assertEqual(["</span>"], translator.body)
        translator.add_permalink_ref.assert_called_once()

    def test_depart_title_table_without_permalink(self):
        translator = self.depart_title(
            nodes.table(ids=["table"]), "</p>", False)

        self.assertEqual(["</span>"], translator.body)

    def test_depart_title_ignored_close_tag(self):
        translator = self.depart_title(
            nodes.section(ids=["heading"]), "</p>", True)

        translator.add_permalink_ref.assert_not_called()
        self.assertEqual([], translator.body)

    def test_depart_title_without_permalink(self):
        translator = self.depart_title(
            nodes.section(ids=["heading"]), "</h2>", False)

        translator.add_permalink_ref.assert_not_called()
        self.assertEqual([], translator.body)

    def test_custom_author(self):
        record = SimpleNamespace(author=None)
        env = SimpleNamespace(
            config=SimpleNamespace(author="Default Author"),
            docname="post",
            blog_metadata={"post": record},
        )
        directive = object.__new__(author.AuthorDirective)
        directive.arguments = ["Ada", "Lovelace"]
        directive.state = SimpleNamespace(document=SimpleNamespace(
            settings=SimpleNamespace(env=env)))

        self.assertEqual([], directive.run())
        self.assertEqual("Ada Lovelace", record.author)

    def test_initialize_normalizes_website(self):
        config = SimpleNamespace(
            website="https://example.test", language=None,
            first_page_title="Start")
        app = SimpleNamespace(config=config)
        translation = mock.Mock()
        translation.gettext.side_effect = lambda value: value

        with mock.patch.object(blog.metadata, "initialize"):
            with mock.patch.object(blog.filing, "initialize"):
                with mock.patch.object(
                        blog.gettext, "translation", return_value=translation):
                    blog.initialize(app)

        self.assertEqual("https://example.test/", config.website)
        self.assertEqual("Start", uistr.UIStr.HOME)
        translation.install.assert_called_once_with()

    def test_aggregator_with_landing_page(self):
        env = SimpleNamespace(
            blog_pages=["pages/landing"],
            blog_posts=["post1", "post2"],
            blog_metadata={
                "post1": SimpleNamespace(title="First"),
                "post2": SimpleNamespace(title="Second"),
            },
        )
        app = SimpleNamespace(
            builder=SimpleNamespace(env=env),
            config=SimpleNamespace(posts_per_page=1, landing_page="landing"),
        )

        with mock.patch.multiple(
                uistr.UIStr, HOME="Home", NEWER="Newer", OLDER="Older",
                PAGE_FMT="Page %d", BLOG_ARCHIVE="Archive", create=True):
            pages = list(aggregator.make_aggregated_pages(app))

        self.assertEqual(["index", "page1", "page2"],
                         [page[0] for page in pages])
        self.assertEqual("page1.html", pages[2][1]["prev"]["link"])

    def test_process_metadata_skips_unclassified_and_nested_docs(self):
        class Title:
            def __init__(self, value):
                self.value = value

            def astext(self):
                return self.value

        records = {
            "nested": SimpleNamespace(is_post=False, is_page=True),
            "unclassified": SimpleNamespace(is_post=False, is_page=False),
            "post": SimpleNamespace(is_post=True, is_page=False),
            "page": SimpleNamespace(is_post=False, is_page=True),
        }
        docnames = [tinkerer.master_doc, "untracked", "nested",
                    "unclassified", "post", "page"]
        relations = {
            tinkerer.master_doc: (None, None, "untracked"),
            "untracked": (tinkerer.master_doc, None, "nested"),
            "nested": ("parent", None, "unclassified"),
            "unclassified": (tinkerer.master_doc, None, "post"),
            "post": (tinkerer.master_doc, None, "page"),
            "page": (tinkerer.master_doc, None, None),
        }
        env = SimpleNamespace(
            collect_relations=lambda: relations,
            blog_metadata=records,
            titles={docname: Title(docname) for docname in records},
        )
        app = SimpleNamespace(config=SimpleNamespace(landing_page=None))

        with mock.patch.multiple(
                uistr.UIStr, HOME="Home", create=True):
            metadata.process_metadata(app, env)

        self.assertEqual(["post"], env.blog_posts)
        self.assertEqual(["page"], env.blog_pages)

    def test_add_metadata_for_documentation_page(self):
        record = SimpleNamespace()
        env = SimpleNamespace(
            blog_page_list=[], blog_posts=[], blog_metadata={"docs/api": record},
            titles={}, filing={"tags": [], "categories": []},
        )
        app = SimpleNamespace(
            builder=SimpleNamespace(env=env),
            config=SimpleNamespace(website="https://example.test/",
                                   tagline="", description=""),
        )
        context = {"body": "documentation"}

        with mock.patch.multiple(
                uistr.UIStr, RECENT_POSTS="Recent", POSTED_BY="By",
                BLOG_ARCHIVE="Archive", FILED_UNDER="Filed", TAGS="Tags",
                TAGS_CLOUD="Cloud", CATEGORIES="Categories", create=True):
            metadata.add_metadata(app, "docs/api", context)

        self.assertIs(record, context["metadata"])
        self.assertNotIn("prev", context)

    def test_unicode_compatibility_branch(self):
        with mock.patch.dict(builtins.__dict__, {
                "unicode": lambda value, encoding: value}):
            module_globals = runpy.run_path(uistr.__file__)

        self.assertNotIn("unicode", module_globals)