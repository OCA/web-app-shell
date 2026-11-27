# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, tools

from .. import importmap


class AppShellImportmapMixin(models.AbstractModel):
    """Publish the JS modules of a single page app via an import map.

    Inherit this mixin on the model describing your app (eg: `shopfloor.app`)
    and implement `get_app_js_root_modules` to return the modules providing
    the app's JS: the import map covers them and all the installed modules
    depending on them.
    """

    _name = "app.shell.mixin.importmap"
    _description = "App shell: single page app"

    js_version_mode = fields.Selection(
        selection=[
            ("module", "Module version"),
            ("file", "File content"),
        ],
        string="JS version mode",
        default="module",
        required=True,
        help="Version appended to the URL of the app's static files "
        "to bust browser cache.\n"
        "* Module version: the version of the Odoo module providing the file. "
        "Fast, but files are refreshed only when the module version changes.\n"
        "* File content: a hash of the content of each file. "
        "Files are refreshed as soon as they change, "
        "but each file is read once per worker.",
    )

    def get_app_js_root_modules(self):
        """Return the names of the modules providing the JS of the app.

        Required: implement it on the model inheriting the mixin.
        The import map covers these modules and all the installed modules
        depending on them. The result can depend on the app record.

        :return: tuple of module names
        """
        raise NotImplementedError(
            f"`get_app_js_root_modules` is not implemented on `{self._name}`"
        )

    def _app_js_roots_key(self):
        """Return the root modules as a stable cache key."""
        return tuple(sorted(set(self.get_app_js_root_modules())))

    def _get_app_js_module_names(self):
        """Return the names of the modules providing JS files to the app.

        These are the root modules and all the installed modules
        depending on them, directly or indirectly.
        """
        return self._get_app_js_module_names_for(self._app_js_roots_key())

    @api.model
    @tools.ormcache("root_modules")
    def _get_app_js_module_names_for(self, root_modules):
        """Return the root modules and the installed modules depending on them."""
        roots = (
            self.env["ir.module.module"]
            .sudo()
            .search([("name", "in", list(root_modules))])
        )
        return tuple(sorted((roots | roots.downstream_dependencies()).mapped("name")))

    def _get_app_js_file_list(self):
        """Return `(url, filepath)` for every JS file the app can import.

        The list is computed once per process (files change only on deploy),
        except in dev mode where new files must be picked up right away.
        """
        root_modules = self._app_js_roots_key()
        if tools.config.get("dev_mode"):
            return self._collect_app_js_files(root_modules)
        return self._get_app_js_file_list_cached(root_modules)

    @api.model
    @tools.ormcache("root_modules")
    def _get_app_js_file_list_cached(self, root_modules):
        """Cached version of `_collect_app_js_files`."""
        return self._collect_app_js_files(root_modules)

    @api.model
    def _collect_app_js_files(self, root_modules):
        """Return `(url, filepath)` for the JS files of the app's modules."""
        res = []
        for module_name in self._get_app_js_module_names_for(root_modules):
            res.extend(importmap.module_js_files(module_name))
        return tuple(res)

    def get_app_js_module_version(self, module_name):
        """Return the version used for the static files of given module.

        Override to use your own versioning policy (eg: project version).
        """
        return importmap.module_version(module_name)

    def get_app_static_url(self, url):
        """Return the versioned URL of a static file of the app's modules.

        Public and callable from the templates. Only the URL is taken: the file
        is looked up inside the static folder of its module, so no path given
        by a caller is ever read.
        """
        return self._static_url(url)

    def _static_url(self, url, filepath=None):
        """Return given static URL with a version, according to `js_version_mode`.

        URLs that are not static URLs (`/module/static/...`) are returned
        untouched, as well as URLs of missing files in `file` mode.
        Use it for classic scripts and stylesheets, eg:
        `<link t-att-href="app.get_app_static_url('/mod/static/src/main.css')" />`.
        """
        if self.js_version_mode == "file":
            return importmap.versioned_url(url, filepath)
        module_name = importmap.url_module_name(url)
        if not module_name:
            return url
        return f"{url}?v={self.get_app_js_module_version(module_name)}"

    def _get_app_js_files(self):
        """Return `{url: versioned_url}` for every JS file the app can import."""
        return {
            url: self._static_url(url, filepath)
            for url, filepath in self._get_app_js_file_list()
        }

    def get_app_js_overrides(self):
        """Return the JS modules to replace in the app.

        Override this method to replace a JS module of the app with your own.
        Every `import` of the original module, from any module,
        loads the replacement instead.

        The replacement can import the original URL to extend it,
        and it must export the same names, eg:

            def get_app_js_overrides(self):
                res = super().get_app_js_overrides()
                res.append(
                    (
                        "/root_module/static/src/services/registry.esm.js",
                        "/my_module/static/src/services/registry.esm.js",
                    )
                )
                return res

        Always append to the result of `super()`: when several modules
        replace the same URL, each replacement gets the previous one
        when importing the original URL.

        :return: list of `(original_url, replacement_url)` tuples.
        """
        return []

    def make_app_importmap(self):
        """Return the import map of the app, ready to be dumped as JSON.

        Render it with `app_shell_core.importmap`, eg:

            <t t-call="app_shell_core.importmap">
                <t t-set="importmap" t-value="app.make_app_importmap()" />
            </t>
        """
        return importmap.build_importmap(
            self._get_app_js_files(),
            self.get_app_js_overrides(),
            versioner=self._static_url,
        )
