import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  isInvitationActionable,
  getMemberDisplayName,
  formatLastActive,
  ORG_TYPE_LABELS,
  ORG_ROLE_LABELS,
  INVITATION_STATUS_LABELS,
  type Invitation,
  type Member,
} from "../user-types";

describe("isInvitationActionable", () => {
  it("returns true for pending invitation", () => {
    const inv = { status: "pending" } as Invitation;
    expect(isInvitationActionable(inv)).toBe(true);
  });

  it("returns false for accepted invitation", () => {
    const inv = { status: "accepted" } as Invitation;
    expect(isInvitationActionable(inv)).toBe(false);
  });

  it("returns false for expired invitation", () => {
    const inv = { status: "expired" } as Invitation;
    expect(isInvitationActionable(inv)).toBe(false);
  });

  it("returns false for revoked invitation", () => {
    const inv = { status: "revoked" } as Invitation;
    expect(isInvitationActionable(inv)).toBe(false);
  });
});

describe("getMemberDisplayName", () => {
  it("returns full_name when available", () => {
    const m = { full_name: "Shola", email: "shola@test.com" } as Member;
    expect(getMemberDisplayName(m)).toBe("Shola");
  });

  it("falls back to email when no name", () => {
    const m = { full_name: null, email: "shola@test.com" } as Member;
    expect(getMemberDisplayName(m)).toBe("shola@test.com");
  });

  it("returns Unknown when neither available", () => {
    const m = { full_name: null, email: null } as Member;
    expect(getMemberDisplayName(m)).toBe("Unknown");
  });
});

describe("formatLastActive", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-02-16T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns 'Never' for null", () => {
    expect(formatLastActive(null)).toBe("Never");
  });

  it("returns 'Today' for same day", () => {
    expect(formatLastActive("2026-02-16T10:00:00Z")).toBe("Today");
  });

  it("returns 'Yesterday' for 1 day ago", () => {
    expect(formatLastActive("2026-02-15T10:00:00Z")).toBe("Yesterday");
  });

  it("returns days ago for recent", () => {
    expect(formatLastActive("2026-02-10T10:00:00Z")).toBe("6d ago");
  });

  it("returns formatted date for old", () => {
    const result = formatLastActive("2025-12-01T10:00:00Z");
    expect(result).toContain("Dec");
    expect(result).toContain("2025");
  });
});

describe("label constants", () => {
  it("ORG_TYPE_LABELS has all 4 types", () => {
    expect(Object.keys(ORG_TYPE_LABELS)).toHaveLength(4);
  });

  it("ORG_ROLE_LABELS has all 4 roles", () => {
    expect(Object.keys(ORG_ROLE_LABELS)).toHaveLength(4);
  });

  it("INVITATION_STATUS_LABELS has all 4 statuses", () => {
    expect(Object.keys(INVITATION_STATUS_LABELS)).toHaveLength(4);
  });
});
