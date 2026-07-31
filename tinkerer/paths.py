'''
    paths
    ~~~~~

    Tinkerer path information.

    :copyright: Copyright 2011-2018 by Vlad Riscutia and contributors (see
    CONTRIBUTORS file)
    :license: FreeBSD, see LICENSE file
'''
import os
import tinkerer
import sys


# package path
__package_path = None


# absolute path to assets
__internal_templates_abs_path = None
templates = []
themes = []
static = None


# template names
post_template = "post.rst"
page_template = "page.rst"


# favicon
favicon = "tinkerer.ico"

# Path to local extensions
_exts = None


def set_paths(root_path="."):
    '''
    Computes required relative paths based on given root path.
    '''
    global root
    try:
        # if root_path == '.':
        #     root = '.'
        # else:
        root = os.path.abspath(root_path)
    except FileNotFoundError:
        print(('root_path', root_path))
        return
        raise

    global blog, doctree, html, master_file, index_file, conf_file
    blog = os.path.join(root, "blog")
    doctree = os.path.join(blog, "doctrees")
    html = os.path.join(blog, "html")
    master_file = os.path.join(root,
                               tinkerer.master_doc + next(iter(tinkerer.source_suffix.keys())))
    index_file = os.path.join(root, "index.html")
    conf_file = os.path.join(root, "conf.py")

    # relative path to assets required by conf.py
    global themes, templates, static

    global _exts
    if not _exts:
        # add "./_exts" path to os search path so Sphinx can pick up any extensions
        # from there
        try:
            sys.path.append(os.path.abspath("./_exts"))
        except FileNotFoundError:
            pass
    else:
        sys.path.remove(_exts)
        sys.path.append(os.path.abspath("./_exts"))


    global __package_path, __internal_templates_abs_path
    # package path
    __package_path = os.path.abspath(os.path.dirname(__file__))


    # absolute path to assets
    __internal_templates_abs_path = os.path.join(__package_path, "__templates")
    themes = os.path.join(__package_path, "themes")
    static = os.path.join(__package_path, "static")

    templates = os.path.join(os.path.abspath("."), "_templates")



# compute paths on import
set_paths()
