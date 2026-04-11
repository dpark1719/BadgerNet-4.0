/**
 * URL for files in Vite `public/` (e.g. `/data/*.json`), honoring `base` in vite.config.
 * Use for fetch(); keeps the app working when deployed under a subpath (GitHub Pages, etc.).
 */
export function publicPath(relativeToPublic: string): string {
  const base = import.meta.env.BASE_URL
  const path = relativeToPublic.replace(/^\/+/, '')
  return `${base}${path}`
}
