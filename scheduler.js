const cron = require('node-cron')
const { spawn } = require('child_process')
const path = require('path')

// Schedule scraping every 6 hours
cron.schedule('0 */6 * * *', () => {
  console.log('Starting scheduled scraping at', new Date().toISOString())
  
  const scraperPath = path.join(__dirname, 'scraper_marketplace_url.py')
  const scraper = spawn('python', [scraperPath], {
    detached: true,
    stdio: 'pipe'
  })
  
  scraper.stdout.on('data', (data) => {
    console.log(`Scraper stdout: ${data}`)
  })
  
  scraper.stderr.on('data', (data) => {
    console.error(`Scraper stderr: ${data}`)
  })
  
  scraper.on('close', (code) => {
    console.log(`Scraper process exited with code ${code}`)
  })
  
  // Unref to allow the process to continue independently
  scraper.unref()
})

console.log('Scheduler started. Scraping will run every 6 hours.')
console.log('Next scheduled run:', new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString())
