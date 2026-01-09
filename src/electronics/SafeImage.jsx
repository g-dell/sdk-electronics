import React, { useState, useRef } from "react";

/**
 * Safe image component that handles loading errors gracefully.
 * 
 * Features:
 * - Automatically retries failed images through proxy endpoint (solves ORB/CORS issues)
 * - Falls back to placeholder when image fails to load
 * - Uses standard img tag to ensure onError handler works correctly
 * 
 * The proxy endpoint (/proxy-image) is used when:
 * - The original image fails to load (likely due to ORB/CORS blocking)
 * - The image URL is external (not a data URI or relative path)
 */
export default function SafeImage({ src, alt, className, fallbackSrc, proxyBaseUrl, ...props }) {
  const [hasError, setHasError] = useState(false);
  const [imageSrc, setImageSrc] = useState(src);
  const [retryCount, setRetryCount] = useState(0);
  const imgRef = useRef(null);

  /**
   * Determines the base URL for the proxy endpoint.
   * Tries multiple strategies to find the server URL.
   */
  const getProxyBaseUrl = () => {
    // If explicitly provided, use it
    if (proxyBaseUrl) {
      return proxyBaseUrl;
    }

    // Try to get from window.location (works in same-origin contexts)
    if (typeof window !== "undefined" && window.location) {
      const origin = window.location.origin;
      // Only use if it's not a data URI or blob URL
      if (origin && !origin.startsWith("data:") && !origin.startsWith("blob:")) {
        return origin;
      }
    }

    // Try to deduce from script sources (for widgets loaded from server)
    if (typeof document !== "undefined") {
      const scripts = document.getElementsByTagName("script");
      for (let script of scripts) {
        if (script.src) {
          try {
            const url = new URL(script.src);
            return url.origin;
          } catch (e) {
            // Invalid URL, skip
          }
        }
      }
    }

    // Fallback: return empty string (will use relative URL)
    return "";
  };

  /**
   * Builds the proxy URL for an image.
   */
  const buildProxyUrl = (imageUrl) => {
    const base = getProxyBaseUrl();
    const encodedUrl = encodeURIComponent(imageUrl);
    return `${base}/proxy-image?url=${encodedUrl}`;
  };

  /**
   * Checks if an URL is external (needs proxy) or local.
   */
  const isExternalUrl = (url) => {
    if (!url || url.startsWith("data:") || url.startsWith("blob:")) {
      return false;
    }
    // If it's a relative URL (starts with / or ./), it's local
    if (url.startsWith("/") || url.startsWith("./") || url.startsWith("../")) {
      return false;
    }
    // If it has a protocol, it's external
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const handleError = () => {
    // If we haven't tried the proxy yet and the URL is external, try proxy
    if (retryCount === 0 && isExternalUrl(src) && !hasError) {
      const proxyUrl = buildProxyUrl(src);
      setRetryCount(1);
      setImageSrc(proxyUrl);
      return;
    }

    // If proxy also failed or we've already tried, use fallback
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
    setRetryCount(0);
    setImageSrc(src);
  }, [src]);

  return (
    <img
      ref={imgRef}
      src={imageSrc}
      alt={alt}
      className={className}
      onError={handleError}
      loading="lazy"
      {...props}
    />
  );
}
