const cron = require('node-cron')
const { spawn } = require('child_process')
const path = require('path')

const scraperPath = path.join(process.cwd(), 'scraper_marketplace_url.py')

function launchScraper(trigger) {
  const timestamp = new Date().toISOString()
  console.log(`[${timestamp}] ${trigger} - launching scraper at ${scraperPath}`)

  const scraper = spawn('python3', [scraperPath], {
    detached: true,
    stdio: 'pipe'
  })

  scraper.stdout.on('data', (data) => {
    process.stdout.write(`[scraper stdout] ${data}`)
  })

  scraper.stderr.on('data', (data) => {
    process.stderr.write(`[scraper stderr] ${data}`)
  })

  scraper.on('close', (code) => {
    console.log(`[${new Date().toISOString()}] Scraper process exited with code ${code}`)
  })

  scraper.on('error', (error) => {
    console.error(`[${new Date().toISOString()}] Failed to start scraper:`, error)
  })

  scraper.unref()
}

// Schedule scraping every 6 hours
cron.schedule('0 */6 * * *', () => launchScraper('Scheduled run'))

console.log('Scheduler started. Scraping will run every 6 hours.')
console.log('Next scheduled run:', new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString())

// Kick off an initial run immediately on startup
launchScraper('Initial run')
