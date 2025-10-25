# Phygitals Marketplace Dashboard

A modern web dashboard for viewing and managing Pokemon card marketplace data from Phygitals.com.

## Features

- 📊 **Real-time Data Visualization** - View scraped marketplace data in an interactive table
- 🔍 **Advanced Filtering** - Filter cards by name, grader, grade, price, and more
- 📈 **Analytics Dashboard** - Statistics cards showing total cards, value, and trends
- ⏰ **Scheduled Scraping** - Automatic data collection every 6 hours
- 📥 **Data Export** - Download data as CSV files
- 🎨 **Modern UI** - Built with shadcn/ui and Tailwind CSS

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript
- **UI Components**: shadcn/ui, Radix UI, Tailwind CSS
- **Data Table**: TanStack Table
- **Backend**: Next.js API Routes
- **Scheduling**: node-cron
- **Data Processing**: Python scrapers

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

### 3. Start Scheduler (Optional)

```bash
node scheduler.js
```

## Project Structure

```
├── app/                    # Next.js app directory
│   ├── api/               # API routes
│   │   ├── data/         # Data fetching endpoint
│   │   └── scrape/       # Scraping trigger endpoint
│   ├── globals.css       # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx          # Dashboard page
├── components/            # React components
│   ├── ui/               # shadcn/ui components
│   ├── data-table.tsx    # Data table component
│   └── stats-cards.tsx   # Statistics cards
├── lib/                   # Utility functions
├── scheduler.js          # Cron job scheduler
└── package.json         # Dependencies
```

## API Endpoints

### GET /api/data
Returns the latest scraped marketplace data.

**Response:**
```json
{
  "data": [...],
  "lastUpdated": "2025-10-24T16:23:47.000Z",
  "scrapingStatus": "completed"
}
```

### POST /api/scrape
Triggers a new scraping session.

**Response:**
```json
{
  "success": true,
  "message": "Scraping started successfully"
}
```

## Data Structure

Each card record contains:

```typescript
{
  listing_url: string        // Direct link to card listing
  full_listing_name: string   // Complete card name
  pokemon_name: string       // Pokemon name
  grader: string            // CGC, PSA, BGS, etc.
  grade: string             // Card grade (10, 9, 8.5, etc.)
  current_price: string      // Current asking price
  fmv: string               // Fair market value
  card_set: string          // Card set name
  card_number: string       // Card number in set
  condition: string         // Card condition
  seller: string            // Seller information
}
```

## Features

### Dashboard
- **Statistics Cards**: Total cards, value, average price, top grader
- **Data Table**: Sortable, filterable table with all card data
- **Real-time Updates**: Auto-refresh every 5 minutes
- **Export Functionality**: Download data as CSV

### Data Management
- **Manual Scraping**: Trigger scraping on-demand
- **Scheduled Scraping**: Automatic collection every 6 hours
- **Progress Tracking**: Real-time scraping status
- **Data Validation**: Error handling and data quality checks

### Filtering & Search
- **Text Search**: Filter by card name
- **Column Filters**: Filter by grader, grade, price range
- **Sorting**: Sort by any column
- **Pagination**: Handle large datasets efficiently

## Deployment

### Vercel (Recommended)

1. Connect your GitHub repository to Vercel
2. Set environment variables if needed
3. Deploy automatically on push

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Manual Deployment

```bash
npm run build
npm start
```

## Environment Variables

No environment variables required for basic functionality.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API endpoints

---

**Built with ❤️ for Pokemon card collectors**