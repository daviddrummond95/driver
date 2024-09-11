from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from pipelines.new_material import generate_email
from shared import email_cache

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(directory="templates")

def get_repository_items():
    repo_items = {}
    material_repo = "material_repo"
    for category in os.listdir(material_repo):
        category_path = os.path.join(material_repo, category)
        if os.path.isdir(category_path):
            components = []
            for component in os.listdir(category_path):
                component_id = f"{category}-{component.replace('.html', '')}"
                components.append({"id": component_id, "name": component.replace('.html', '')})
            repo_items[category] = components
    return repo_items

@router.get("/")
async def read_root(request: Request):
    logger.info("Accessing editor root")
    email_id = request.query_params.get("email_id") or request.session.get("email_id")
    generated_email_components = []
    if email_id:
        ordered_ids = email_cache.get(email_id)
        if ordered_ids:
            logger.info(f"Found generated email components with ID {email_id}")
            generated_email_components = [get_component_content(component_id) for component_id in ordered_ids]
        else:
            logger.info(f"No generated email found for ID {email_id}")
    else:
        logger.info("No email ID found in query params or session")
    return templates.TemplateResponse("constructor.html", {"request": request, "generated_email_components": generated_email_components})

def get_component_content(component_id):
    category, component_name = component_id.split('-', 1)
    file_path = f"material_repo/{category}/{component_name}.html"
    
    if not os.path.exists(file_path):
        return f"<p>Component not found: {component_id}</p>"
    
    with open(file_path, "r") as file:
        content = file.read()
    
    return content

@router.get("/repository")
async def get_repository(request: Request):
    logger.info("Accessing repository")
    repository_items = get_repository_items()
    return templates.TemplateResponse("repository.html", {"request": request, "repository_items": repository_items})

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
    prompt: str = Form(...),
    content_purposes: str = Form(...),
    key_messages: str = Form(...)
):
    content_purposes = [p.strip() for p in content_purposes.split(',')]
    key_messages = [m.strip() for m in key_messages.split(',')]
    
    email_html = generate_email(prompt, content_purposes, key_messages)
    return HTMLResponse(content=email_html)

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
async def finalize_email(request: Request, email_content: str = Form(...)):
    return templates.TemplateResponse("finalize.html", {"request": request, "email_content": email_content})

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




