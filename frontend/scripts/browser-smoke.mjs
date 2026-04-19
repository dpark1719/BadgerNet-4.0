/**
 * Headless smoke: landing → main app → Industry charts render without errors.
 * Requires: npm install && npx playwright install chromium
 * With dev server on 127.0.0.1:5173: npm run smoke
 */
import { chromium } from 'playwright'

const base = process.env.SMOKE_URL ?? 'http://localhost:5173'
const issues = []

const browser = await chromium.launch({ headless: true })
const page = await browser.newPage()
page.on('pageerror', (e) => issues.push(`pageerror: ${e.message}`))
page.on('console', (msg) => {
  if (msg.type() === 'error') issues.push(`console: ${msg.text()}`)
})

await page.goto(base, { waitUntil: 'networkidle', timeout: 60000 })
await page.getByRole('button', { name: 'Explore the data' }).click()
await page.waitForSelector('nav.tabs', { timeout: 30000 })
await page.waitForSelector('.charts', { timeout: 30000 })
await page.waitForSelector('.chart-wrap, .bar-panel, .sankey-panel', {
  timeout: 30000,
})

const banners = await page.locator('.banner.error').count()
if (banners > 0) issues.push(`error banners visible: ${banners}`)

await browser.close()

if (issues.length) {
  console.error('browser-smoke FAILED')
  for (const line of issues) console.error(line)
  process.exit(1)
}
console.log('browser-smoke OK', base)
