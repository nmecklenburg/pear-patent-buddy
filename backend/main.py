from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from controllers.arxiv_controller import search_by_description, ArxivPaper
from controllers.patent_controller import search_patents_by_description, Patent
from typing import List
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow only the frontend running at localhost:3000
origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],    # You can restrict methods if needed
    allow_headers=["*"],    # You can restrict headers if needed
)

class SearchRequest(BaseModel):
    description: str
    max_papers: int = 10

# TODO: response object?
@app.post("/api/search", response_model=List[ArxivPaper])
async def search_papers(request: SearchRequest):
    papers = await search_by_description(request.description, request.max_papers)
    return papers

# TODO actually return more info about patent
@app.post("/api/search_patents", response_model=List[Patent])
async def search_patents(request: SearchRequest):
    # TODO call search func from patent controller
    patents = await search_patents_by_description(request.description)
    return patents