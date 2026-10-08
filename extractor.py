import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)


def naive_extract(text: str):
    prompt = f"""
Extract the useful information from the text below.

Return ONLY valid JSON.
Do not include markdown.
Do not include ```json.
Do not include any explanation.

Text:
{text}
"""

    response = llm.invoke(prompt)

    return json.loads(response.content)