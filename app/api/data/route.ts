import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET() {
  try {
    // Look for the latest data file
    const dataDir = process.cwd()
    const files = fs.readdirSync(dataDir)
    
    // Find the latest marketplace data file
    const dataFiles = files
      .filter(file => file.includes('phygitals_marketplace_complete') && file.endsWith('.json'))
      .map(file => ({
        name: file,
        path: path.join(dataDir, file),
        stats: fs.statSync(path.join(dataDir, file))
      }))
      .sort((a, b) => b.stats.mtime.getTime() - a.stats.mtime.getTime())
    
    if (dataFiles.length === 0) {
      return NextResponse.json({
        data: [],
        lastUpdated: null,
        scrapingStatus: 'idle'
      })
    }
    
    const latestFile = dataFiles[0]
    let data
    try {
      // Try reading with UTF-8 encoding first
      const fileContent = fs.readFileSync(latestFile.path, 'utf8')
      data = JSON.parse(fileContent)
    } catch (error) {
      console.error('Error reading/parsing JSON:', error)
      try {
        // Fallback: try reading as buffer and converting
        const buffer = fs.readFileSync(latestFile.path)
        const fileContent = buffer.toString('utf8')
        data = JSON.parse(fileContent)
      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError)
        return NextResponse.json({
          data: [],
          lastUpdated: null,
          scrapingStatus: 'idle'
        })
      }
    }
    
    // Check if data is recent (within last hour)
    const now = new Date()
    const fileTime = new Date(latestFile.stats.mtime)
    const hoursSinceUpdate = (now.getTime() - fileTime.getTime()) / (1000 * 60 * 60)
    
    let scrapingStatus = 'completed'
    if (hoursSinceUpdate > 1) {
      scrapingStatus = 'stale' // Data is more than 1 hour old
    }

    return NextResponse.json({
      data: Array.isArray(data) ? data : [],
      lastUpdated: latestFile.stats.mtime.toISOString(),
      scrapingStatus: scrapingStatus,
      totalCards: Array.isArray(data) ? data.length : 0,
      hoursSinceUpdate: Math.round(hoursSinceUpdate * 10) / 10
    })
  } catch (error) {
    console.error('Error reading data:', error)
    return NextResponse.json({
      data: [],
      lastUpdated: null,
      scrapingStatus: 'idle'
    })
  }
}
