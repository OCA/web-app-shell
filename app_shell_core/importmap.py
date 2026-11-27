# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
"""Import map helpers for the ES modules of single page apps.

The app is made of plain ES modules served from each module's ``static``
folder. Static files are served by Odoo with a long cache, hence:

* every JS file gets a version token: the version of its Odoo module
  or a hash of its content (see `app.shell.mixin.importmap.js_version_mode`)
* an import map tells the browser to load every module via its versioned URL

Since the map is applied to every ``import`` (relative or absolute),
modules importing each other always end up on the same versioned URL.
This gives proper cache busting and a single instance per module.

The same map is used to replace modules (see ``build_importmap``).
"""

import hashlib
import os

from werkzeug.security import safe_join

from odoo.modules.module import get_manifest, get_module_path

# Folders never served to the app
EXCLUDED_DIRS = {"description", "tests", "node_modules"}
JS_EXTENSIONS = (".js", ".mjs")

# filepath -> (mtime_ns, size, token)
_TOKEN_CACHE = {}


def file_token(filepath):
    """Return a short hash of the content of given file.

    Results are cached until the file changes on disk (mtime or size),
    so that files are hashed only once per process.
    """
    stat = os.stat(filepath)
    cached = _TOKEN_CACHE.get(filepath)
    if cached and cached[:2] == (stat.st_mtime_ns, stat.st_size):
        return cached[2]
    with open(filepath, "rb") as fd:
        token = hashlib.sha1(fd.read(), usedforsecurity=False).hexdigest()[:12]
    _TOKEN_CACHE[filepath] = (stat.st_mtime_ns, stat.st_size, token)
    return token


def module_version(module_name):
    """Return the version of given module, from its manifest."""
    return get_manifest(module_name).get("version") or "0"


def url_module_name(url):
    """Return the module name of a static URL like `/module/static/path`."""
    module_name, sep, __ = url.lstrip("/").partition("/static/")
    if not sep or not module_name or "/" in module_name:
        return None
    return module_name


def url_to_filepath(url):
    """Return the file path for a static URL like `/module/static/path`.

    Return None if the URL is not a static URL or the file does not exist.
    """
    module_name = url_module_name(url)
    if not module_name:
        return None
    path = url.lstrip("/").partition("/static/")[2]
    module_path = get_module_path(module_name, display_warning=False)
    if not module_path:
        return None
    filepath = safe_join(os.path.join(module_path, "static"), path.split("?")[0])
    if not filepath or not os.path.isfile(filepath):
        return None
    return filepath


def versioned_url(url, filepath=None):
    """Return given static URL with a version token based on file content.

    URLs that do not match a static file are returned untouched.
    """
    filepath = filepath or url_to_filepath(url)
    if not filepath:
        return url
    return f"{url}?v={file_token(filepath)}"


def module_js_files(module_name):
    """Yield `(url, filepath)` for every JS file in module's static folder."""
    module_path = get_module_path(module_name, display_warning=False)
    if not module_path:
        return
    static_path = os.path.join(module_path, "static")
    for root, dirs, files in os.walk(static_path):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for fname in sorted(files):
            if not fname.endswith(JS_EXTENSIONS):
                continue
            filepath = os.path.join(root, fname)
            rel_path = os.path.relpath(filepath, static_path).replace(os.sep, "/")
            yield f"/{module_name}/static/{rel_path}", filepath


def build_importmap(imports, overrides=(), versioner=versioned_url):
    """Build an import map.

    :param imports: dict `{url: versioned_url}`
    :param overrides: list of `(original_url, replacement_url)` tuples.
        Every import of `original_url` loads `replacement_url` instead.
        Inside the replacement, `original_url` still points to what it
        pointed to before the override, so that the replacement can import
        the original and extend it. Overrides are applied in order:
        when the same URL is overridden twice, the 2nd replacement
        gets the 1st one when importing the original URL.
    :param versioner: function returning the versioned URL of a replacement
        that is not part of `imports`.
    :return: dict ready to be dumped as JSON.
    """
    imports = dict(imports)
    scopes = {}
    for original, replacement in overrides:
        if original == replacement:
            continue
        target = imports.get(replacement) or versioner(replacement)
        scopes.setdefault(target, {})[original] = imports.get(original, original)
        imports[original] = target
        imports.setdefault(replacement, target)
    importmap = {"imports": imports}
    if scopes:
        importmap["scopes"] = scopes
    return importmap
