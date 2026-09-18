import { describe, expect, it } from "vitest";
import { formatCountdown, remainingMs, urgency } from "./time";

describe("countdown", () => {
  it("formats hours:minutes:seconds", () => {
    expect(formatCountdown(23 * 3600_000 + 59 * 60_000 + 12_000)).toBe("23:59:12");
    expect(formatCountdown(0)).toBe("00:00:00");
    expect(formatCountdown(72 * 3600_000)).toBe("72:00:00");
  });
  it("marks overdue with a minus", () => {
    expect(formatCountdown(-(1 * 3600_000 + 12 * 60_000 + 3_000))).toBe("-01:12:03");
  });
  it("computes remaining from a deadline", () => {
    const now = Date.parse("2026-09-18T10:00:00Z");
    expect(remainingMs("2026-09-19T10:00:00Z", now)).toBe(24 * 3600_000);
  });
  it("maps urgency thresholds", () => {
    expect(urgency(10 * 3600_000)).toBe("ok");
    expect(urgency(3 * 3600_000)).toBe("warn");
    expect(urgency(30 * 60_000)).toBe("critical");
    expect(urgency(-1)).toBe("overdue");
  });
});
