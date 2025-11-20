"use client"

import { useState } from "react"
import { Search, Loader2, Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

interface JobScraperFormProps {
  onSearch: (params: SearchParams) => void
  isLoading: boolean
}

export interface SearchParams {
  country: string
  role: string
  location?: string
  limit: number
  sites: string[]
}

const SUPPORTED_SITES = ["linkedin", "indeed", "glassdoor"]
const COUNTRIES = ["USA", "Canada", "UK", "Germany", "France", "India", "Australia"]

export const JobScraperForm = ({ onSearch, isLoading }: JobScraperFormProps) => {
  const [country, setCountry] = useState("USA")
  const [role, setRole] = useState("")
  const [location, setLocation] = useState("")
  const [limit, setLimit] = useState("60")
  const [selectedSites, setSelectedSites] = useState<string[]>(SUPPORTED_SITES)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!role.trim()) {
      return
    }

    onSearch({
      country,
      role: role.trim(),
      location: location.trim() || undefined,
      limit: parseInt(limit, 10),
      sites: selectedSites,
    })
  }

  const handleSiteToggle = (site: string) => {
    setSelectedSites(prev => {
      if (prev.includes(site)) {
        // Don't allow unchecking if it's the last selected site
        if (prev.length === 1) return prev
        return prev.filter(s => s !== site)
      }
      return [...prev, site]
    })
  }

  return (
    <Card className="w-full border-border/50 shadow-sm">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-semibold">Find Your Next Job</CardTitle>
        <CardDescription className="text-base">
          Search across multiple job platforms in one place
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid gap-5 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="role" className="text-sm font-medium">
                Job Title / Role
              </Label>
              <Input
                id="role"
                type="text"
                placeholder="e.g., Software Engineer"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                required
                className="h-11"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="location" className="text-sm font-medium">
                Location (Optional)
              </Label>
              <Input
                id="location"
                type="text"
                placeholder="e.g., San Francisco, CA"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="h-11"
              />
            </div>
          </div>

          <div className="grid gap-5 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="country" className="text-sm font-medium">
                Country
              </Label>
              <Select value={country} onValueChange={(value) => setCountry(value)}>
                <SelectTrigger id="country" className="h-11">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {COUNTRIES.map(c => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="limit" className="text-sm font-medium">
                Maximum Results
              </Label>
              <Input
                id="limit"
                type="number"
                min="1"
                max="200"
                value={limit}
                onChange={(e) => setLimit(e.target.value)}
                className="h-11"
              />
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <Label className="text-sm font-medium">Job Boards</Label>
            <div className="grid grid-cols-3 gap-3">
              {SUPPORTED_SITES.map(site => (
                <button
                  key={site}
                  type="button"
                  className={`
                    relative flex items-center justify-center rounded-lg border-2 p-4 transition-all
                    ${
                      selectedSites.includes(site)
                        ? "border-primary bg-primary/5"
                        : "border-border bg-background hover:border-primary/50"
                    }
                  `}
                  onClick={() => handleSiteToggle(site)}
                >
                  <div className="flex flex-col items-center gap-2">
                    <div className={`h-5 w-5 rounded border-2 flex items-center justify-center ${
                      selectedSites.includes(site)
                        ? "border-primary bg-primary"
                        : "border-muted-foreground"
                    }`}>
                      {selectedSites.includes(site) && (
                        <Check className="h-3 w-3 text-primary-foreground" />
                      )}
                    </div>
                    <span className="text-sm font-medium capitalize">{site}</span>
                  </div>
                </button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              Select at least one job board to search
            </p>
          </div>

          <Button
            type="submit"
            className="h-11 w-full text-base font-medium"
            disabled={isLoading || !role.trim() || selectedSites.length === 0}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="mr-2 h-5 w-5" />
                Search Jobs
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

