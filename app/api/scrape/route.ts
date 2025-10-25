import { NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

export async function POST() {
  try {
    // Check if scraping is already running
    const isRunning = await checkScrapingStatus()
    if (isRunning) {
      return NextResponse.json({
        success: false,
        message: 'Scraping is already running'
      })
    }

    // Start the scraper in the background
    const scraperPath = path.join(process.cwd(), '..', 'scraper_marketplace_url.py')
    const scraper = spawn('python', [scraperPath], {
      detached: true,
      stdio: 'ignore'
    })
    
    // Unref to allow the process to continue after the API call ends
    scraper.unref()

    return NextResponse.json({
      success: true,
      message: 'Scraping started successfully'
    })
  } catch (error) {
    console.error('Error starting scraper:', error)
    return NextResponse.json({
      success: false,
      message: 'Failed to start scraping'
    })
  }
}

async function checkScrapingStatus(): Promise<boolean> {
  try {
    const { exec } = require('child_process')
    const util = require('util')
    const execAsync = util.promisify(exec)
    
    const { stdout } = await execAsync('tasklist /FI "IMAGENAME eq python.exe" /FO CSV')
    return stdout.includes('python.exe')
  } catch (error) {
    return false
  }
}
