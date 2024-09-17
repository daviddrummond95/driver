import os
import json
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
import re
from fastapi import Request, Form
from fastapi.templating import Jinja2Templates
from pipelines.EAGLE import check_mlr_compliance  # Import the MLR compliance check function
from pipelines.GAIT import tag_content  # Import the GAIT tagging function
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()

# Load configuration
with open('model.yaml', 'r') as file:
    config = yaml.safe_load(file)

if config['environment'] == 'aws':
    from langchain_aws import ChatBedrock
    import boto3

    llm = ChatBedrock(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        model_kwargs=dict(temperature=0.5),
        client=boto3.client('bedrock-runtime', region_name='us-east-1')
    )
else:
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20240620",
        max_retries=2,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

# Load the taxonomy
with open('GAIT/config/taxonomy.json', 'r') as f:
    taxonomy = json.load(f)['taxonomy']

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
    
    # Tag content using GAIT
    gait_tags = tag_content(component["raw_content"])
    
    email_id = request.query_params.get("email_id")
    return templates.TemplateResponse("generated_components.html", {
        "request": request,
        "components": [{
            'type': component_type,
            'content': component["wrapped_content"],
            'compliance_result': compliance_result,
            'gait_tags': gait_tags  # Include GAIT tags in the response
        }],
        "email_id": email_id,
        "taxonomy": taxonomy  # Include taxonomy in the response
    })
