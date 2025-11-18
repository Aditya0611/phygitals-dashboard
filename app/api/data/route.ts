import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET() {
  try {
    // Look for the latest data file (local mode only)
    const dataDir = process.cwd()
    const files = fs.readdirSync(dataDir)

    // If LATEST_ONLY=1, prefer the most recent progress chunk instead of the merged file
    const useLatestOnly = process.env.LATEST_ONLY === '1'

    const toFileMeta = (file: string) => ({
      name: file,
      path: path.join(dataDir, file),
      stats: fs.statSync(path.join(dataDir, file))
    })

    const progressFiles = files
      .filter(file => file.startsWith('marketplace_url_progress_page') && file.endsWith('.json'))
      .map(toFileMeta)
      .sort((a, b) => b.stats.mtime.getTime() - a.stats.mtime.getTime())

    const completeFiles = files
      .filter(file => file.includes('phygitals_marketplace_complete') && file.endsWith('.json'))
      .map(toFileMeta)
      .sort((a, b) => b.stats.mtime.getTime() - a.stats.mtime.getTime())

    let latestFile = null as null | typeof progressFiles[number]
    let sourceType: 'progress' | 'complete' | 'unknown' = 'unknown'

    if (useLatestOnly) {
      latestFile = progressFiles[0] ?? completeFiles[0] ?? null
      sourceType = progressFiles[0] ? 'progress' : completeFiles[0] ? 'complete' : 'unknown'
    } else {
      const latestProgress = progressFiles[0]
      const latestComplete = completeFiles[0]

      if (latestProgress && latestComplete) {
        if (latestProgress.stats.mtime >= latestComplete.stats.mtime) {
          latestFile = latestProgress
          sourceType = 'progress'
        } else {
          latestFile = latestComplete
          sourceType = 'complete'
        }
      } else if (latestProgress) {
        latestFile = latestProgress
        sourceType = 'progress'
      } else if (latestComplete) {
        latestFile = latestComplete
        sourceType = 'complete'
      }
    }

    if (!latestFile) {
      return NextResponse.json({
        data: [],
        lastUpdated: null,
        scrapingStatus: 'idle'
      })
    }

    let data = []
    try {
      // Check if file exists and has content
      const stats = fs.statSync(latestFile.path)
      if (stats.size === 0) {
        console.error('File is empty:', latestFile.path)
        return NextResponse.json({
          data: [],
          lastUpdated: null,
          scrapingStatus: 'idle',
          error: 'Data file is empty'
        })
      }
      
      // Try reading with UTF-8 encoding first
      const fileContent = fs.readFileSync(latestFile.path, 'utf8').trim()
      if (!fileContent) {
        console.error('File content is empty after trim')
        return NextResponse.json({
          data: [],
          lastUpdated: null,
          scrapingStatus: 'idle',
          error: 'Data file has no content'
        })
      }
      
      data = JSON.parse(fileContent)
      
      // Validate it's an array
      if (!Array.isArray(data)) {
        data = []
      }
    } catch (error) {
      console.error('Error reading/parsing JSON:', error)
      // Return empty data instead of crashing
      data = []
    }
    
    // Check if data is recent (within last hour)
    const now = new Date()
    const fileTime = new Date(latestFile.stats.mtime)
    const hoursSinceUpdate = (now.getTime() - fileTime.getTime()) / (1000 * 60 * 60)
    
    let scrapingStatus = useLatestOnly ? 'latest-only' : 'completed'
    if (sourceType === 'progress') {
      scrapingStatus = 'running'
    } else if (hoursSinceUpdate > 1) {
      scrapingStatus = 'stale' // Data is more than 1 hour old
    }

    // Optional local blocklist of problematic/unlisted URLs
    let blockedUrls: Set<string> = new Set()
    try {
      const blockPath = path.join(dataDir, 'unlisted_blocklist.json')
      if (fs.existsSync(blockPath)) {
        const arr = JSON.parse(fs.readFileSync(blockPath, 'utf8'))
        if (Array.isArray(arr)) blockedUrls = new Set(arr.map((s: any) => String(s)))
      }
    } catch {}

    // Remove unlisted cards: require a valid listing URL and positive price
    // Show ALL cards (including below $100) in dashboard
    const cleaned = (Array.isArray(data) ? data : []).filter((card: any) => {
      // Accept any known listing link field
      const hasUrl = Boolean(card?.listing_url || card?.card_url || card?.url || card?.link)
      const priceRaw = String(card?.current_price ?? card?.price ?? '').trim()
      const priceText = priceRaw.toLowerCase()
      const price = parseFloat(priceRaw.replace(/[$,]/g, ''))
      // Normalize status fields and exclude any unlisted/offline states
      const statusFields = [card?.status, card?.listing_status, card?.availability, card?.state]
      const statusJoined = statusFields
        .filter(Boolean)
        .map((s: any) => String(s).toLowerCase())
        .join(' | ')
      const flaggedByBooleans = [card?.listed, card?.is_listed, card?.available, card?.isAvailable]
        .some((v: any) => v === false)
      const explicitlyUnlisted = (
        statusJoined.includes('unlisted') ||
        statusJoined.includes('not listed') ||
        statusJoined.includes('delisted') ||
        statusJoined.includes('inactive') ||
        statusJoined.includes('unavailable') ||
        statusJoined.includes('sold') ||
        statusJoined.includes('out of stock')
      ) || flaggedByBooleans || priceText.includes('unlisted') || priceText.includes('not for sale')
      const url = String(card?.listing_url || card?.card_url || card?.url || card?.link || '')
      if (blockedUrls.has(url)) return false
      // Show all cards with valid price (including below $100)
      return hasUrl && !Number.isNaN(price) && price > 0 && !explicitlyUnlisted
    })
    // ALT-first FMV normalization for display
    .map((card: any) => {
      // Handle "N/A" FMV - don't convert to $0.00
      const currentFmv = String(card?.fmv || '').trim()
      if (currentFmv === 'N/A' || currentFmv === 'n/a' || currentFmv === '' || !currentFmv) {
        // If FMV is N/A or missing, try to find ALT FMV or keep as "N/A"
        const fmvSource = String(card?.fmv_source || '').toLowerCase()
        const altCandidates = [
          card?.alt_fmv,
          card?.alt_value,
          card?.alt_estimate,
          card?.alt_price,
          card?.fmv_alt,
          card?.alt
        ]
        const alt = altCandidates
          .map(v => (v == null ? '' : String(v)))
          .map(v => parseFloat(v.replace(/[$,]/g, '')))
          .find(v => Number.isFinite(v) && v > 0)
        const price = parseFloat(String(card?.current_price ?? card?.price ?? '').replace(/[$,]/g, ''))
        
        if (alt !== undefined && Number.isFinite(alt) && alt > 0 && Number.isFinite(price) && price > 0) {
          // Only use ALT if it looks reasonable
          if (!(alt > 500 || alt > price * 3)) {
            return { ...card, fmv: `$${alt.toFixed(2)}`, fmv_source: 'alt' }
          }
        }
        // Keep as "N/A" if no valid FMV found
        return { ...card, fmv: 'N/A', fmv_source: card?.fmv_source || '' }
      }
      
      // FMV exists - check if it's a valid number
      const fmvParsed = parseFloat(currentFmv.replace(/[$,]/g, ''))
      if (!Number.isFinite(fmvParsed) || fmvParsed <= 0) {
        // Invalid FMV - try ALT as fallback
        const fmvSource = String(card?.fmv_source || '').toLowerCase()
        const altCandidates = [
          card?.alt_fmv,
          card?.alt_value,
          card?.alt_estimate,
          card?.alt_price,
          card?.fmv_alt,
          card?.alt
        ]
        const alt = altCandidates
          .map(v => (v == null ? '' : String(v)))
          .map(v => parseFloat(v.replace(/[$,]/g, '')))
          .find(v => Number.isFinite(v) && v > 0)
        const price = parseFloat(String(card?.current_price ?? card?.price ?? '').replace(/[$,]/g, ''))
        
        if (alt !== undefined && Number.isFinite(alt) && alt > 0 && Number.isFinite(price) && price > 0) {
          if (!(alt > 500 || alt > price * 3)) {
            return { ...card, fmv: `$${alt.toFixed(2)}`, fmv_source: 'alt' }
          }
        }
        return { ...card, fmv: 'N/A', fmv_source: card?.fmv_source || '' }
      }
      
      // Valid FMV exists - check if we should prefer ALT
      const fmvSource = String(card?.fmv_source || '').toLowerCase()
      const altCandidates = [
        card?.alt_fmv,
        card?.alt_value,
        card?.alt_estimate,
        card?.alt_price,
        card?.fmv_alt,
        card?.alt
      ]
      const alt = altCandidates
        .map(v => (v == null ? '' : String(v)))
        .map(v => parseFloat(v.replace(/[$,]/g, '')))
        .find(v => Number.isFinite(v) && v > 0)
      const price = parseFloat(String(card?.current_price ?? card?.price ?? '').replace(/[$,]/g, ''))
      
      // Prefer ALT if available and valid
      if (alt !== undefined && Number.isFinite(alt) && alt > 0 && Number.isFinite(price) && price > 0) {
        if (!(alt > 500 || alt > price * 3)) {
          return { ...card, fmv: `$${alt.toFixed(2)}`, fmv_source: 'alt' }
        }
      }
      
      // Use existing FMV if it's valid
      return card
    })

    return NextResponse.json({
      data: cleaned,
      lastUpdated: latestFile.stats.mtime.toISOString(),
      scrapingStatus: scrapingStatus,
      totalCards: cleaned.length,
      hoursSinceUpdate: Math.round(hoursSinceUpdate * 10) / 10,
      dataSource: sourceType
    }, {
      headers: {
        'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0',
        'Pragma': 'no-cache',
        'Expires': '0',
        'Last-Modified': latestFile.stats.mtime.toISOString(),
        'ETag': `"${latestFile.stats.mtime.getTime()}"`
      }
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
