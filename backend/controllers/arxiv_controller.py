import arxiv
from typing import List, Optional, Set, Dict, Union
from dataclasses import dataclass
import json
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

anthropic = Anthropic()

"""
claude-3-7-sonnet-20250219
claude-3-5-sonnet-20240620
claude-3-opus-20240229
claude-3-5-haiku-20241022 --> cheapest
"""
claude_model="claude-3-7-sonnet-20250219"

@dataclass
class ArxivPaper:
    title: str
    authors: List[str]
    summary: str
    pdf_url: str
    published: str
    paper_url: str
    paper_id: str
    doi: Optional[str]
    relevance_score: float = 0.0
    reasoning: str = ""

async def evaluate_arxiv_paper(paper: ArxivPaper, description: str) -> Dict[str, Union[float, str]]:
    prompt = f"""
You are evaluating the relevance of a research paper to a patent/invention description.
Analyze how relevant and similar the paper's concepts are to the invention.
A score of 1 means that the description will infringe upon the given paper.

Invention Description:
{description}

Output a single float number between 0 and 1 representing the relevance score.
0 means completely irrelevant, 1 means the invention would infringe on this paper.
Consider:
- The attached PDF of the paper.
- Conceptual similarity
- Technical overlap
- Potential applicability
- Implementation methods
- Specific claims and techniques described

Respond with a JSON object containing two fields:
1. relevance_score: A number between 0 and 1
2. reasoning: A string explaining the score

Example format:
{{"relevance_score": 0.75, "reasoning": "This paper is highly relevant because..."}}
"""
    try:
        print(f"Paper Title: {paper.title}")
        print(f"Paper PDF Url: {paper.pdf_url}")
        message = anthropic.messages.create(
            model=claude_model,
            max_tokens=1000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "document",
                            "source": {
                                "type": "url",
                                "url": paper.pdf_url
                            }
                        }
                    ]
                }
            ]
        )
        
        result = json.loads(message.content[0].text)
        result["relevance_score"] = max(0.0, min(1.0, float(result["relevance_score"])))
        return result
    except Exception as e:
        print(f"Error evaluating paper: {e}")
        return {"relevance_score": 0.0, "reasoning": f"Failed to evaluate paper: {str(e)}"}

async def score_and_sort_papers(papers: List[ArxivPaper], description: str) -> List[ArxivPaper]:
    for paper in papers:
        result = await evaluate_arxiv_paper(paper, description)
        paper.relevance_score = result["relevance_score"]
        paper.reasoning = result["reasoning"]
    
    return sorted(papers, key=lambda x: x.relevance_score, reverse=True)

async def get_search_query(description: str) -> str:
    prompt = f"""
You are an expert patent analyst and scientific researcher tasked with finding relevant prior art on arXiv.

Given the following patent-claim description, extract the most technically significant concepts, components, methods, and applications, then generate a single arXiv search query.

**Mandatory arXiv syntax rules**
• Prefix every search term or phrase with an arXiv field code.  
  – Use `all:` unless a specific field (`ti:`, `abs:`, `au:`, `cat:` …) is clearly better.  
• Capitalise Boolean operators (`AND`, `OR`, `ANDNOT`).  
• Group OR-lists inside parentheses.  
• Wrap multi-word phrases in double quotes.  
• Do *not* URL-encode anything; return plain text.  
• Output **only** the final query string.
• Prefix every token or quoted phrase with a field code (use all: by default).
• Do NOT output raw ( ) or " " — leave them in, but remember the client must URL-encode
  ( → %28, ) → %29, " → %22) before sending the HTTP request.

**Guidelines for good recall + precision**
1. Identify core technical concepts and their common synonyms.  
2. Balance broad umbrella terms with specific implementations.  
3. Include relevant application domains or device classes.  
4. Omit stop-words and non-technical phrasing.

Patent claim description:
{description}
"""

    message = anthropic.messages.create(
        model=claude_model,
        max_tokens=2000,
        temperature=0.2,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    return message.content[0].text.strip()

def extract_arxiv_id(entry_id: str) -> str:
    # entry_id format: http://arxiv.org/abs/2403.12345v1
    return entry_id.split('/')[-1]

def convert_to_https_arxiv(url: str) -> str:
    if url.startswith('http://'):
        return url.replace('http://', 'https://')
    return url

def search_papers(query: str, max_results: int = 10) -> List[ArxivPaper]:
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    results = []
    for result in client.results(search):
        paper = ArxivPaper(
            title=result.title,
            authors=[author.name for author in result.authors],
            summary=result.summary,
            pdf_url=convert_to_https_arxiv(result.pdf_url),
            published=result.published.strftime("%Y-%m-%d"),
            paper_url=result.entry_id,
            paper_id=extract_arxiv_id(result.entry_id),
            doi=result.doi
        )
        results.append(paper)
    
    print(f"Analyzing {len(results)} Papers")
        
    return results

"""
1. Analyze Input: Use LLM to take in description and produce keywords
2. Search Arxiv: Currently using python library
3. Analyze Papers: Use LLM to analyze papers and return the most relevant ones
"""
async def search_by_description(description: str, max_papers: int = 10) -> List[ArxivPaper]:
    query = await get_search_query(description)
    papers = search_papers(query, max_results=max_papers)
    
    return await score_and_sort_papers(papers, description)