import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from controllers.arxiv_controller import search_by_description

description = """
An AI-powered dating app that uses machine learning to analyze multimedia profile content and predict emotional compatibility beyond traditional matching algorithms
"""

async def main():
    papers_with_pdf = await search_by_description(description, max_papers=5)
    
    for i, paper in enumerate(papers_with_pdf, 1):
        print(f"{i}. Title: {paper.title}")
        print(f"   Paper ID: {paper.paper_id}")
        print(f"   Relevance Score: {paper.relevance_score:.2f}")
        print(f"   Reasoning: {paper.reasoning}")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 
