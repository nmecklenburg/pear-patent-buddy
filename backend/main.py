from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}