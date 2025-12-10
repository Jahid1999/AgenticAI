from fastapi import FastAPI

app = FastAPI(
    title="Agentic AI API",
    description="API for Agentic AI with OpenAI Agent SDK integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/")
async def root():
    return {"message": "Welcome to Agentic AI API"}


@app.get("/hello", summary="Say Hello", description="Returns a hello greeting message")
async def say_hello():
    return {"message": "Hello from Agentic AI!"}


@app.get("/health", summary="Health Check", description="Check if the API is running")
async def health_check():
    return {"status": "healthy"}
