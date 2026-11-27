Core tools to publish single page apps (SPA) from Odoo, without Odoo's
web client and assets bundles: the app is made of plain ES modules served
from the `static` folder of its modules.

This first version provides the loading of the app's JS via an
[import map](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/script/type/importmap):

- every JS file of the app is loaded from a versioned URL (module version
  or hash of the content), so that a file is downloaded again only when it
  changes, with no version to put in the code;
- every module is loaded from a single URL, hence a single instance, no
  matter how it's imported (relative or absolute path);
- any JS module can be replaced by another one server side, everywhere it
  is imported.

It's exposed by `app.shell.mixin.importmap`, to inherit on the model describing your
app. It's the first piece of a generic "app shell", see the roadmap.
