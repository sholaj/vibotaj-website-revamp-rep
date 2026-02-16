import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LoadingState } from "../loading-state";

describe("LoadingState", () => {
  it("renders table skeleton by default", () => {
    const { container } = render(<LoadingState />);
    // Should have skeleton elements (divs with specific classes)
    const skeletons = container.querySelectorAll(
      '[class*="skeleton"], [data-slot="skeleton"]',
    );
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("renders specified number of rows for table variant", () => {
    const { container } = render(<LoadingState variant="table" rows={3} />);
    // 1 header row + 3 data rows = 4 row divs
    const rows = container.querySelectorAll(".space-y-3 > div.flex");
    expect(rows).toHaveLength(4);
  });

  it("renders card skeletons", () => {
    const { container } = render(<LoadingState variant="cards" rows={6} />);
    const cards = container.querySelectorAll(".rounded-lg.border");
    expect(cards).toHaveLength(6);
  });

  it("renders detail skeleton", () => {
    const { container } = render(<LoadingState variant="detail" />);
    // Should have grid layout for detail view
    const grid = container.querySelector(".grid");
    expect(grid).not.toBeNull();
  });
});
