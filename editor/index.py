from fastapi import APIRouter, Request, HTTPException, Form, Depends, WebSocket
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import os
from shared import email_cache
from editor.component.index import router as component_router
from editor.utils import get_repository_items
import logging
import uuid
import json

logger = logging.getLogger(__name__)

router = APIRouter()

router.include_router(component_router, prefix="/component")

templates = Jinja2Templates(directory="templates")

@router.get("/")
async def read_root(request: Request):
    logger.info("Accessing editor root")
    email_id = request.query_params.get("email_id") or str(uuid.uuid4())
    generated_email_components = []
    if email_id in email_cache:
        logger.info(f"Found generated email components with ID {email_id}")
        generated_email_components = [get_component_content(component_id) for component_id in email_cache[email_id].get("components", [])]
    else:
        logger.info(f"No generated email found for ID {email_id}")
    
    # Check if the 'new_component' query parameter is present
    if request.query_params.get("new_component"):
        return RedirectResponse(url=f"/editor/component/new_component?email_id={email_id}")
    
    return templates.TemplateResponse("constructor.html", {
        "request": request, 
        "generated_email_components": generated_email_components,
        "email_id": email_id
    })

def get_component_content(component_id):
    try:
        category, component_name = component_id.split('/', 1)
    except ValueError:
        # If the component_id doesn't contain a slash, use it as the component_name
        category = "unknown"
        component_name = component_id

    file_path = f"material_repo/{category}/{component_name}"
    
    if not os.path.exists(file_path):
        return f"<p>Component not found: {component_id}</p>"
    
    with open(file_path, "r") as file:
        content = file.read()
    
    return content

@router.get("/repository", response_class=HTMLResponse)
async def get_repository(request: Request):
    logger.info("Accessing repository")
    repository_items = get_repository_items()
    logger.info(f"Repository items: {repository_items}")
    return templates.TemplateResponse("repository_partial.html", {"request": request, "repository_items": repository_items})

@router.post("/add_to_repository")
async def add_to_repository(request: Request, component_type: str = Form(...), content: str = Form(...)):
    try:

        # After successfully saving the component, get the updated repository items
        updated_repository_items = get_repository_items()

        # Return the updated repository HTML
        return templates.TemplateResponse("repository_partial.html", {
            "request": request,
            "repository_items": updated_repository_items
        })
    except Exception as e:
        logger.error(f"Error saving component to repository: {str(e)}")
        return JSONResponse({
            "success": False,
            "message": "Failed to add component to repository"
        }, status_code=500)

@router.get("/document")
async def get_document(request: Request):
    logger.info("Accessing document")
    email_id = request.session.get("email_id")
    generated_email = email_cache.get(email_id) if email_id else None
    if generated_email:
        logger.info(f"Found generated email with ID {email_id} for document")
        logger.debug(f"Email content: {generated_email[:100]}...")  # Log first 100 chars
    else:
        logger.info("No generated email found for document")
    return templates.TemplateResponse("document.html", {"request": request, "generated_email": generated_email})

@router.post("/generate-email")
async def generate_email_endpoint(
    request: Request,
    prompt: str = Form(...),
    content_purposes: str = Form(...),
    key_messages: str = Form(...)
):
    try:
        # Generate a unique ID for this email
        email_id = str(uuid.uuid4())
        
        # Store the email ID and generation parameters in the email_cache
        email_cache[email_id] = {
            "prompt": prompt,
            "content_purposes": content_purposes.split(','),
            "key_messages": key_messages.split(',')
        }
        
        logger.info(f"Email generation initiated for email_id: {email_id}")
        return JSONResponse({"email_id": email_id})
    except Exception as e:
        logger.error(f"Error initiating email generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/component/{component_id}", response_class=HTMLResponse)
async def get_component(component_id: str):
    category, component_name = component_id.split('-', 1)
    file_path = f"material_repo/{category}/{component_name}.html"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Component not found")
    
    with open(file_path, "r") as file:
        content = file.read()
    
    return content

@router.post("/finalize")
async def finalize_email(request: Request, email_content: str = Form(...), email_id: str = Form(...)):
    # You can use the email_id to retrieve any additional data from the cache if needed
    cached_components = email_cache.get(email_id, [])
    
    return templates.TemplateResponse("finalize.html", {
        "request": request, 
        "email_content": email_content,
        "email_id": email_id,
        "cached_components": cached_components
    })

@router.post("/upload")
async def upload_to_promomats(
    request: Request,
    email_name: str = Form(...),
    campaign_tags: str = Form(...),
    email_content: str = Form(...)
):
    # Here you would implement the actual upload to PromoMats
    # For now, we'll just simulate a successful upload
    logger.info(f"Uploading email '{email_name}' with tags: {campaign_tags}")
    return templates.TemplateResponse("upload_success.html", {
        "request": request,
        "email_name": email_name,
        "campaign_tags": campaign_tags,
        "email_content": email_content
    })

@router.post("/update-cache")
async def update_cache(data: dict):
    try:
        email_id = data.get("email_id")
        if not email_id:
            return JSONResponse({"success": False, "message": "No email ID provided"}, status_code=400)

        component_ids = data.get("component_ids", [])
        email_cache[email_id] = component_ids

        return JSONResponse({"success": True, "message": "Email cache updated successfully"})
    except Exception as e:
        logger.error(f"Error updating email cache: {str(e)}")
        return JSONResponse({"success": False, "message": f"Failed to update email cache: {str(e)}"}, status_code=500)

@router.get("/component/new_component", response_class=HTMLResponse)
async def new_component_page(request: Request):
    email_id = request.query_params.get("email_id")
    return templates.TemplateResponse("new_component_page.html", {"request": request, "email_id": email_id})

