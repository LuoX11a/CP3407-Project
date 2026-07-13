import { describe, it, expect, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import NavButton from "../components/NavButton";

// Save original userAgent
const originalUserAgent = navigator.userAgent;

describe("NavButton", () => {
  afterEach(() => {
    Object.defineProperty(navigator, "userAgent", {
      value: originalUserAgent,
      configurable: true,
    });
  });

  it("generates Google Maps URL on non-iOS devices", () => {
    Object.defineProperty(navigator, "userAgent", {
      value:
        "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
      configurable: true,
    });

    render(<NavButton lat={1.3521} lng={103.8198} />);

    // Title is "Navigate to 1.3521,103.8198" (no space after comma)
    const link = screen.getByTitle("Navigate to 1.3521,103.8198");
    expect(link.getAttribute("href")).toBe(
      "https://www.google.com/maps/dir/?api=1&destination=1.3521,103.8198"
    );
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
  });

  it("renders with custom label text", () => {
    render(
      <NavButton
        lat={1.3521}
        lng={103.8198}
        label="Get Directions"
        address="Orchard Road"
      />
    );

    // Title uses address when provided
    const link = screen.getByTitle("Navigate to Orchard Road");
    expect(link.textContent).toContain("Get Directions");
    expect(link.getAttribute("href")).toContain("google.com/maps/dir/");
  });

  it("renders compact variant with compact CSS class", () => {
    render(
      <NavButton lat={1.3521} lng={103.8198} compact={true} />
    );

    const link = screen.getByTitle("Navigate to 1.3521,103.8198");
    expect(link.className).toContain("nav-btn-compact");
    // Compact mode uses a 16x16 SVG icon
    const svg = link.querySelector("svg");
    expect(svg).toBeTruthy();
    expect(svg.getAttribute("width")).toBe("16");
    expect(svg.getAttribute("height")).toBe("16");
  });
});
