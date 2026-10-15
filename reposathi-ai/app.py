
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import ollama

from sample_project.searcher import search_code
app = FastAPI(title="RepoSathi AI")

PROJECT_ROOT = Path(__file__).parent / "sample_project"
MAX_FILE_SIZE = 50_000


class AskRequest(BaseModel):
    question: str
    file_name: str | None = None


@app.get("/")
def home():
    return {"message": "RepoSathi AI backend is running!"}



@app.post("/ask")
def ask(request: AskRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    context = ""

    if request.file_name:
        if not request.file_name.endswith(".py"):
            raise HTTPException(
                status_code=400,
                detail="Only Python files are allowed",
            )

        root = PROJECT_ROOT.resolve()
        target = (root / request.file_name).resolve()

        if not target.is_relative_to(root) or target == root:
            raise HTTPException(
                status_code=400,
                detail="File must be inside sample_project",
            )

        if not target.is_file():
            raise HTTPException(
                status_code=404,
                detail="File not found",
            )

        if target.stat().st_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File is too large",
            )

        try:
            code = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            raise HTTPException(
                status_code=400,
                detail="Could not read the requested file",
            )

        context = (
            f"File: {request.file_name}\n"
            f"Code:\n```python\n{code}\n```"
        )

    else:
        results = search_code(question)

        # Temporary debug output in the VS Code terminal
        print("SEARCH RESULTS:", results)

        if results:
            matches = "\n".join(
                f"{item['file']}:{item['line']} — {item['code']}"
                for item in results[:10]
            )
            context = f"Relevant code search results:\n{matches}"
        else:
            context = (
                "No exact keyword matches were found. "
                "Do not claim that matching code was found."
            )

    prompt = (
        f"User question: {question}\n\n"
        f"{context}\n\n"
        "Explain relevant code to a beginner in simple language. "
        "When search results are provided, mention their file names "
        "and line numbers. Do not invent file contents."
    )

    try:
        response = ollama.chat(
            model="gemma3:1b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are RepoSathi AI, a coding assistant for "
                        "beginners. Explain code clearly and accurately. "
                        "Never invent file contents or line numbers."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        return {"answer": response["message"]["content"]}

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="AI unavailable. Check that Ollama is running.",
        )
