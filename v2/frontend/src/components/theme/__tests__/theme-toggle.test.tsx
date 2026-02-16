import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ThemeToggle } from "../theme-toggle";

const mockSetTheme = vi.fn();
let mockResolvedTheme = "light";

vi.mock("next-themes", () => ({
  useTheme: () => ({
    setTheme: mockSetTheme,
    resolvedTheme: mockResolvedTheme,
  }),
}));

describe("ThemeToggle", () => {
  it("renders a toggle button with accessible label", () => {
    render(<ThemeToggle />);
    expect(
      screen.getByRole("button", { name: /toggle theme/i }),
    ).toBeInTheDocument();
  });

  it("switches from light to dark on click", async () => {
    const user = userEvent.setup();
    mockResolvedTheme = "light";
    render(<ThemeToggle />);

    await user.click(screen.getByRole("button", { name: /toggle theme/i }));
    expect(mockSetTheme).toHaveBeenCalledWith("dark");
  });

  it("switches from dark to light on click", async () => {
    const user = userEvent.setup();
    mockResolvedTheme = "dark";
    render(<ThemeToggle />);

    await user.click(screen.getByRole("button", { name: /toggle theme/i }));
    expect(mockSetTheme).toHaveBeenCalledWith("light");
  });
});
