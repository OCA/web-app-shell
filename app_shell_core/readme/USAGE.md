## Event hub

`static/src/services/event_hub.esm.js` exports the app's event hub, a single
instance shared by every module that imports it:

```js
import event_hub from "/app_shell_core/static/src/services/event_hub.esm.js";

const on_login = (user, profile) => {...};
event_hub.on("login:success", on_login);
event_hub.emit("login:success", user, profile);
event_hub.off("login:success", on_login);
```

- Listeners receive the arguments given to `emit`, in order, not an `Event`
  object.
- Listeners run synchronously, in registration order. An error in one
  listener is reported and does not stop the others.
- `once` listens to the next occurrence only, `off(name)` removes every
  listener of an event, `off()` removes them all, and `has_listeners(name)`
  tells whether an event has listeners.
- Event names are namespaced with `:`, eg: `login:success`.
- It's a thin wrapper around the native `EventTarget`: no dependency, the
  same for Vue 2, Vue 3 or plain JS code.
- The `$emit`, `$on`, `$once` and `$off` aliases of the former Vue 2 based
  hub still work, but are deprecated.
