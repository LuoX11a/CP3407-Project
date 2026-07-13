---
layout: default
title: "US #8 — One-Tap Navigate to Carpark"
parent: Iteration 2
---

# User Story #8: One-Tap Navigate to Carpark

| Field | Detail |
|-------|--------|
| Priority | 10 |
| Estimated Days | 0.5 |
| Status | **Done** (Iteration 2 — #36) |
| Persona | Tan Wei Ming (Daily Commuter) |

## Story

> As a **driver who has found a carpark**, I want to **tap a single button to open turn-by-turn navigation** so that I can **drive directly there without manually typing the address into Google Maps**.

## Acceptance Criteria

- [x] Each carpark card has a "Navigate" button
- [x] On Android/Windows/Mac, tapping opens Google Maps with the carpark coordinates
- [x] On iOS (iPhone/iPad), tapping opens Apple Maps with the carpark coordinates
- [x] Button uses the carpark address as the link title for accessibility
- [x] Compact mode available for inline use (e.g., inside map popups)
- [x] Clicking the navigate button does not also select the carpark card

## Implementation

**Component**: `frontend/src/components/NavButton.jsx`

Uses `navigator.userAgent` detection for iOS vs. fallback. Generates:
- **Apple Maps**: `https://maps.apple.com/?daddr={lat},{lng}&dirflg=d`
- **Google Maps**: `https://www.google.com/maps/dir/?api=1&destination={lat},{lng}`

Integrated in `CarparkCard.jsx` footer and `MapView.jsx` popup content.

---

## Test Cases

### 1. Test for…

*…generating the correct Google Maps navigation URL on a non-iOS device.*

Get the NavButton component running in the vitest + jsdom test environment. Mock `navigator.userAgent` to return a standard Android user agent string (`"Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36"`). Render `<NavButton lat={1.3521} lng={103.8198} />` using React Testing Library. Find the rendered `<a>` element by its title text or role. Check that the `href` attribute equals `"https://www.google.com/maps/dir/?api=1&destination=1.3521,103.8198"`. Verify the link has `target="_blank"` and `rel="noopener noreferrer"` for security. Confirm the default label text is "Navigate".

*This is a grey-box test. You need to know the component uses `navigator.userAgent` to choose between Google Maps and Apple Maps URLs, and that the iOS detection regex is `/iPad|iPhone|iPod/`. The userAgent is mocked in jsdom via `Object.defineProperty`.*

**Android user taps Navigate → Google Maps opens with carpark as destination.**

---

### 2. Test for…

*…generating the correct Apple Maps navigation URL on an iOS device.*

Get the NavButton component running in the vitest + jsdom test environment. Mock `navigator.userAgent` to return an iPhone user agent string (`"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"`). Render `<NavButton lat={1.3521} lng={103.8198} address="Orchard Road" />`. Find the `<a>` element. Check that the `href` attribute equals `"https://maps.apple.com/?daddr=1.3521,103.8198&dirflg=d"`. Verify that the link's `title` attribute contains "Orchard Road" for accessibility. Confirm that clicking the link calls `e.stopPropagation()` — simulate a click event and verify it does not bubble to a parent element's click handler.

*This is a grey-box test. You need to know the Apple Maps URL scheme and that the component calls `e.stopPropagation()` to prevent the parent carpark card's onClick from firing simultaneously.*

**iPhone user taps Navigate → Apple Maps opens with driving directions.**

---

### 3. Test for…

*…rendering the compact variant for use inside map popups.*

Get the NavButton component running. Render `<NavButton lat={1.3521} lng={103.8198} compact={true} label="Get Directions" />`. Verify the rendered `<a>` element has the CSS class `nav-btn-compact`. Check that the SVG icon inside the button is 16×16 pixels (compact mode) rather than 18×18 (default mode). Confirm the custom label "Get Directions" is displayed instead of the default "Navigate". Verify the button still generates the correct Google Maps URL.

*This is a grey-box test. You need to know the two rendering paths in NavButton (compact vs. default) and the corresponding CSS classes. This test ensures the map popup variant renders correctly without taking too much space.*

**Compact button in map popup → smaller icon, custom label, same navigation URL.**
