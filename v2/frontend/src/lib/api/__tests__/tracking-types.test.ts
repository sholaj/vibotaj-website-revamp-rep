import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { formatRelativeTime } from "../tracking-types";

describe("formatRelativeTime", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-02-16T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns 'just now' for less than 1 minute", () => {
    expect(formatRelativeTime("2026-02-16T11:59:30Z")).toBe("just now");
  });

  it("returns minutes ago", () => {
    expect(formatRelativeTime("2026-02-16T11:45:00Z")).toBe("15m ago");
  });

  it("returns hours ago", () => {
    expect(formatRelativeTime("2026-02-16T09:00:00Z")).toBe("3h ago");
  });

  it("returns days ago", () => {
    expect(formatRelativeTime("2026-02-13T12:00:00Z")).toBe("3d ago");
  });

  it("returns months ago", () => {
    expect(formatRelativeTime("2025-12-16T12:00:00Z")).toBe("2mo ago");
  });

  it("returns years ago", () => {
    expect(formatRelativeTime("2024-02-16T12:00:00Z")).toBe("2y ago");
  });
});
