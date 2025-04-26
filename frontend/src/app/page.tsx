'use client'

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { Loader2 } from "lucide-react"

interface ArxivPaper {
  title: string
  summary: string
  authors: string[]
  link: string
  published: string
  relevance_score: number
}

export default function Home() {
  const [description, setDescription] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [papers, setPapers] = useState<ArxivPaper[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!description.trim()) {
      setError("Please enter a description of your invention.")
      return
    }

    setError(null)
    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: description,
          max_papers: 10
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to fetch papers')
      }

      const data = await response.json()
      setPapers(data)
    } catch (error) {
      setError("Failed to search for papers. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <Card className="w-full max-w-2xl shadow-lg">
        <CardHeader className="space-y-2">
          <CardTitle className="text-2xl font-bold text-primary">Patent Search Assistant</CardTitle>
          <CardDescription className="text-muted-foreground">
            Describe your invention and we'll help you find relevant prior art
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="space-y-2">
              <label
                htmlFor="description"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Invention Description
              </label>
              <Textarea
                id="description"
                placeholder="Enter a detailed description of your invention..."
                className="min-h-[150px] resize-none"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={isLoading}
              />
              {error && (
                <p className="text-sm text-red-500 mt-2">{error}</p>
              )}
            </div>
            <Button 
              className="w-full sm:w-auto" 
              size="lg" 
              onClick={handleSearch}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                'Search Prior Art'
              )}
            </Button>

            {papers.length > 0 && (
              <div className="mt-8 space-y-4">
                <h2 className="text-xl font-semibold">Search Results</h2>
                {papers.map((paper, index) => (
                  <Card key={index} className="p-4">
                    <h3 className="font-medium">{paper.title}</h3>
                    <p className="text-sm text-muted-foreground mt-1">{paper.summary}</p>
                    <div className="mt-2 flex items-center justify-between">
                      <p className="text-sm">Score: {paper.relevance_score.toFixed(2)}</p>
                      <a 
                        href={paper.link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-primary hover:underline"
                      >
                        View Paper
                      </a>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
