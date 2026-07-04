import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Private, auth-gated areas — nothing useful for crawlers.
      disallow: ["/dashboard", "/watchlist", "/compare", "/alerts", "/settings", "/stocks/"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
