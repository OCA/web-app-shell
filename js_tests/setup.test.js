import {describe, expect, it} from "vitest";

describe("test setup", () => {
    it("runs the tests in node", () => {
        // Node provides EventTarget, the event hub is built on it
        expect(typeof EventTarget).toBe("function");
    });
});
