from dotenv import load_dotenv
from langchain_groq import ChatGroq

from schemas import Invoice


load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)


structured_llm = llm.with_structured_output(Invoice)


def structured_extract(text: str) -> Invoice:
    return structured_llm.invoke(text)