import { describe, expect, it } from "vitest";
import { getNavGroupsForRole, type UserRole } from "../navigation";

describe("getNavGroupsForRole", () => {
  it("returns all groups and all items for admin", () => {
    const groups = getNavGroupsForRole("admin");
    const allItems = groups.flatMap((g) => g.items);

    expect(groups).toHaveLength(3);
    expect(allItems.map((i) => i.name)).toEqual([
      "Dashboard",
      "Shipments",
      "Documents",
      "Compliance",
      "Analytics",
      "Users",
      "Organizations",
      "Settings",
    ]);
  });

  it("returns Operations + Compliance for compliance_officer", () => {
    const groups = getNavGroupsForRole("compliance_officer");
    const allItems = groups.flatMap((g) => g.items);

    expect(groups).toHaveLength(2);
    expect(groups.map((g) => g.label)).toEqual(["Operations", "Compliance"]);
    expect(allItems.map((i) => i.name)).toEqual([
      "Dashboard",
      "Shipments",
      "Documents",
      "Compliance",
      "Analytics",
    ]);
  });

  it("returns Operations only for logistics", () => {
    const groups = getNavGroupsForRole("logistics");
    const allItems = groups.flatMap((g) => g.items);

    expect(groups).toHaveLength(1);
    expect(groups[0]!.label).toBe("Operations");
    expect(allItems.map((i) => i.name)).toEqual([
      "Dashboard",
      "Shipments",
      "Documents",
    ]);
  });

  it("returns Dashboard + Shipments + Documents for buyer", () => {
    const groups = getNavGroupsForRole("buyer");
    const allItems = groups.flatMap((g) => g.items);

    expect(allItems.map((i) => i.name)).toEqual([
      "Dashboard",
      "Shipments",
      "Documents",
    ]);
  });

  it("returns Dashboard + Shipments + Documents for supplier", () => {
    const groups = getNavGroupsForRole("supplier");
    const allItems = groups.flatMap((g) => g.items);

    expect(allItems.map((i) => i.name)).toEqual([
      "Dashboard",
      "Shipments",
      "Documents",
    ]);
  });

  it("returns only Dashboard + Shipments for viewer", () => {
    const groups = getNavGroupsForRole("viewer");
    const allItems = groups.flatMap((g) => g.items);

    expect(groups).toHaveLength(1);
    expect(allItems.map((i) => i.name)).toEqual(["Dashboard", "Shipments"]);
  });

  it("filters out empty groups", () => {
    const roles: UserRole[] = [
      "admin",
      "compliance_officer",
      "logistics",
      "buyer",
      "supplier",
      "viewer",
    ];
    for (const role of roles) {
      const groups = getNavGroupsForRole(role);
      for (const group of groups) {
        expect(group.items.length).toBeGreaterThan(0);
      }
    }
  });
});
