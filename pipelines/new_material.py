import os
import yaml
from dotenv import load_dotenv
import re
from langchain_core.prompts import ChatPromptTemplate
import sqlite3

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        max_retries=2,
        api_key=os.getenv("OPENAI_API_KEY")
    )

# ... rest of the file remains unchanged ...

async def generate_email_structure(prompt, content_purposes=None, key_messages=None):
    logger.info("Starting email structure generation")
    logger.info(f"Prompt: {prompt}")
    logger.info(f"Content purposes: {content_purposes}")
    logger.info(f"Key messages: {key_messages}")

    # Get available component types
    material_repo = "material_repo"
    available_types = [d for d in os.listdir(material_repo) if os.path.isdir(os.path.join(material_repo, d))]
    logger.info(f"Available component types: {available_types}")

    # Generate list of required components
    type_order_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant helping to structure an email."),
        ("human", """
        Given the following component types: {available_types}
        And considering the email prompt: {prompt}
        Content purposes: {content_purposes}
        Key messages: {key_messages}

        Please provide an ordered list of component types that would create a well-structured email.
        Respond with only the ordered list wrapped in XML tags, like this:
        <ordered_types>type1, type2, type3</ordered_types>
         
        Subject line must be first and footer must be last.
        """)
    ])

    logger.info("Sending prompt to LLM")  # Add this line
    type_order_response = await llm.ainvoke(type_order_prompt.format_messages(
        available_types=', '.join(available_types),
        prompt=prompt,
        content_purposes=', '.join(content_purposes) if content_purposes else 'Any',
        key_messages=', '.join(key_messages) if key_messages else 'Any'
    ))
    logger.info(f"Received response from LLM: {type_order_response.content}")  # Add this line

    ordered_types = [t.strip() for t in re.search(r'<ordered_types>(.*?)</ordered_types>', type_order_response.content, re.DOTALL).group(1).split(',')]
    logger.info(f"Ordered component types: {ordered_types}")

    return ordered_types

async def generate_email_components(prompt, ordered_types, content_purposes=None, key_messages=None):
    generated_components = []
    for component_type in ordered_types:
        components = get_filtered_components([component_type], content_purposes, key_messages)
        logger.info(f"Filtered components for {component_type}: {components}")
        
        if not components:
            logger.warning(f"No matching components found for type: {component_type}")
            continue

        component_info = "\n".join([f"ID: {c['id']}\nContent: {c['content']}" for c in components])
        selection_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI assistant helping to select the most appropriate email component."),
            ("human", """
            Given the following email component options for the type '{component_type}':

            {component_info}

            And considering:
            - Email prompt: {prompt}
            - Content purposes: {content_purposes}
            - Key messages: {key_messages}
            - Previously selected components: {selected_components}

            Please select the most appropriate component ID for this email.
            If none of the options are suitable, respond with 'None of the above'.
            Respond with only the selected ID or 'None of the above', wrapped in XML tags like this:
            <selected_component>ID_here_or_none_of_the_above</selected_component>
            """)
        ])

        selection_response = await llm.ainvoke(selection_prompt.format_messages(
            component_type=component_type,
            component_info=component_info,
            prompt=prompt,
            content_purposes=', '.join(content_purposes) if content_purposes else 'Any',
            key_messages=', '.join(key_messages) if key_messages else 'Any',
            selected_components=', '.join(generated_components)
        ))
        selected_id = re.search(r'<selected_component>(.*?)</selected_component>', selection_response.content, re.DOTALL).group(1).strip()
        
        if selected_id != 'None of the above':
            logger.info(f"Selected component for {component_type}: {selected_id}")
            generated_components.append(selected_id)
            yield {"type": "component", "data": selected_id}
        else:
            logger.info(f"No suitable component found for {component_type}")

    yield {"type": "complete", "data": generated_components}

# Implement get_filtered_components function
import sqlite3
import os

def get_filtered_components(component_types, content_purposes=None, key_messages=None):
    conn = sqlite3.connect('data/components.db')
    cursor = conn.cursor()

    placeholders = ', '.join(['?' for _ in component_types])
    query = f"""
    SELECT id, component_type
    FROM component_tags
    WHERE component_type IN ({placeholders})
    """
    
    cursor.execute(query, component_types)
    results = cursor.fetchall()
    conn.close()

    filtered_components = []
    for id, component_type in results:
        file_path = os.path.join("material_repo", id)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            filtered_components.append({
                "id": id,
                "content": content,
                "component_type": component_type
            })

    logger.info(f"Filtered components: {[comp['id'] for comp in filtered_components]}")
    return filtered_components
