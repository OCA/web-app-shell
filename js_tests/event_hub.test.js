// @vitest-environment jsdom
import {afterEach, describe, expect, it, vi} from "vitest";

import event_hub from "../app_shell_core/static/src/services/event_hub.esm.js";

afterEach(() => {
    // The hub is a singleton: each test starts with no listener
    event_hub.off();
});

describe("event hub", () => {
    it("calls listeners with the arguments given to emit, in order", () => {
        const listener = vi.fn();
        event_hub.on("user:login", listener);
        event_hub.emit("user:login", "alice", {profile: 1});
        expect(listener).toHaveBeenCalledWith("alice", {profile: 1});
    });

    it("calls listeners in registration order", () => {
        const calls = [];
        event_hub.on("step", () => calls.push("first"));
        event_hub.on("step", () => calls.push("second"));
        event_hub.emit("step");
        expect(calls).toEqual(["first", "second"]);
    });

    it("does not call listeners of another event", () => {
        const listener = vi.fn();
        event_hub.on("login:success", listener);
        event_hub.emit("logout:success");
        expect(listener).not.toHaveBeenCalled();
    });

    it("calls a listener on every emit", () => {
        const listener = vi.fn();
        event_hub.on("tick", listener);
        event_hub.emit("tick");
        event_hub.emit("tick");
        expect(listener).toHaveBeenCalledTimes(2);
    });

    it("calls a once listener only for the next emit", () => {
        const listener = vi.fn();
        event_hub.once("boot", listener);
        event_hub.emit("boot", 1);
        event_hub.emit("boot", 2);
        expect(listener).toHaveBeenCalledTimes(1);
        expect(listener).toHaveBeenCalledWith(1);
    });

    it("stops calling a listener removed with off", () => {
        const listener = vi.fn();
        event_hub.on("tick", listener);
        event_hub.off("tick", listener);
        event_hub.emit("tick");
        expect(listener).not.toHaveBeenCalled();
    });

    it("removes only the given listener with off", () => {
        const removed = vi.fn();
        const kept = vi.fn();
        event_hub.on("tick", removed);
        event_hub.on("tick", kept);
        event_hub.off("tick", removed);
        event_hub.emit("tick");
        expect(removed).not.toHaveBeenCalled();
        expect(kept).toHaveBeenCalledTimes(1);
    });

    it("removes all the listeners of an event when off gets no listener", () => {
        const first = vi.fn();
        const second = vi.fn();
        const other = vi.fn();
        event_hub.on("tick", first);
        event_hub.on("tick", second);
        event_hub.on("tock", other);
        event_hub.off("tick");
        event_hub.emit("tick");
        event_hub.emit("tock");
        expect(first).not.toHaveBeenCalled();
        expect(second).not.toHaveBeenCalled();
        expect(other).toHaveBeenCalledTimes(1);
    });

    it("removes the listeners of all events when off gets no argument", () => {
        const listener = vi.fn();
        event_hub.on("tick", listener);
        event_hub.on("tock", listener);
        event_hub.off();
        expect(event_hub.has_listeners("tick")).toBe(false);
        expect(event_hub.has_listeners("tock")).toBe(false);
    });

    it("removes a once listener with off before it is called", () => {
        const listener = vi.fn();
        event_hub.once("boot", listener);
        event_hub.off("boot", listener);
        event_hub.emit("boot");
        expect(listener).not.toHaveBeenCalled();
    });

    it("tells if an event has listeners", () => {
        expect(event_hub.has_listeners("tick")).toBe(false);
        const listener = vi.fn();
        event_hub.on("tick", listener);
        expect(event_hub.has_listeners("tick")).toBe(true);
        event_hub.off("tick", listener);
        expect(event_hub.has_listeners("tick")).toBe(false);
    });

    it("calls the listener of each registration when the same function is registered twice", () => {
        const listener = vi.fn();
        event_hub.on("tick", listener);
        event_hub.on("tick", listener);
        event_hub.emit("tick");
        expect(listener).toHaveBeenCalledTimes(2);
    });

    it("keeps calling the other listeners when one of them throws", () => {
        const after = vi.fn();
        // In jsdom, the error of a listener is reported instead of thrown
        const onError = (event) => event.preventDefault();
        window.addEventListener("error", onError);
        event_hub.on("tick", () => {
            throw new Error("boom");
        });
        event_hub.on("tick", after);
        try {
            event_hub.emit("tick");
        } finally {
            window.removeEventListener("error", onError);
        }
        expect(after).toHaveBeenCalledTimes(1);
    });

    it("keeps the deprecated Vue 2 aliases working", () => {
        const listener = vi.fn();
        event_hub.$on("tick", listener);
        event_hub.$emit("tick", "a");
        event_hub.$off("tick", listener);
        event_hub.$emit("tick", "b");
        expect(listener).toHaveBeenCalledTimes(1);
        expect(listener).toHaveBeenCalledWith("a");
    });
});
