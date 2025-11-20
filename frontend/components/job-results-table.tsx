"use client"

import { useState } from "react"
import { ExternalLink, Building2, MapPin, Briefcase, TrendingUp, AlertCircle } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"

interface JobData {
  title: string
  company: string
  location: string
  url: string
  source: string
}

interface JobResultsTableProps {
  jobs: JobData[]
  country: string
  role: string
  location?: string
  sites: string[]
  errors?: Record<string, string>
}

export const JobResultsTable = ({ 
  jobs, 
  country, 
  role, 
  location, 
  sites,
  errors 
}: JobResultsTableProps) => {
  const [activeTab, setActiveTab] = useState<string>("all")
  
  const getSiteColor = (site: string) => {
    switch (site.toLowerCase()) {
      case "linkedin":
        return "bg-blue-100 text-blue-700 border-blue-200"
      case "indeed":
        return "bg-green-100 text-green-700 border-green-200"
      case "glassdoor":
        return "bg-purple-100 text-purple-700 border-purple-200"
      default:
        return "bg-gray-100 text-gray-700 border-gray-200"
    }
  }

  const getJobsBySource = (source: string) => {
    if (source === "all") return jobs
    return jobs.filter(job => job.source.toLowerCase() === source.toLowerCase())
  }

  const getJobCount = (source: string) => {
    return getJobsBySource(source).length
  }

  if (jobs.length === 0) {
    return (
      <Card className="w-full border-border/50 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            No Results Found
          </CardTitle>
          <CardDescription>
            No job listings were found matching your criteria. Try adjusting your search parameters.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  // Show tabs for all searched sites, not just ones with results
  const searchedSites = sites.map(site => site.toLowerCase())

  const renderJobTable = (filteredJobs: JobData[]) => (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="w-[5%] font-semibold">S.N.</TableHead>
            <TableHead className="w-[30%] font-semibold">
              <div className="flex items-center gap-2">
                <Briefcase className="h-4 w-4" />
                Job Title
              </div>
            </TableHead>
            <TableHead className="w-[25%] font-semibold">
              <div className="flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                Company
              </div>
            </TableHead>
            <TableHead className="w-[20%] font-semibold">
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Location
              </div>
            </TableHead>
            <TableHead className="w-[10%] text-center font-semibold">Source</TableHead>
            <TableHead className="w-[10%] text-center font-semibold">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredJobs.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                No jobs found from this source
              </TableCell>
            </TableRow>
          ) : (
            filteredJobs.map((job, idx) => (
              <TableRow key={`${job.source}-${job.url}-${idx}`} className="hover:bg-muted/50">
                <TableCell className="text-muted-foreground">
                  {idx + 1}
                </TableCell>
                <TableCell className="font-medium">
                  <div className="line-clamp-2">{job.title}</div>
                </TableCell>
                <TableCell>
                  <div className="line-clamp-1">{job.company}</div>
                </TableCell>
                <TableCell>
                  <div className="line-clamp-1 text-muted-foreground text-sm">
                    {job.location || "Remote"}
                  </div>
                </TableCell>
                <TableCell className="text-center">
                  <Badge variant="outline" className={`${getSiteColor(job.source)} capitalize text-xs`}>
                    {job.source}
                  </Badge>
                </TableCell>
                <TableCell className="text-center">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
                  >
                    View
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Stats Section */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-border/50 shadow-sm">
          <CardHeader className="pb-3">
            <CardDescription className="text-xs font-medium">Total Jobs Found</CardDescription>
            <CardTitle className="text-3xl font-bold">{jobs.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="border-border/50 shadow-sm">
          <CardHeader className="pb-3">
            <CardDescription className="text-xs font-medium">Searching For</CardDescription>
            <CardTitle className="text-xl font-semibold truncate">{role}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="border-border/50 shadow-sm">
          <CardHeader className="pb-3">
            <CardDescription className="text-xs font-medium">Location</CardDescription>
            <CardTitle className="text-xl font-semibold truncate">
              {location || country}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Error Messages */}
      {errors && Object.keys(errors).length > 0 && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-destructive flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Some sites encountered errors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm text-destructive/90">
              {Object.entries(errors).map(([site, error]) => (
                <li key={site}>
                  <strong className="capitalize font-medium">{site}:</strong> {error}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Tabbed Results */}
      <Card className="w-full border-border/50 shadow-sm">
        <CardContent className="p-0">
          <Tabs defaultValue="all" value={activeTab} onValueChange={setActiveTab}>
            <div className="border-b px-6 pt-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    <TrendingUp className="h-6 w-6" />
                    {activeTab === "all" ? "All Jobs" : `${activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Jobs`}
                  </h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Showing {getJobCount(activeTab)} job{getJobCount(activeTab) !== 1 ? "s" : ""}
                  </p>
                </div>
              </div>
              <TabsList className="bg-transparent border-0 p-0 h-auto space-x-6">
                <TabsTrigger 
                  value="all" 
                  className="data-[state=active]:bg-transparent data-[state=active]:shadow-none border-b-2 border-transparent data-[state=active]:border-foreground rounded-none px-0 pb-3 font-semibold text-base"
                >
                  All ({jobs.length})
                </TabsTrigger>
                {searchedSites.includes("linkedin") && (
                  <TabsTrigger 
                    value="linkedin" 
                    className="data-[state=active]:bg-transparent data-[state=active]:shadow-none border-b-2 border-transparent data-[state=active]:border-foreground rounded-none px-0 pb-3 font-semibold text-base capitalize"
                  >
                    LinkedIn ({getJobCount("linkedin")})
                  </TabsTrigger>
                )}
                {searchedSites.includes("indeed") && (
                  <TabsTrigger 
                    value="indeed" 
                    className="data-[state=active]:bg-transparent data-[state=active]:shadow-none border-b-2 border-transparent data-[state=active]:border-foreground rounded-none px-0 pb-3 font-semibold text-base capitalize"
                  >
                    Indeed ({getJobCount("indeed")})
                  </TabsTrigger>
                )}
                {searchedSites.includes("glassdoor") && (
                  <TabsTrigger 
                    value="glassdoor" 
                    className="data-[state=active]:bg-transparent data-[state=active]:shadow-none border-b-2 border-transparent data-[state=active]:border-foreground rounded-none px-0 pb-3 font-semibold text-base capitalize"
                  >
                    Glassdoor ({getJobCount("glassdoor")})
                  </TabsTrigger>
                )}
              </TabsList>
            </div>
            
            <TabsContent value="all" className="m-0">
              {renderJobTable(jobs)}
            </TabsContent>
            
            {searchedSites.includes("linkedin") && (
              <TabsContent value="linkedin" className="m-0">
                {renderJobTable(getJobsBySource("linkedin"))}
              </TabsContent>
            )}
            
            {searchedSites.includes("indeed") && (
              <TabsContent value="indeed" className="m-0">
                {renderJobTable(getJobsBySource("indeed"))}
              </TabsContent>
            )}
            
            {searchedSites.includes("glassdoor") && (
              <TabsContent value="glassdoor" className="m-0">
                {renderJobTable(getJobsBySource("glassdoor"))}
              </TabsContent>
            )}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}

