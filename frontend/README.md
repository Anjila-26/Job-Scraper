# Job Scraper Frontend

A modern, beautiful frontend for the Job Scraper application built with Next.js 16, TypeScript, and shadcn/ui.

## Features

- 🎨 Modern UI with shadcn/ui components
- 📱 Fully responsive design
- 🔍 Real-time job search across multiple platforms
- 📊 Clean table view with job details
- 🔔 Toast notifications for user feedback
- ⚡ Fast and performant with Next.js 16
- 🎯 Type-safe with TypeScript

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with Toaster
│   ├── page.tsx            # Main page with job search
│   └── globals.css         # Global styles with shadcn theme
├── components/
│   ├── job-scraper-form.tsx    # Job search form component
│   ├── job-results-table.tsx   # Results table component
│   └── ui/                     # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── select.tsx
│       ├── sonner.tsx
│       └── table.tsx
└── lib/
    └── utils.ts            # Utility functions (cn helper)
```

## Components

### JobScraperForm
The main search form that collects user preferences:
- Country selection dropdown
- Job title/role input (required)
- Optional location input
- Maximum results slider
- Job board toggles (LinkedIn, Indeed, Glassdoor)
- Submit button with loading state

**Props:**
```typescript
interface JobScraperFormProps {
  onSearch: (params: SearchParams) => void
  isLoading: boolean
}
```

### JobResultsTable
Displays scraped job results in a clean table:
- Job title, company, location columns
- Source badge (LinkedIn/Indeed/Glassdoor)
- External link to original job posting
- Error messages if any scrapers failed
- Empty state when no results found

**Props:**
```typescript
interface JobResultsTableProps {
  jobs: JobData[]
  country: string
  role: string
  location?: string
  sites: string[]
  errors?: Record<string, string>
}
```

## shadcn/ui Components

This project uses the following shadcn/ui components:

- **Button** - Primary actions and toggles
- **Card** - Container for form and results
- **Input** - Text input fields
- **Label** - Form labels
- **Select** - Dropdown menus
- **Table** - Results display
- **Toaster** - Toast notifications (via sonner)

## Styling

The app uses Tailwind CSS 4 with a custom theme defined in `globals.css`:

- CSS variables for theming
- OKLCH color format for better color control
- Light and dark mode support (via CSS variables)
- Responsive design with mobile-first approach

## API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000`:

**Endpoint:** `GET /scrape`

**Query Parameters:**
- `country` (required)
- `role` (required)
- `location` (optional)
- `limit` (optional, default: 60)
- `sites` (optional, can be repeated)

**Example Request:**
```
http://localhost:8000/scrape?country=USA&role=Software%20Engineer&location=San%20Francisco&limit=60&sites=linkedin&sites=indeed
```

## Development

Start the development server:

```bash
npm run dev
```

Build for production:

```bash
npm run build
npm start
```

Run linting:

```bash
npm run lint
```

## Adding New Components

To add a new shadcn/ui component:

1. Install the component package if needed:
   ```bash
   npm install @radix-ui/react-[component-name]
   ```

2. Create the component file in `components/ui/`

3. Import and use in your pages/components

## Type Safety

All components are fully typed with TypeScript. Key interfaces:

```typescript
interface SearchParams {
  country: string
  role: string
  location?: string
  limit: number
  sites: string[]
}

interface JobData {
  title: string
  company: string
  location: string
  url: string
  source: string
}

interface ScrapeResponse {
  country: string
  role: string
  location?: string
  sites: string[]
  dataframe: {
    columns: string[]
    rows: JobData[]
    row_count: number
  }
  errors?: Record<string, string>
}
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Server components by default for better performance
- Client components only where needed (`"use client"`)
- Optimized images and assets
- Code splitting with Next.js

## Accessibility

- Semantic HTML
- ARIA labels where appropriate
- Keyboard navigation support
- Focus management
- Screen reader friendly

## License

MIT
