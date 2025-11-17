import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

// Force dynamic rendering - no caching
export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET(request: Request) {
  try {
    const dataDir = process.cwd()
    const intelligenceFile = path.join(dataDir, 'deal_intelligence.json')
    
    if (!fs.existsSync(intelligenceFile)) {
      return NextResponse.json({ 
        error: 'Deal intelligence data not found. Please run the intelligence system first.' 
      }, { status: 404 })
    }
    
    // Get file modification time for cache busting
    const stats = fs.statSync(intelligenceFile)
    const fileMtime = stats.mtime.toISOString()
    
    // Read file fresh every time (no caching)
    const fileContent = fs.readFileSync(intelligenceFile, 'utf8')
    const data = JSON.parse(fileContent)
    
    // Use file modification time as lastUpdated if available
    const lastUpdated = data.summary?.last_updated || fileMtime
    
    return NextResponse.json({
      success: true,
      data: data,
      lastUpdated: lastUpdated,
      fileMtime: fileMtime
    }, {
      headers: {
        'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0',
        'Pragma': 'no-cache',
        'Expires': '0',
        'Last-Modified': fileMtime,
        'ETag': `"${stats.mtime.getTime()}"`
      }
    })
    
  } catch (error) {
    console.error('Error reading deal intelligence data:', error)
    return NextResponse.json({ 
      error: 'Failed to read deal intelligence data' 
    }, { status: 500 })
  }
}
