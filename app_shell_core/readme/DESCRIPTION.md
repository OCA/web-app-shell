Core tools to publish single page apps (SPA) from Odoo, without Odoo's
web client and assets bundles: the app is made of plain ES modules served
from the `static` folder of its modules.

This first version provides the event hub: a framework-free publish and
subscribe service for the app's JS modules, with its unit tests. The other
tools come in the next versions, see the roadmap.
