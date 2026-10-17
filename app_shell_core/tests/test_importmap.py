# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
import re
import tempfile

from odoo.tests.common import TransactionCase

from odoo.addons.app_shell_core import importmap

# Static files of `bus`, always available on disk, used as fixtures
WORKER_URL = "/bus/static/src/workers/websocket_worker.js"
UTILS_URL = "/bus/static/src/workers/websocket_worker_utils.js"
SCRIPT_URL = "/bus/static/src/workers/websocket_worker_script.js"
TOKEN_RE = re.compile(r"\?v=[0-9a-f]{12}$")


class TestImportmapTools(TransactionCase):
    def test_file_token(self):
        """The token is a short hash of the content, changing with it."""
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fd:
            fd.write("export const a = 1;")
        self.addCleanup(os.unlink, fd.name)
        token = importmap.file_token(fd.name)
        self.assertEqual(len(token), 12)
        self.assertEqual(importmap.file_token(fd.name), token)
        with open(fd.name, "w") as fd2:
            fd2.write("export const a = 2; // changed")
        self.assertNotEqual(importmap.file_token(fd.name), token)

    def test_module_version(self):
        """The module version comes from the manifest."""
        self.assertEqual(
            importmap.module_version("app_shell_core"),
            importmap.get_manifest("app_shell_core")["version"],
        )

    def test_url_module_name(self):
        """The module name is read from static URLs only."""
        self.assertEqual(importmap.url_module_name(WORKER_URL), "bus")
        self.assertIsNone(importmap.url_module_name("/web/login"))

    def test_versioned_url(self):
        """Static files get a content token, other URLs are untouched."""
        self.assertRegex(importmap.versioned_url(WORKER_URL), TOKEN_RE)
        # Not existing file, not a static URL, path traversal: untouched
        for url in (
            "/bus/static/src/nope.js",
            "/web/login",
            "/bus/static/../__manifest__.py",
        ):
            self.assertEqual(importmap.versioned_url(url), url)

    def test_module_js_files(self):
        """All the JS files of the module are listed, except tests."""
        urls = dict(importmap.module_js_files("bus"))
        self.assertIn(WORKER_URL, urls)
        self.assertIn(UTILS_URL, urls)
        for url in urls:
            self.assertTrue(url.endswith((".js", ".mjs")), url)
            self.assertNotIn("/static/tests/", url)
            self.assertNotIn("/static/description/", url)
        self.assertEqual(list(importmap.module_js_files("not_a_module")), [])

    def test_build_importmap_no_override(self):
        """Without overrides, the map is the given imports."""
        imports = {WORKER_URL: WORKER_URL + "?v=1"}
        self.assertEqual(importmap.build_importmap(imports), {"imports": imports})

    def test_build_importmap_override(self):
        """Imports of the original get the replacement, which gets the original."""
        imports = {
            WORKER_URL: WORKER_URL + "?v=1",
            UTILS_URL: UTILS_URL + "?v=2",
        }
        res = importmap.build_importmap(imports, [(WORKER_URL, UTILS_URL)])
        self.assertEqual(res["imports"][WORKER_URL], UTILS_URL + "?v=2")
        self.assertEqual(
            res["scopes"], {UTILS_URL + "?v=2": {WORKER_URL: WORKER_URL + "?v=1"}}
        )
        # Input not modified
        self.assertEqual(imports[WORKER_URL], WORKER_URL + "?v=1")

    def test_build_importmap_override_chain(self):
        """Each replacement of the same URL gets the previous one."""
        imports = {
            WORKER_URL: WORKER_URL + "?v=1",
            UTILS_URL: UTILS_URL + "?v=2",
            SCRIPT_URL: SCRIPT_URL + "?v=3",
        }
        res = importmap.build_importmap(
            imports, [(WORKER_URL, UTILS_URL), (WORKER_URL, SCRIPT_URL)]
        )
        self.assertEqual(res["imports"][WORKER_URL], SCRIPT_URL + "?v=3")
        self.assertEqual(
            res["scopes"],
            {
                UTILS_URL + "?v=2": {WORKER_URL: WORKER_URL + "?v=1"},
                SCRIPT_URL + "?v=3": {WORKER_URL: UTILS_URL + "?v=2"},
            },
        )

    def test_build_importmap_override_not_mapped(self):
        """A replacement outside of the imports is versioned anyway."""
        res = importmap.build_importmap({}, [(WORKER_URL, UTILS_URL)])
        self.assertRegex(res["imports"][WORKER_URL], TOKEN_RE)
        self.assertEqual(res["imports"][UTILS_URL], res["imports"][WORKER_URL])

    def test_build_importmap_custom_versioner(self):
        """The versioner given is used for replacements outside of the imports."""
        res = importmap.build_importmap(
            {}, [(WORKER_URL, UTILS_URL)], versioner=lambda url: url + "?v=x"
        )
        self.assertEqual(res["imports"][WORKER_URL], UTILS_URL + "?v=x")
