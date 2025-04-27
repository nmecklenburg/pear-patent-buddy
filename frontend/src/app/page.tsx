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
import { useState, useRef, useEffect } from "react"
import { Loader2, ChevronDown, ChevronUp, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface ArxivPaper {
  title: string
  summary: string
  authors: string[]
  pdf_url: string
  published: string
  relevance_score: number
  reasoning: string
}

interface Patent {
  id: string
  title: string
  summary: string
  relevance_score: number
}

interface PaperCardProps {
  paper: ArxivPaper
}

interface CollapsibleSectionProps {
  title: string
  children: React.ReactNode
  defaultExpanded?: boolean
  isEmpty?: boolean
}

function PaperSearchLoadingText() {
  return (
    <div className="relative inline-flex items-center text-sm text-primary font-medium">
      <span className="loading-dots">Searching for papers</span>
    </div>
  )
}

function PatentSearchLoadingText() {
  return (
    <div className="relative inline-flex items-center text-sm text-primary font-medium">
      <span className="loading-dots">Searching for patents</span>
    </div>
  )
}

function CollapsibleSection({ 
  title, 
  children, 
  defaultExpanded = true,
  isEmpty = false,
  isLoading = false,
  type = 'papers'
}: CollapsibleSectionProps & { 
  isLoading?: boolean,
  type?: 'papers' | 'patents'
}) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <div className="space-y-2">
      <div 
        className={cn(
          "flex items-center gap-2 cursor-pointer select-none",
          !isEmpty && !isLoading && "hover:text-primary"
        )}
        onClick={() => !isEmpty && !isLoading && setIsExpanded(!isExpanded)}
      >
        {!isEmpty && !isLoading ? (
          isExpanded ? (
            <ChevronDown className="h-5 w-5 transition-transform duration-200" />
          ) : (
            <ChevronRight className="h-5 w-5 transition-transform duration-200" />
          )
        ) : (
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        )}
        <h2 className={cn(
          "text-xl font-semibold flex-1",
          isEmpty && "text-muted-foreground"
        )}>
          {title}
        </h2>
        {isEmpty && !isLoading && (
          <p className="text-sm text-muted-foreground">No results found</p>
        )}
        {isLoading && (
          type === 'papers' ? <PaperSearchLoadingText /> : <PatentSearchLoadingText />
        )}
      </div>
      {!isEmpty && !isLoading && isExpanded && (
        <div className="space-y-4 pt-2 transition-all duration-200">
          {children}
        </div>
      )}
    </div>
  )
}

function RelevanceIndicator({ score }: { score: number }) {
  let status: 'not-relevant' | 'somewhat-relevant' | 'highly-relevant'
  let label: string
  let bgColor: string
  let textColor: string
  
  if (score < 0.3) {
    status = 'not-relevant'
    label = 'Not Relevant'
    bgColor = 'bg-red-100'
    textColor = 'text-red-700'
  } else if (score < 0.7) {
    status = 'somewhat-relevant'
    label = 'Somewhat Relevant'
    bgColor = 'bg-yellow-100'
    textColor = 'text-yellow-700'
  } else {
    status = 'highly-relevant'
    label = 'Really Relevant'
    bgColor = 'bg-green-100'
    textColor = 'text-green-700'
  }

  return (
    <div className="group relative">
      <div
        className={cn(
          "px-2 py-0.5 rounded text-sm font-medium whitespace-nowrap",
          bgColor,
          textColor
        )}
      >
        {label}
      </div>
      <div className="absolute -top-8 right-0 px-2 py-1 bg-black text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
        LLM Relevancy Score: {score.toFixed(2)}
      </div>
    </div>
  )
}

function PaperCard({ paper }: PaperCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const summaryPreviewLength = 150

  return (
    <Card className="p-4">
      <div className="space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-start gap-4">
          <div className="flex-1">
            <h3 className="font-medium">
              {paper.title}
            </h3>
          </div>
          <div className="flex flex-col items-end gap-2">
            <a 
              href={paper.pdf_url}
              target="_blank" 
              rel="noopener noreferrer"
              className="text-sm bg-primary text-primary-foreground px-3 py-1 rounded-md hover:bg-primary/90"
            >
              PDF
            </a>
            <RelevanceIndicator score={paper.relevance_score} />
          </div>
        </div>
        
        <div className="text-sm text-muted-foreground">
          <p className="text-xs">Published: {paper.published}</p>
          <p className="text-xs">Authors: {paper.authors.join(", ")}</p>
        </div>

        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">
            {isExpanded ? paper.summary : paper.summary.slice(0, summaryPreviewLength) + "..."}
          </p>
          {paper.summary.length > summaryPreviewLength && (
            <Button
              variant="ghost"
              size="sm"
              className="w-full text-xs"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? (
                <><ChevronUp className="h-4 w-4 mr-1" /> Show Less</>
              ) : (
                <><ChevronDown className="h-4 w-4 mr-1" /> Show More</>
              )}
            </Button>
          )}
        </div>

        {isExpanded && paper.reasoning && (
          <div className="mt-2 pt-2 border-t">
            <p className="text-sm font-medium">Relevance Analysis:</p>
            <p className="text-sm text-muted-foreground">{paper.reasoning}</p>
          </div>
        )}
      </div>
    </Card>
  )
}

function PatentCard({ patent }: { patent: Patent }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const summaryPreviewLength = 150

  return (
    <Card className="p-4">
      <div className="space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-start gap-4">
          <div className="flex-1">
            <h3 className="font-medium">
              {patent.title}
            </h3>
            <p className="text-sm text-primary">Patent #{patent.id}</p>
          </div>
          <RelevanceIndicator score={patent.relevance_score} />
        </div>

        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">
            {isExpanded ? patent.summary : patent.summary.slice(0, summaryPreviewLength) + "..."}
          </p>
          {patent.summary.length > summaryPreviewLength && (
            <Button
              variant="ghost"
              size="sm"
              className="w-full text-xs"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? (
                <><ChevronUp className="h-4 w-4 mr-1" /> Show Less</>
              ) : (
                <><ChevronDown className="h-4 w-4 mr-1" /> Show More</>
              )}
            </Button>
          )}
        </div>
      </div>
    </Card>
  )
}

function AutoExpandingTextarea({ 
  value, 
  onChange, 
  disabled,
  onSubmit 
}: { 
  value: string
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void
  disabled: boolean
  onSubmit: () => void
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = '4rem'; // 2 lines default height
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent newline
      if (!disabled) {
        onSubmit();
      }
    }
  };

  return (
    <Textarea
      ref={textareaRef}
      value={value}
      onChange={onChange}
      onKeyDown={handleKeyDown}
      disabled={disabled}
      placeholder="Enter a detailed description of your invention..."
      className="min-h-[4rem] transition-height duration-200"
      style={{ resize: 'none', overflow: 'hidden' }}
    />
  );
}

export default function Home() {
  const [description, setDescription] = useState("")
  const [isPapersLoading, setIsPapersLoading] = useState(false)
  const [isPatentsLoading, setIsPatentsLoading] = useState(false)
  const [papers, setPapers] = useState<ArxivPaper[]>([])
  const [patents, setPatents] = useState<Patent[]>([])
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!description.trim()) {
      setError("Please enter a description of your invention.")
      return
    }

    setError(null)
    setIsPapersLoading(true)
    setIsPatentsLoading(true)

    // Search papers
    fetch('http://localhost:8000/api/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        description: description,
        max_papers: 10
      }),
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch papers')
        return response.json()
      })
      .then(data => setPapers(data))
      .catch(error => setError("Failed to search for papers. Please try again."))
      .finally(() => setIsPapersLoading(false))

    // Search patents
    fetch('http://localhost:8000/api/search_patents', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        description: description,
      }),
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch patents')
        return response.json()
      })
      .then(data => setPatents(data))
      .catch(error => setError("Failed to search for patents. Please try again."))
      .finally(() => setIsPatentsLoading(false))
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
              <AutoExpandingTextarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={isPapersLoading || isPatentsLoading}
                onSubmit={handleSearch}
              />
              {error && (
                <p className="text-sm text-red-500 mt-2">{error}</p>
              )}
            </div>
            <div className="flex justify-end">
              <Button 
                size="lg" 
                onClick={handleSearch}
                disabled={isPapersLoading || isPatentsLoading}
              >
                {(isPapersLoading || isPatentsLoading) ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  'Find Potential Infringement'
                )}
              </Button>
            </div>

            <div className="space-y-6">
              <CollapsibleSection 
                title="Relevant Research Papers" 
                isEmpty={papers.length === 0}
                isLoading={isPapersLoading}
                type="papers"
              >
                {papers.map((paper, index) => (
                  <PaperCard key={index} paper={paper} />
                ))}
              </CollapsibleSection>
            </div>
            <div className="space-y-6">
              <CollapsibleSection 
                title="Relevant Patents" 
                isEmpty={patents.length === 0}
                isLoading={isPatentsLoading}
                type="patents"
              >
                {patents.map((patent, index) => (
                  <PatentCard key={index} patent={patent} />
                ))}
              </CollapsibleSection>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
