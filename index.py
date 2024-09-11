from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pipelines.new_material import generate_email
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
import secrets
import uuid
from shared import email_cache

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Generate a random secret key
SECRET_KEY = secrets.token_urlsafe(32)

# Add SessionMiddleware with more specific settings
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="email_generator_session",
    max_age=3600,  # 1 hour
    same_site="lax",
    https_only=False  # Set to True if you're using HTTPS
)

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("prompt.html", {"request": request})

@app.post("/generate-email")
async def generate_email_endpoint(
    request: Request,
    prompt: str = Form(...),
    content_purposes: list = Form(...),
    key_messages: list = Form(...)
):
    try:
        ordered_ids = generate_email(prompt, content_purposes, key_messages)
        logger.info("Email components generated successfully")
        
        # Generate a unique ID for this email
        email_id = str(uuid.uuid4())
        
        # Store the ordered component IDs in the cache
        email_cache[email_id] = ordered_ids
        
        # Store the email ID in the session
        request.session["email_id"] = email_id
        
        logger.info(f"Email ID {email_id} stored in session")
        return RedirectResponse(url=f"/editor/?email_id={email_id}", status_code=303)
    except Exception as e:
        logger.error(f"Error generating email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-session")
async def test_session(request: Request):
    count = request.session.get("count", 0)
    count += 1
    request.session["count"] = count
    return {"count": count}

@app.get("/features", response_class=HTMLResponse)
async def features(request: Request):
    return templates.TemplateResponse("features.html", {"request": request})

@app.get("/content_gen_feature", response_class=HTMLResponse)
async def content_gen_feature(request: Request):
    return templates.TemplateResponse("content_gen_feature.html", {"request": request})

# Import the editor router after defining the app
from editor.index import router as editor_router
app.include_router(editor_router, prefix="/editor")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)