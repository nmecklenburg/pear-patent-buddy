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

interface PaperCardProps {
  paper: ArxivPaper
}

interface CollapsibleSectionProps {
  title: string
  children: React.ReactNode
  defaultExpanded?: boolean
  isEmpty?: boolean
}

function CollapsibleSection({ 
  title, 
  children, 
  defaultExpanded = true,
  isEmpty = false
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded)

  return (
    <div className="space-y-2">
      <div 
        className={cn(
          "flex items-center gap-2 cursor-pointer select-none",
          !isEmpty && "hover:text-primary"
        )}
        onClick={() => !isEmpty && setIsExpanded(!isExpanded)}
      >
        {!isEmpty ? (
          isExpanded ? (
            <ChevronDown className="h-5 w-5" />
          ) : (
            <ChevronRight className="h-5 w-5" />
          )
        ) : (
          <ChevronRight className="h-5 w-5 text-muted-foreground" />
        )}
        <h2 className={cn(
          "text-xl font-semibold",
          isEmpty && "text-muted-foreground"
        )}>
          {title}
        </h2>
      </div>
      {!isEmpty && isExpanded && (
        <div className="space-y-4 pt-2">
          {children}
        </div>
      )}
      {isEmpty && (
        <p className="text-sm text-muted-foreground pl-7">No results found</p>
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
    <div 
      className="flex items-center gap-1 group relative cursor-help"
      title="An LLM assigned a score based on how much this article could be prior art"
    >
      <div
        className={cn(
          "px-2 py-0.5 rounded text-sm font-medium whitespace-nowrap",
          bgColor,
          textColor
        )}
      >
        {label}
      </div>
      <span className="text-sm font-medium whitespace-nowrap">
        ({score.toFixed(2)})
      </span>
    </div>
  )
}

// Helper function to format LaTeX in text
function formatLatex(text: string): string {
  const regex = /\$([^$]+)\$/g;
  return text.replace(regex, (match) => {
    // Just return the original LaTeX for now
    return match;
  });
}

function PaperCard({ paper }: PaperCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const summaryPreviewLength = 150

  return (
    <Card className="p-4">
      <div className="space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-start gap-4">
          <h3 className="font-medium flex-1">
            {formatLatex(paper.title)}
          </h3>
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
      placeholder="Enter a detailed description of your invention... (Press Enter to search, Shift+Enter for new line)"
      className="min-h-[4rem] transition-height duration-200"
      style={{ resize: 'none', overflow: 'hidden' }}
    />
  );
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
              <AutoExpandingTextarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={isLoading}
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
            </div>

            <div className="space-y-6">
              <CollapsibleSection 
                title="Relevant Research Papers" 
                isEmpty={papers.length === 0}
              >
                {papers.map((paper, index) => (
                  <PaperCard key={index} paper={paper} />
                ))}
              </CollapsibleSection>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
