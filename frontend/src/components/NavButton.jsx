import { useMemo } from "react";

/**
 * One-tap navigation button.
 * Detects iOS vs Android/other and opens Google Maps or Apple Maps accordingly.
 * Falls back to Google Maps if user agent detection is inconclusive.
 */
export default function NavButton({ lat, lng, address, label = "Navigate", compact = false }) {
  const url = useMemo(() => {
    if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
      return `https://maps.apple.com/?daddr=${lat},${lng}&dirflg=d`;
    }
    return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
  }, [lat, lng]);

  if (compact) {
    return (
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="nav-btn nav-btn-compact"
        title={`Navigate to ${address || `${lat},${lng}`}`}
        onClick={(e) => e.stopPropagation()}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="3 11 22 2 13 21 11 13 3 11" />
        </svg>
        <span>{label}</span>
      </a>
    );
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="nav-btn"
      title={`Navigate to ${address || `${lat},${lng}`}`}
      onClick={(e) => e.stopPropagation()}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="3 11 22 2 13 21 11 13 3 11" />
      </svg>
      <span>{label}</span>
    </a>
  );
}
