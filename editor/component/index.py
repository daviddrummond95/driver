from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
import os
import json
import sqlite3

from pipelines.new_component import new_component_page, generate_components
from editor.utils import get_repository_items  # Import from utils instead of editor.index

import logging
logger = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(directory="templates")

DB_PATH = 'data/components.db'

@router.get("/new_component", response_class=HTMLResponse)
async def new_component(request: Request):
    return await new_component_page(request)

@router.post("/generate_component", response_class=HTMLResponse)
async def generate_component(request: Request, prompt: str = Form(...), component_type: str = Form(...)):
    return await generate_components(request, prompt, component_type)

@router.post("/add_to_repository")
async def add_to_repository(request: Request, component_type: str = Form(...), content: str = Form(...), tags: str = Form(...)):
    try:
        # Create the directory path
        dir_path = os.path.join("material_repo", component_type)
        os.makedirs(dir_path, exist_ok=True)
        
        # Create a unique filename
        file_name = f"{component_type}_{len(os.listdir(dir_path)) + 1}.html"
        file_path = os.path.join(dir_path, file_name)
        
        # Write the HTML content to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Save tags to SQLite database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        component_id = f"{component_type}-{file_name.replace('.html', '')}"
        c.execute("INSERT OR REPLACE INTO component_tags (id, tags) VALUES (?, ?)",
                  (component_id, tags))
        conn.commit()
        conn.close()

        # After successfully saving the component, get the updated repository items
        updated_repository_items = get_repository_items()

        # Return only the new component information
        new_component = {
            "id": f"{component_type}-{file_name.replace('.html', '')}",
            "name": file_name.replace('.html', '')
        }

        return JSONResponse({
            "success": True,
            "message": f"{component_type} component added to repository with tags",
            "file_path": file_path,
            "new_component": new_component,
            "component_type": component_type
        })
    except Exception as e:
        logger.error(f"Error saving component to repository: {str(e)}")
        return JSONResponse({
            "success": False,
            "message": "Failed to add component to repository"
        }, status_code=500)

@router.get("/get_component_tags/{component_id}")
async def get_component_tags(component_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT tags FROM component_tags WHERE id = ?", (component_id,))
        result = c.fetchone()
        conn.close()

        if result:
            return JSONResponse({
                "success": True,
                "tags": result[0]
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Component not found"
            }, status_code=404)
    except Exception as e:
        logger.error(f"Error retrieving component tags: {str(e)}")
        return JSONResponse({
            "success": False,
            "message": "Failed to retrieve component tags"
        }, status_code=500)