import logging
import json
import sqlite3
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

router = APIRouter()

DB_PATH = 'data/components.db'

def get_impact_repository_items():
    logger.info("Fetching impact repository items")
    conn = sqlite3.connect('data/components.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT category FROM component_performance")
    categories = [row[0] for row in cursor.fetchall()]
    logger.info(f"Found categories: {categories}")
    
    impact_repository_items = {}
    for category in categories:
        cursor.execute("SELECT DISTINCT component_id FROM component_performance WHERE category = ?", (category,))
        components = [{"id": row[0], "name": row[0].split('-')[-1]} for row in cursor.fetchall()]
        impact_repository_items[category] = components
    
    conn.close()
    logger.info(f"Impact repository items: {json.dumps(impact_repository_items)}")
    return impact_repository_items

@router.get("/", response_class=HTMLResponse)
async def material_performance(request: Request):
    impact_repository_items = get_impact_repository_items()
    return templates.TemplateResponse("Material performance.html", {"request": request, "impact_repository_items": impact_repository_items})

def get_component_tags(component_id: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT tags FROM component_tags WHERE id = ?", (component_id,))
        result = c.fetchone()
        conn.close()

        if result:
            tags = json.loads(result[0])
            # If tags is a list, convert it to a dictionary
            if isinstance(tags, list):
                return {"Tags": tags}
            return tags
        else:
            return {}
    except Exception as e:
        logger.error(f"Error retrieving component tags: {str(e)}")
        return {}

def get_average_ctr(component_type, persona, tag=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    if tag:
        query = '''
        SELECT AVG(cp.ctr) as avg_ctr
        FROM component_performance cp
        JOIN component_tags ct ON cp.component_id = ct.id
        WHERE cp.component_id LIKE ? AND cp.persona = ? AND ct.tags LIKE ?
        AND cp.date BETWEEN ? AND ?
        '''
        cursor.execute(query, (f"{component_type}-%", persona, f"%{tag}%", start_date, end_date))
    else:
        query = '''
        SELECT AVG(ctr) as avg_ctr
        FROM component_performance
        WHERE component_id LIKE ? AND persona = ?
        AND date BETWEEN ? AND ?
        '''
        cursor.execute(query, (f"{component_type}-%", persona, start_date, end_date))
    
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] is not None else 0

@router.get("/api/component-performance/{component_id:path}")
async def component_performance(component_id: str):
    logger.info(f"Received request for component_id: {component_id}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        query = '''
        SELECT persona, AVG(ctr) as avg_ctr
        FROM component_performance
        WHERE component_id = ?
        AND date BETWEEN ? AND ?
        GROUP BY persona
        '''
        logger.info(f"Executing query: {query}")
        logger.info(f"Query parameters: component_id={component_id}, start_date={start_date}, end_date={end_date}")
        
        cursor.execute(query, (component_id, start_date, end_date))
        results = cursor.fetchall()

        if not results:
            logger.warning(f"No data found for component: {component_id} within the date range")
            return JSONResponse({
                "error": f"No data found for the specified component: {component_id} within the date range"
            }, status_code=404)

        personas = []
        ctr_values = []
        type_avg_ctr_values = []
        tag_avg_ctr_values = []
        component_type = component_id.split('-')[0]
        tags = get_component_tags(component_id)

        for persona, avg_ctr in results:
            personas.append(persona)
            ctr_values.append(round(avg_ctr, 2))
            
            # Get average CTR for the component type
            type_avg_ctr = get_average_ctr(component_type, persona)
            type_avg_ctr_values.append(round(type_avg_ctr, 2))
            
            # Get average CTR for each tag
            tag_avg_ctrs = {}
            for category, tag_list in tags.items():
                if isinstance(tag_list, list):
                    for tag in tag_list:
                        tag_avg_ctr = get_average_ctr(component_type, persona, tag)
                        tag_avg_ctrs[tag] = round(tag_avg_ctr, 2)
                else:
                    tag_avg_ctr = get_average_ctr(component_type, persona, tag_list)
                    tag_avg_ctrs[tag_list] = round(tag_avg_ctr, 2)
            
            tag_avg_ctr_values.append(tag_avg_ctrs)

        # Log the data for debugging
        logger.info(f"Personas: {personas}")
        logger.info(f"CTR values: {ctr_values}")
        logger.info(f"Type average CTR values: {type_avg_ctr_values}")
        logger.info(f"Tag average CTR values: {tag_avg_ctr_values}")
        
        return JSONResponse({
            "name": component_id,
            "personas": personas,
            "ctr_values": ctr_values,
            "type_avg_ctr_values": type_avg_ctr_values,
            "tag_avg_ctr_values": tag_avg_ctr_values,
            "tags": tags
        })

    except Exception as e:
        logger.error(f"Error processing request for component_id {component_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()

@router.get("/component/{component_id}", response_class=HTMLResponse)
async def get_component(component_id: str):
    logger.info(f"Fetching component content for: {component_id}")
    try:
        category, component_name = component_id.split('-', 1)
        file_path = f"material_repo/{category}/{component_name}.html"
        
        if not os.path.exists(file_path):
            logger.warning(f"Component not found: {file_path}")
            raise HTTPException(status_code=404, detail="Component not found")
        
        with open(file_path, "r") as file:
            content = file.read()
        
        logger.info(f"Successfully retrieved content for component: {component_id}")
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error fetching component content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching component content: {str(e)}")