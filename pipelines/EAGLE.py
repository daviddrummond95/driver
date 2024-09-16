from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

llm = ChatGroq(
    model="llama3-70b-8192",
    temperature=0.2,
    max_tokens=None,
    timeout=None,
    max_retries=2,
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
        """
    )
])

chain = prompt | llm

def check_mlr_compliance(html_content):
    result = chain.invoke({"html_content": html_content})
    return result.content
