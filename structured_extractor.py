from dotenv import load_dotenv
from langchain_groq import ChatGroq

from schemas import Invoice


load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)


# json_schema forces a schema-shaped reply. The default function-calling mode
# let the model answer in plain text, which Groq rejects as tool_use_failed.
structured_llm = llm.with_structured_output(Invoice, method="json_schema")


def structured_extract(text: str) -> Invoice:
    return structured_llm.invoke(text)