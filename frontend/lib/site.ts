// The site's public origin, for canonical URLs, Open Graph tags, robots and
// the sitemap. Vercel exposes the production domain to builds, so a deploy
// there needs no configuration; NEXT_PUBLIC_SITE_URL overrides it for a custom
// domain or any other host.
function resolve(): string {
  const explicit = process.env.NEXT_PUBLIC_SITE_URL;
  if (explicit) return explicit.replace(/\/$/, "");
  const vercel = process.env.VERCEL_PROJECT_PRODUCTION_URL ?? process.env.VERCEL_URL;
  if (vercel) return `https://${vercel}`;
  return "http://localhost:3000";
}

export const SITE_URL = resolve();
export const SITE_NAME = "StockSense AI";
export const SITE_TAGLINE = "Stock forecasts that show their work";
export const SITE_DESCRIPTION =
  "Every forecast comes with a confidence score, an expected price range, the factors behind it and a backtest you can run yourself. Educational use only, not financial advice.";
