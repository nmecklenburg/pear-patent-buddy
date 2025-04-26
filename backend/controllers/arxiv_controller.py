import arxiv
from typing import List, Optional, Set
from dataclasses import dataclass
from litellm import acompletion

"""
claude-3-7-sonnet-20250219
claude-3-5-sonnet-20240620
claude-3-opus-20240229
claude-3-5-haiku-20241022 --> cheapest
"""

@dataclass
class ArxivPaper:
    title: str
    authors: List[str]
    summary: str
    pdf_url: str
    published: str
    paper_url: str
    doi: Optional[str]
    relevance_score: float = 0.0

async def evaluate_arxiv_paper(paper: ArxivPaper, description: str) -> float:
    """
    Evaluate a single arxiv paper's relevance to the original description using LLM.
    Returns a relevance score between 0 and 1.
    """
    prompt = f"""
You are evaluating the relevance of a research paper to a patent/invention description.
Analyze how relevant and similar the paper's concepts are to the invention.

Invention Description:
\"\"\"{description}\"\"\"

Paper to Evaluate:
Title: {paper.title}
Summary: {paper.summary}

Output a single float number between 0 and 1 representing the relevance score.
0 means completely irrelevant, 1 means highly relevant.
Consider:
- Conceptual similarity
- Technical overlap
- Potential applicability
- Implementation methods

Output only the number, no explanations.
"""
    
    response = await acompletion(
        model="anthropic/claude-3-5-haiku-20241022",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    try:
        score = float(response.choices[0].message.content.strip())
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    except ValueError:
        return 0.0

async def score_and_sort_papers(papers: List[ArxivPaper], description: str) -> List[ArxivPaper]:
    """
    Score papers using LLM evaluation and sort by relevance.
    """
    # Evaluate each paper
    for paper in papers:
        paper.relevance_score = await evaluate_arxiv_paper(paper, description)
    
    return sorted(papers, key=lambda x: x.relevance_score, reverse=True)

async def get_search_query(description: str) -> str:
    prompt = f"""
You are helping search for prior art on arXiv.
Given the following patent claim description, generate a concise search query with important keywords and synonyms combined using AND/OR logic.
Avoid full sentences. Use keyword-style phrasing.

Description:
\"\"\"{description}\"\"\"

Output only the query string, no explanations.
"""
    
    response = await acompletion(
        model="anthropic/claude-3-5-haiku-20241022",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    return response.choices[0].message.content.strip()

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
            pdf_url=result.pdf_url,
            published=result.published.strftime("%Y-%m-%d"),
            paper_url=result.entry_id,
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
    query = await get_search_query(description)
    
    papers = search_papers(query, max_results=max_papers)
    
    return await score_and_sort_papers(papers, description)