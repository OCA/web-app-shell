/**
 * Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
 * @author Simone Orsi <simone.orsi@camptocamp.com>
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
 */

/*
 * Global pub-sub of the app, in vanilla JS.
 *
 *   import event_hub from "/app_shell_core/static/src/services/event_hub.esm.js";
 *
 *   const handler = (data, other) => {...};
 *   event_hub.on("my:event", handler);
 *   event_hub.emit("my:event", data, other);
 *   event_hub.off("my:event", handler);
 *
 * A thin wrapper around the native `EventTarget`: no dependency, works the
 * same for Vue 2, Vue 3 or plain JS code. It used to be a Vue 2 instance,
 * whose events are gone in Vue 3.
 *
 * Semantics:
 * - a listener receives the arguments given to `emit`, in order;
 * - listeners run synchronously, in registration order; an error in one
 *   listener is reported and does not stop the others;
 * - event names are namespaced with `:`, eg: `login:success`,
 *   `bus:shopfloor.sync`; the $emit/$on/$once/$off aliases are deprecated.
 *
 * Like Vue events: listeners receive the arguments given to `emit` (not an
 * Event object) and are called synchronously, in registration order.
 */

class EventHub extends window.EventTarget {
    constructor() {
        super();
        // Event name -> list of {fn, wrapper}, to be able to remove listeners
        this._listeners = new Map();
    }

    /**
     * Emit an event.
     *
     * @param {String} name: event name
     * @param {...*} args: arguments passed to the listeners
     */
    emit(name, ...args) {
        this.dispatchEvent(new window.CustomEvent(name, {detail: args}));
    }

    /**
     * Listen to an event.
     *
     * @param {String} name: event name
     * @param {Function} fn: listener, called with the arguments of `emit`
     */
    on(name, fn) {
        this._add(name, fn, (event) => fn(...event.detail));
    }

    /**
     * Listen to the next occurrence of an event only.
     *
     * @param {String} name: event name
     * @param {Function} fn: listener, called with the arguments of `emit`
     */
    once(name, fn) {
        const wrapper = (event) => {
            this._remove(name, wrapper);
            fn(...event.detail);
        };
        this._add(name, fn, wrapper);
    }

    /**
     * Stop listening.
     *
     * @param {String} name: event name. If omitted, all listeners are removed.
     * @param {Function} fn: listener to remove.
     *  If omitted, all the listeners of the event are removed.
     */
    off(name, fn) {
        if (!name) {
            [...this._listeners.keys()].forEach((key) => this.off(key));
            return;
        }
        for (const entry of [...(this._listeners.get(name) || [])]) {
            if (!fn || entry.fn === fn) {
                this._remove(name, entry.wrapper);
            }
        }
    }

    /**
     * Check if an event has listeners.
     *
     * @param {String} name: event name
     * @returns {Boolean}
     */
    has_listeners(name) {
        return Boolean((this._listeners.get(name) || []).length);
    }

    _add(name, fn, wrapper) {
        if (!this._listeners.has(name)) {
            this._listeners.set(name, []);
        }
        this._listeners.get(name).push({fn, wrapper});
        this.addEventListener(name, wrapper);
    }

    _remove(name, wrapper) {
        const entries = (this._listeners.get(name) || []).filter(
            (entry) => entry.wrapper !== wrapper
        );
        if (entries.length) {
            this._listeners.set(name, entries);
        } else {
            this._listeners.delete(name);
        }
        this.removeEventListener(name, wrapper);
    }

    // Deprecated: Vue 2 instance API, kept for modules not adapted yet.
    // To be removed in the next major version.

    $emit(name, ...args) {
        this.emit(name, ...args);
    }

    $on(name, fn) {
        this.on(name, fn);
    }

    $once(name, fn) {
        this.once(name, fn);
    }

    $off(name, fn) {
        this.off(name, fn);
    }
}

export default new EventHub();
