import arxiv
from typing import List, Optional, Set, Dict, Union
from dataclasses import dataclass
import json
from anthropic import Anthropic
from dotenv import load_dotenv
import textwrap

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

"""
TODO:
1. We have a pdf url, if we could analyze that in some fashion, that would be ideal. note: needs to be https and has file size limits.
"""
async def evaluate_arxiv_paper(paper: ArxivPaper, description: str) -> Dict[str, Union[float, str]]:
    prompt = f"""
You are evaluating the relevance of a research paper to a patent/invention description.
Analyze how relevant and similar the paper's concepts are to the invention.
A score of 1 means that the description will infringe upon the given paper.

Invention Description:
{description}

Paper Details:
Title: {paper.title}
Summary: {paper.summary}

Output a single float number between 0 and 1 representing the relevance score.
0 means completely irrelevant, 1 means the invention would infringe on this paper.
Consider:
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

Return only valid minified JSON with no Markdown formatting, no code fences,
no explanation text—just the JSON object.
"""
    try:
        message = anthropic.messages.create(
            model=claude_model,
            max_tokens=2000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt
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
You are an expert patent analyst.
From the patent-claim description below, output ONE arXiv Boolean search query.

HARD RULES
1. Compose 2 – 4 groups joined by AND.  
   • Each group is wrapped in parentheses: ( … ).  
   • Inside a group, list 2 – 4 synonyms joined by OR.  
   • Prefix every token with the same field code (use all: unless ti:, abs:, au:, cat: is clearly better).

     Example pattern:
     (all:dating OR all:matchmaking) AND (all:recommender OR all:filtering) AND (all:profile OR all:multimedia)

2. Prefer single-word tokens; use a quoted multi-word phrase only if there is no concise single-word alternative.
3. Capitalise Boolean operators (AND, OR, ANDNOT).
4. Do not URL-encode anything.
5. Return exactly **one line** containing only the final query—no extra spaces at either end.

HEURISTICS
• Pick high-leverage synonyms—three strong OR-tokens beat eight weak ones.  
• Include the application domain ("dating") if it improves precision.  
• Skip marketing adjectives and generic verbs.

---
Patent-claim description
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

def search_papers(query: str, max_results: int = 25) -> List[ArxivPaper]:
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order = arxiv.SortOrder.Descending,
    )

    results = []
    for result in client.results(search):
        paper = ArxivPaper(
            title=result.title,
            authors=[author.name for author in result.authors],
            summary=result.summary,
            pdf_url=result.pdf_url,  # We keep this but won't use it for evaluation
            published=result.published.strftime("%Y-%m-%d"),
            paper_url=result.entry_id,
            paper_id=extract_arxiv_id(result.entry_id),
            doi=result.doi
        )
        results.append(paper)
        
    return results

"""
1. Analyze Input: Use LLM to take in description and produce keywords
2. Search Arxiv: Currently using python library
3. Analyze Papers: Use LLM to analyze papers and return the most relevant ones
"""
async def search_by_description(description: str, max_papers: int = 10) -> List[ArxivPaper]:
    raw_query = await get_search_query(description)
    query = " ".join(textwrap.dedent(raw_query).split())

    papers = search_papers(query, max_results=max_papers)
    sorted_papers = await score_and_sort_papers(papers, description)

    return sorted_papers