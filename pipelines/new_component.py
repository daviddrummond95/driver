import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import re
from fastapi import Request, Form
from fastapi.templating import Jinja2Templates
from pipelines.EAGLE import check_mlr_compliance  # Import the MLR compliance check function



llm = ChatGroq(
    model="llama3-70b-8192",
    temperature=0.5,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are creating a reusable component for an email about a medical product or service."
    ),
    (
        "human",
        """
        User Prompt: {user_prompt}
        Email Component: {email_component}
        
        Based on the above information, generate appropriate content for the specified email component.
        Ensure the content aligns with the user's prompt while being suitable for healthcare professionals.
        Keep the tone professional and informative.

        You will respond with html, be sure to wrap it in "<html></html>" as normal
        You will use tailwind for styling. Make it attractive. 
        """
    )
])

def html_extractor(text):
    match = re.search(r'(<html>.*?</html>)', text.content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)
    else:
        return f"<html><body>{text}</body></html>"

chain = prompt | llm | html_extractor

def generate_component(user_prompt, email_component):
    content = chain.invoke({
        "user_prompt": user_prompt,
        "email_component": email_component
    })
    component_html = f"""
<div class="component-content">
    {content}
</div>
"""
    return {
        "raw_content": content,
        "wrapped_content": component_html
    }

# FastAPI route handlers
templates = Jinja2Templates(directory="templates")

async def new_component_page(request: Request):
    email_id = request.query_params.get("email_id")
    return templates.TemplateResponse("new_component_page.html", {"request": request, "email_id": email_id})

async def generate_components(request: Request, prompt: str = Form(...), component_type: str = Form(...)):
    component = generate_component(prompt, component_type)
    
    # Check MLR compliance
    compliance_result = check_mlr_compliance(component["raw_content"])
    
    email_id = request.query_params.get("email_id")
    return templates.TemplateResponse("generated_components.html", {
        "request": request,
        "components": [{
            'type': component_type,
            'content': component["wrapped_content"],
            'compliance_result': compliance_result
        }],
        "email_id": email_id
    })
