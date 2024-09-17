import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import os
import yaml
from dotenv import load_dotenv

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
        temperature=0.2,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=os.getenv("OPENAI_API_KEY")
    )

# Load the taxonomy
with open('GAIT/config/taxonomy.json', 'r') as f:
    taxonomy = json.load(f)['taxonomy']

# Create a string representation of the taxonomy for the prompt
taxonomy_str = "\n".join([
    f"{field['field']}:\n" + 
    "\n".join([f"- {value['value']}: {value['definition']}" for value in field['values']])
    for field in taxonomy
])

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        f"""You are an expert in analyzing and tagging medical content based on a given taxonomy. 
        Your task is to analyze the given content and assign the most relevant tags from each category in the taxonomy.
        
        Here's the taxonomy:
        
        {taxonomy_str}
        """
    ),
    (
        "human",
        """
        Please analyze the following content and provide the most relevant tags from each category:

        {content}

        Provide your response using XML-like tags for each field from the taxonomy. 
        If multiple values are relevant for a category, include them as comma-separated values within the tag.
        If no relevant tag is found for a category, use an empty tag.

        Example output:
        <Content_Type>Product Monograph</Content_Type>
        <Target_Audience>Oncologists, Pharmacists</Target_Audience>
        <Disease_Area>Breast Cancer</Disease_Area>
        <Product_Name>Oncozen</Product_Name>
        <Key_Message>Efficacy breakthrough, Precision medicine</Key_Message>
        <Content_Purpose>Clinical efficacy, Mechanism of action</Content_Purpose>
        <Communication_Channel>Digital</Communication_Channel>
        <Stage_in_Customer_Journey>Consideration</Stage_in_Customer_Journey>
        <Clinical_Focus>Treatment</Clinical_Focus>
        <Patient_Population>Newly Diagnosed</Patient_Population>
        <Treatment_Phase>First-line</Treatment_Phase>
        <Mechanism_of_Action>Targeted Therapy</Mechanism_of_Action>
        <Competitive_Positioning>Best-in-class</Competitive_Positioning>
        <Scientific_Evidence_Level>Phase 3 Trial</Scientific_Evidence_Level>
        """
    )
])

chain = prompt | llm

def tag_content(content):
    result = chain.invoke({"content": content})
    tagged_content = result.content

    # Extract tag values using regex
    tags = {}
    for field in taxonomy:
        field_name = field['field'].replace(' ', '_')
        pattern = f'<{field_name}>(.*?)</{field_name}>'
        match = re.search(pattern, tagged_content, re.DOTALL)
        if match:
            values = [v.strip() for v in match.group(1).split(',')]
            tags[field['field']] = values
        else:
            tags[field['field']] = []

    return tags
