import os
import yaml
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate

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

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert in Medical Legal Review (MLR) compliance for healthcare communications. Your task is to analyze the given HTML content and identify any potential compliance issues."
    ),
    (
        "human",
        """
        Please review the following HTML content for MLR compliance:

        {html_content}

        Analyze the content and provide a detailed report on any compliance issues found. If there are no issues, state that the content is compliant.

        Please respond in the proper HTML format and include a recommended new component that can be added to the page to fix the issues found.

        Example Output:
        <div class="mlr-review">
            <h3 class="text-lg font-semibold mb-2">MLR Compliance Report</h3>
            <h4 class="text-md font-semibold mb-1">Product Information Accuracy:</h4>
            <p>No issues found.</p>
            <h4 class="text-md font-semibold mb-1">Fair Balance:</h4>
            <p>No issues found.</p>
            <h4 class="text-md font-semibold mb-1">No Misleading Statements:</h4>
            <p>No issues found.</p>
            <h4 class="text-md font-semibold mb-1">No Unsubstantiated Benefits:</h4>
            <p>No issues found.</p>
            <h4 class="text-md font-semibold mb-1">Regulatory Requirements:</h4>
            <p>No issues found.</p>
            <h4 class="text-md font-semibold mb-1">Target Audience Appropriateness:</h4>
            <p>Not appropriate for the target audience. This content is too complex for the intended audience. The wording is too technical and the content is not tailored to the needs of the target audience.</p>
            <div class="recommended-component">
                <h4 class="text-md font-semibold mb-1">Recommended Component</h4>
                <div class="component-content">
                    <!-- Content of the recommended component -->
                </div>
            </div>
        </div>
        """
    )
])

chain = prompt | llm

def check_mlr_compliance(html_content):
    result = chain.invoke({"html_content": html_content})
    return result.content
