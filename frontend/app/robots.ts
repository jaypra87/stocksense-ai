import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";


export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Private, auth-gated areas. Nothing useful for crawlers.
      disallow: ["/dashboard", "/watchlist", "/compare", "/alerts", "/settings", "/stocks/"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
