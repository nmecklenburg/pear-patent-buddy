from litellm import acompletion
from dataclasses import dataclass
from typing import List
import pandas as pd
import asyncio
from tqdm import tqdm
from run_evals import EvalCase
import uuid

@dataclass
class Patent:
    id: str
    name: str
    abstract: str

@dataclass
class InfringingIdea:
    product_name: str
    description: str
    infringing_aspects: List[str]

@dataclass
class InfringingIdeaResponse:
    infringing_ideas: List[InfringingIdea]

async def process_patents_from_csv(csv_path: str) -> List[tuple[Patent, InfringingIdeaResponse]]:
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Create Patent objects from the DataFrame
    patents = [
        Patent(id=str(row['id']), abstract=str(row['abstract']), name=str(row['name']))
        for _, row in df.iterrows()
        if pd.notna(row['abstract'])  # Skip rows with missing abstracts
    ]
    
    # Process patents one at a time with progress bar
    results = []
    for patent in tqdm(patents):
        result = await generate_infringing_ideas(patent)
        results.append((patent, result))
    
    return results

async def generate_infringing_ideas(patent: Patent):
    prompt = f"""
You are a product manager who has a tendency to come up with ideas that infringe upon existing patents.
Given the provided patent abstract, you must come up with 10 product ideas that would technically infringe upon 1 or many of the components in the patent.
Come up with highly creative and unusual products.

Abstract:
\"\"\"{patent.abstract}\"\"\"

Output a list of 10 product ideas adhering to the below json format:

{{
    "infringing_ideas": [
        {{
            "product_name": "Name of the product",
            "description": "Brief description of how it works",
            "infringing_aspects": [
                "List specific aspects that would infringe on the patent"
            ]
        }},
        // ... (repeat for all 10 ideas)
    ]
}}

Make sure each idea is unique and creative while clearly infringing on key aspects of the patent.
"""

    response = await acompletion(
        model="anthropic/claude-3-5-haiku-20241022",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0
    )
    
    # Parse JSON response into dataclass
    import json
    response_json = json.loads(response.choices[0].message.content.strip())
    ideas = [
        InfringingIdea(**idea) 
        for idea in response_json["infringing_ideas"]
    ]
    return InfringingIdeaResponse(infringing_ideas=ideas)

async def main():
    results = await process_patents_from_csv("./eval/arxiv_sources.csv")
    
    # Convert results to evaluation format
    eval_cases = []
    for patent, result in results:
        for idea in result.infringing_ideas:
            eval_case = EvalCase(
                id=str(uuid.uuid4()),
                title=patent.name,
                type='patent',
                demo=False,
                input=idea.description,
                ground_truth=[patent.id]
            )
            eval_cases.append(eval_case)
    
    return eval_cases

if __name__ == "__main__":
    eval_cases = asyncio.run(main())
    
    # Convert eval cases to DataFrame and save to CSV
    output_file = "generated_eval_cases.csv"  # You can change this variable name as needed
    eval_df = pd.DataFrame([vars(case) for case in eval_cases])
    eval_df.to_csv(output_file, index=False)
    print(f"Evaluation cases saved to {output_file}")