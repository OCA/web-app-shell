## Expose the import map of an app

Inherit `app.shell.mixin.importmap` on the model describing your app and return
the modules providing the app's JS:

``` python
class MyApp(models.Model):
    _name = "my.app"
    _inherit = ["app.shell.mixin.importmap"]

    def get_app_js_root_modules(self):
        return ("my_app_frontend",)
```

The import map covers the JS files of the root modules (one or more) and
of all the installed modules depending on them, each one mapped to a
versioned URL. The method is called on the app record: the root modules
can depend on it.

Example, for `my_app_frontend`:

``` json
{
  "imports": {
    "/my_app_frontend/static/src/main.esm.js": "/my_app_frontend/static/src/main.esm.js?v=18.0.1.0.0"
  }
}
```

The map applies to every `import`, relative (`./foo.esm.js`) or absolute
(`/other_module/static/src/foo.esm.js`): every file is loaded from its
versioned URL, without any version in the code, and all the modules
importing the same file get the same instance of it.

The list of files is computed once per process (files change only on
deploy), or on every call in dev mode (`--dev`) so that new files are
picked up without restarting.

Pass the app record to the template of the app's page (eg: as `app`)
and render the import map in `<head>`, before any ES module, passing it
explicitly:

``` xml
<t t-call="app_shell_core.importmap">
    <t t-set="importmap" t-value="app.make_app_importmap()" />
</t>
<script type="module">
    import "/my_app_frontend/static/src/main.esm.js";
</script>
```

You decide which map is rendered: eg: one built or extended by your
own code.

Load ES modules with an inline module importing the plain URL (no
version): the import map does not apply to the `src` attribute. Classic
scripts and stylesheets get their versioned URL from
`get_app_static_url`:

``` xml
<link
    t-att-href="app.get_app_static_url('/my_app_frontend/static/src/main.css')"
    rel="stylesheet"
/>
```

## Versioning

`js_version_mode` decides the version appended to the URLs:

- **Module version** (default): the version of the module providing the
  file. No file is read. Files are downloaded again only when the module
  version changes. Override `get_app_js_module_version` for another
  policy (eg: a project version).
- **File content**: a hash of the content of each file, read once per
  worker process (until the file changes on disk).

## Replace a JS module

Override `get_app_js_overrides` to replace a module everywhere it is
imported. The replacement can still import the original URL to extend
it (via import map `scopes`), and must export the same names. When
several modules replace the same URL, each one gets the previous one.

## Browser support

Import maps are supported by Chrome/Edge 89+, Firefox 108+ and Safari
16.4+. Older browsers ignore the map: modules are loaded from their plain
URL, without versioning, and overrides are not applied.
