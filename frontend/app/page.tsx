"use client"

import { useState } from "react"
import { JobScraperForm, SearchParams } from "@/components/job-scraper-form"
import { JobResultsTable } from "@/components/job-results-table"
import { toast } from "sonner"

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

export default function Home() {
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState<ScrapeResponse | null>(null)

  const handleSearch = async (params: SearchParams) => {
    setIsLoading(true)
    setResults(null)

    try {
      const queryParams = new URLSearchParams({
        country: params.country,
        role: params.role,
        limit: params.limit.toString(),
      })

      if (params.location) {
        queryParams.append("location", params.location)
      }

      params.sites.forEach(site => {
        queryParams.append("sites", site)
      })

      const response = await fetch(
        `http://localhost:8000/scrape?${queryParams.toString()}`
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        throw new Error(
          errorData?.detail || `Failed to fetch jobs: ${response.statusText}`
        )
      }

      const data: ScrapeResponse = await response.json()
      setResults(data)

      toast.success(`Found ${data.dataframe.row_count} jobs!`, {
        description: `Scraped from ${data.sites.join(", ")}`,
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : "An error occurred"
      toast.error("Search failed", {
        description: message,
      })
      console.error("Search error:", error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <main className="container mx-auto px-4 py-8 md:py-12 max-w-7xl">
        <div className="mb-10 space-y-3">
          <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
            Job Search Dashboard
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Search for jobs across LinkedIn, Indeed, and Glassdoor in one place
          </p>
        </div>

        <div className="space-y-8">
          <JobScraperForm onSearch={handleSearch} isLoading={isLoading} />

          {results && (
            <JobResultsTable
              jobs={results.dataframe.rows}
              country={results.country}
              role={results.role}
              location={results.location}
              sites={results.sites}
              errors={results.errors}
            />
          )}
        </div>
      </main>
    </div>
  )
}
