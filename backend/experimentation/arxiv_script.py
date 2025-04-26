import asyncio
from arxiv_controller import search_by_description

description = """
I am creating a swipe to unlock feature where the user will be putting their finger 
on a button on a screen and dragging it across the screen horizontally. The button
will drag along with the finger and when the button gets to the end of the screen, it will unlock
whatever device the user was using.
"""

async def main():
    papers = await search_by_description(description)
    
    print(f"\nSearch results for: {description}\n")
    for i, paper in enumerate(papers, 1):
        print(f"{i}. Title: {paper.title}")
        print(f"   Relevance Score: {paper.relevance_score:.2f}")
        print(f"   Authors: {', '.join(paper.authors)}")
        print(f"   Summary: {paper.summary[:200]}...")
        print(f"   URL: {paper.paper_url}")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 
