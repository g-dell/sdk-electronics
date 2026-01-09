import React, { useState } from "react";

/**
 * Safe image component that handles loading errors gracefully.
 * Falls back to a placeholder when image fails to load (e.g., ORB blocking, 404, etc.)
 * Uses standard img tag to ensure onError handler works correctly.
 */
export default function SafeImage({ src, alt, className, fallbackSrc, ...props }) {
  const [hasError, setHasError] = useState(false);
  const [imageSrc, setImageSrc] = useState(src);

  const handleError = () => {
    if (!hasError && fallbackSrc) {
      setHasError(true);
      setImageSrc(fallbackSrc);
    } else if (!hasError) {
      // If no fallback provided, use a data URI placeholder
      setHasError(true);
      setImageSrc(
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Crect fill='%23f3f4f6' width='400' height='400'/%3E%3Ctext fill='%239ca3af' font-family='sans-serif' font-size='18' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3EImage not available%3C/text%3E%3C/svg%3E"
      );
    }
  };

  // Reset error state if src changes
  React.useEffect(() => {
    setHasError(false);
    setImageSrc(src);
  }, [src]);

  return (
    <img
      src={imageSrc}
      alt={alt}
      className={className}
      onError={handleError}
      loading="lazy"
      {...props}
    />
  );
}
