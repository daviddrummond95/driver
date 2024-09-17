from fastapi import FastAPI, Request, Form, HTTPException, WebSocket
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pipelines.new_material import generate_email_structure, generate_email_components
from pipelines.new_component import new_component_page, generate_components
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
import secrets
import uuid
from shared import email_cache
import os
import asyncio
import json

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
    content_purposes: list = Form(None),
    key_messages: list = Form(None)
):
    try:
        email_id = str(uuid.uuid4())
        
        email_cache[email_id] = {
            "prompt": prompt,
            "content_purposes": content_purposes if content_purposes else None,
            "key_messages": key_messages if key_messages else None,
            "components": []  # Initialize an empty list to store generated components
        }
        
        logger.info(f"Email generation initiated for email_id: {email_id}")
        logger.info(f"Prompt: {prompt}")
        logger.info(f"Content purposes: {content_purposes}")
        logger.info(f"Key messages: {key_messages}")
        
        return RedirectResponse(url=f"/processing/?email_id={email_id}", status_code=303)
    except Exception as e:
        logger.error(f"Error initiating email generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/processing/")
async def processing_page(request: Request, email_id: str):
    return templates.TemplateResponse("processing.html", {"request": request, "email_id": email_id})

@app.websocket("/ws/{email_id}")
async def websocket_endpoint(websocket: WebSocket, email_id: str):
    await websocket.accept()
    try:
        logger.info(f"WebSocket connection established for email_id: {email_id}")

        email_data = email_cache.get(email_id, {})
        prompt = email_data.get("prompt")
        content_purposes = email_data.get("content_purposes")
        key_messages = email_data.get("key_messages")

        if not prompt:
            raise ValueError(f"No prompt found for email_id: {email_id}")

        ordered_types = await generate_email_structure(prompt, content_purposes, key_messages)
        await websocket.send_json({"type": "ordered_types", "data": ordered_types})

        generated_components = []
        async for component in generate_email_components(prompt, ordered_types, content_purposes, key_messages):
            if component['type'] == 'component':
                generated_components.append(component['data'])
                await websocket.send_json({"type": "component_generated", "data": component['data']})
            elif component['type'] == 'complete':
                email_cache[email_id]["components"] = generated_components
                await websocket.send_json({"type": "generation_complete", "email_id": email_id, "components": generated_components})

    except Exception as e:
        logger.error(f"Error in WebSocket: {str(e)}")
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        await websocket.close()

@app.get("/new-component")
async def new_component(request: Request):
    return await new_component_page(request)

@app.post("/generate-component")
async def generate_component(request: Request, prompt: str = Form(...), component_type: str = Form(...)):
    return await generate_components(request, prompt, component_type)

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

from components.index import router as component_router
app.include_router(component_router, prefix="/components")

# Add this new endpoint to retrieve generated components
@app.get("/editor/")
async def editor_page(request: Request, email_id: str):
    email_data = email_cache.get(email_id, {})
    generated_components = email_data.get("components", [])
    return templates.TemplateResponse("constructor.html", {
        "request": request,
        "email_id": email_id,
        "generated_email_components": generated_components
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")