import itertools
from langchain_groq import ChatGroq
import os
import re

# Ensure you have set your OpenAI API key in your environment variables
os.environ["GROQ_API_KEY"] = ""

llm = ChatGroq(
    model="llama3-70b-8192",
    temperature=0.5,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)


# Content Purposes and Key Messages (as before)
content_purposes = [
    "Clinical efficacy",
    "Safety profile",
    "Mechanism of action",
    "Patient selection",
    "Administration and dosing",
    "Comparative data",
    "Cost-effectiveness",
    "Guidelines and recommendations",
    "Real-world evidence",
    "Pipeline information",
    "Expert opinions",
    "Patient-reported outcomes",
    "Combination therapy potential",
    "Regulatory information",
    "Support services"
]

key_messages = [
    "Efficacy breakthrough",
    "Precision medicine",
    "Quality of life focus",
    "Innovative mechanism",
    "Practice-changing potential",
    "Simplified treatment regimen",
    "Synergistic combinations",
    "Robust safety profile",
    "Cost-effective innovation",
    "Personalized patient support",
    "Continuous innovation",
    "Real-world reliability"
]

# Email components
email_components = [
    "clinical_data",
    "cta",
    "dosing",
    "footer",
    "greetings",
    "introduction",
    "key_message",
    "safety_information",
    "subject_lines"
]

# Generate all possible combinations
combinations = list(itertools.product(content_purposes, key_messages, email_components))

from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are creating a reusable component for an oncology drug named {drug_name}."
        ),
        (
            "human",
            """Content Purpose: {content_purpose}
            Key Message: {key_message}
            Email Component: {email_component}
            
            Based on the above information, generate appropriate content for the specified email component. DO NOT generate the whole email.
            Ensure the content aligns with the content purpose and key message while being suitable for healthcare professionals.
            Keep the tone professional and informative.

            You will respond with html, be sure to wrap it in "<html></html>" as normal
            You will use tailwind for styling. Make it attractive. 
            """
        )
    ]
)

def html_extractor(text):
    # Extract the entire HTML content, including <html> tags
    match = re.search(r'(<html>.*?</html>)', text.content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)
    else:
        # If no HTML tags found, wrap the original text in basic HTML structure
        return f"<html><body>{text}</body></html>"

chain = prompt | llm | html_extractor

# Generate and save content
def generate_and_save_content(combinations):
    for i, combo in enumerate(combinations, 1):
        content_purpose, key_message, email_component = combo
        
        content = chain.invoke(
            {
            "drug_name": "Oncozen",
            "content_purpose": content_purpose,
            "key_message": key_message,
            "email_component": email_component
            }
        )
        
        # Create the directory path
        dir_path = os.path.join("material_repo", email_component)
        os.makedirs(dir_path, exist_ok=True)
        
        # Create the file path
        file_path = os.path.join(dir_path, f"{content_purpose}_{key_message}.html")
        
        # Write the HTML content to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Saved content for {email_component} - {content_purpose} - {key_message} to {file_path}")

    print("\nAll content has been generated and saved.")

# Generate content for all combinations
generate_and_save_content(combinations)