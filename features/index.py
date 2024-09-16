from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from pipelines.new_material import generate_email
from shared import email_cache
from editor.component.index import router as component_router
import logging
logger = logging.getLogger(__name__)

router = APIRouter()

router.include_router(component_router, prefix="/component")

templates = Jinja2Templates(directory="templates")