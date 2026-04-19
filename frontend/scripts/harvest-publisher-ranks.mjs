/**
 * Optional Playwright probe for publisher pages (US News / Niche).
 * Often blocked (CAPTCHA, HTTP/2, bot walls). Does not write files by default.
 *
 *   cd frontend && node scripts/harvest-publisher-ranks.mjs
 *
 * If you capture ranks manually, prefer data/raw/major_ranks.csv + npm run harvest:rankings
 */
import { chromium } from 'playwright'

const urls = [
  ['usnews-college', 'https://www.usnews.com/best-colleges/university-of-wisconsin-madison-3895'],
  ['niche-uw', 'https://www.niche.com/colleges/university-of-wisconsin-madison/'],
]

const browser = await chromium.launch({
  headless: true,
  args: ['--disable-http2'],
})
const page = await browser.newPage()
const out = []

for (const [id, url] of urls) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 })
    await page.waitForTimeout(4000)
    const title = await page.title()
    const snippet = (await page.innerText('body')).slice(0, 400).replace(/\s+/g, ' ')
    out.push({ id, url, title, snippet })
  } catch (e) {
    out.push({ id, url, error: String(e.message || e) })
  }
}

await browser.close()
console.log(JSON.stringify({ note: 'probe_only', results: out }, null, 2))
