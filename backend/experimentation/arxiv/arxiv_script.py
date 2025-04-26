import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from controllers.arxiv_controller import search_by_description

description = """
I am creating a swipe to unlock feature where the user will be putting their finger 
on a button on a screen and dragging it across the screen horizontally. The button
will drag along with the finger and when the button gets to the end of the screen, it will unlock
whatever device the user was using.
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
