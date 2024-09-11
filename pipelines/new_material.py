import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import re
import logging

# Initialize the LLM
os.environ["GROQ_API_KEY"] = ""
llm = ChatGroq(
    model="llama3-70b-8192",
    temperature=0.5,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

logger = logging.getLogger(__name__)

def get_filtered_components(content_purposes, key_messages):
    filtered_components = []
    material_repo = "material_repo"
    for category in os.listdir(material_repo):
        category_path = os.path.join(material_repo, category)
        if os.path.isdir(category_path):
            for component in os.listdir(category_path):
                component_id = f"{category}-{component.replace('.html', '')}"
                # Split the filename, but join all parts except the last one for the purpose
                parts = component.replace('.html', '').split('_')
                purpose = '_'.join(parts[:-1])
                message = parts[-1]
                if (not content_purposes or purpose in content_purposes) and (not key_messages or message in key_messages):
                    with open(os.path.join(category_path, component), 'r') as f:
                        content = f.read()
                    filtered_components.append({"id": component_id, "content": content})
    return filtered_components

def generate_email(prompt, content_purposes, key_messages):
    logger.info("Starting email generation")
    logger.info(f"Prompt: {prompt}")
    logger.info(f"Content purposes: {content_purposes}")
    logger.info(f"Key messages: {key_messages}")

    # Convert single strings to lists
    if isinstance(content_purposes, str):
        content_purposes = [content_purposes]
    if isinstance(key_messages, str):
        key_messages = [key_messages]

    # Get filtered components
    components = get_filtered_components(content_purposes, key_messages)
    logger.info(f"Found {len(components)} matching components")

    if not components:
        logger.warning("No matching components found")
        return "<p>No matching components found for the given criteria.</p>"

    # Prepare the prompt for the LLM
    component_info = "\n".join([f"ID: {c['id']}\nContent: {c['content']}" for c in components])
    llm_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant tasked with creating an email from pre-made components."),
        ("human", f"""
        Given the following email components and the user's prompt, select and order the components to create a cohesive email.
        Return only a comma-separated list of component IDs in the order they should appear in the email.

        User Prompt: {prompt}

        Available Components:
        {component_info}

        You will provide the ordered Component IDs as a comma-separated list tagged by <ordered_components>.

        Example:
        <ordered_components>
        component1,component2,component3
        </ordered_components>

        """)
    ])

    try:
        # Get the ordered component IDs from the LLM
        response = llm(llm_prompt.format_messages())
        ordered_ids = [id.strip() for id in re.search(r'<ordered_components>(.*?)</ordered_components>', response.content, re.DOTALL).group(1).split(',')]
        logger.info(f"Ordered component IDs: {ordered_ids}")

        return ordered_ids
    except Exception as e:
        logger.error(f"Error in generate_email: {str(e)}")
        return []

# Example usage:
# email_html = generate_email("Create an email about the efficacy of Oncozen", ["Clinical efficacy"], ["Efficacy breakthrough"])
