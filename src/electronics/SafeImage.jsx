import React, { useState, useRef } from "react";
import { config } from "../config";

/**
 * Safe image component that handles loading errors gracefully.
 * 
 * Features:
 * - Automatically retries failed images through proxy endpoint (solves ORB/CORS issues)
 * - Falls back to placeholder when image fails to load
 * - Uses standard img tag to ensure onError handler works correctly
 * - Extensive logging for debugging proxy URL resolution
 * 
 * The proxy endpoint (/proxy-image) is used when:
 * - The original image fails to load (likely due to ORB/CORS blocking)
 * - The image URL is external (not a data URI or relative path)
 * 
 * Props:
 * - proxyBaseUrl: Optional explicit server base URL. If not provided, uses global config.
 */
export default function SafeImage({ src, alt, className, fallbackSrc, proxyBaseUrl, ...props }) {
  const [hasError, setHasError] = useState(false);
  const [imageSrc, setImageSrc] = useState(src);
  const [retryCount, setRetryCount] = useState(0);
  const imgRef = useRef(null);

  /**
   * Determines the base URL for the proxy endpoint.
   * Tries multiple strategies to find the server URL with detailed logging.
   */
  const getProxyBaseUrl = () => {
    console.log("[SafeImage] Resolving proxy base URL...");
    
    // If explicitly provided, use it
    if (proxyBaseUrl) {
      console.log("[SafeImage] Using explicit proxyBaseUrl prop:", proxyBaseUrl);
      return proxyBaseUrl;
    }

    // Use global config (which has its own logging)
    const baseUrl = config.serverBaseUrl;
    if (baseUrl) {
      console.log("[SafeImage] Using global config serverBaseUrl:", baseUrl);
      return baseUrl;
    }

    // Fallback: try window.location
    if (typeof window !== "undefined" && window.location) {
      const origin = window.location.origin;
      if (origin && !origin.startsWith("data:") && !origin.startsWith("blob:")) {
        console.log("[SafeImage] Using window.location.origin as fallback:", origin);
        return origin;
      } else {
        console.warn("[SafeImage] window.location.origin is invalid:", origin);
      }
    }

    // Last resort: empty string (relative URL)
    console.warn("[SafeImage] No proxy base URL found, will use relative URL");
    return "";
  };

  /**
   * Builds the proxy URL for an image.
   */
  const buildProxyUrl = (imageUrl) => {
    const base = getProxyBaseUrl();
    const encodedUrl = encodeURIComponent(imageUrl);
    const proxyUrl = base ? `${base}/proxy-image?url=${encodedUrl}` : `/proxy-image?url=${encodedUrl}`;
    console.log("[SafeImage] Built proxy URL:", proxyUrl, "for original image:", imageUrl);
    return proxyUrl;
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

  const handleError = (errorEvent) => {
    console.log("[SafeImage] Image load error for:", imageSrc, {
      retryCount,
      hasError,
      isExternal: isExternalUrl(src),
      originalSrc: src,
    });

    // If we haven't tried the proxy yet and the URL is external, try proxy
    if (retryCount === 0 && isExternalUrl(src) && !hasError) {
      console.log("[SafeImage] Attempting proxy retry for external image:", src);
      const proxyUrl = buildProxyUrl(src);
      setRetryCount(1);
      setImageSrc(proxyUrl);
      return;
    }

    // If proxy also failed or we've already tried, use fallback
    if (retryCount > 0) {
      console.error("[SafeImage] Proxy also failed for image:", src, "Proxy URL was:", imageSrc);
    }

    if (!hasError && fallbackSrc) {
      console.log("[SafeImage] Using fallback image:", fallbackSrc);
      setHasError(true);
      setImageSrc(fallbackSrc);
    } else if (!hasError) {
      console.warn("[SafeImage] No fallback available, showing placeholder for:", src);
      // If no fallback provided, use a data URI placeholder
      setHasError(true);
      setImageSrc(
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Crect fill='%23f3f4f6' width='400' height='400'/%3E%3Ctext fill='%239ca3af' font-family='sans-serif' font-size='18' x='50%25' y='50%25' text-anchor='middle' dy='.3em'%3EImage not available%3C/text%3E%3C/svg%3E"
      );
    }
  };

  // Reset error state if src changes
  React.useEffect(() => {
    console.log("[SafeImage] Image src changed to:", src);
    setHasError(false);
    setRetryCount(0);
    setImageSrc(src);
  }, [src]);

  // Log initial render info
  React.useEffect(() => {
    console.log("[SafeImage] Component mounted with src:", src, {
      proxyBaseUrl,
      isExternal: isExternalUrl(src),
      resolvedBaseUrl: getProxyBaseUrl(),
    });
  }, []);

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
