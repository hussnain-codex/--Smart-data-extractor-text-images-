
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import ToolMessage

from tools import calculate_invoice_total, check_invoice_date

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
)

# Register the available Python tools.
tools = [
    calculate_invoice_total,
    check_invoice_date,
]

tools_by_name = {tool.name: tool for tool in tools}

llm_with_tools = llm.bind_tools(tools)


def ask_with_tools(question: str, max_steps: int = 5):
    """Execute model-requested Python tools and return the final answer."""

    messages = [
        (
            "system",
            "Answer the user's question accurately. "
            "Use the available Python tools when calculations "
            "or invoice date checks are needed. "
            "Do not claim a tool was executed unless it was.",
        ),
        ("human", question),
    ]

    for step in range(max_steps):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        # No tool requested: return the model's final answer.
        if not response.tool_calls:
            print("\nAI response:")
            print(response.content)
            return response.content

        # Execute each requested tool.
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            print(f"\nExecuting tool: {tool_name}")
            print(f"Arguments: {tool_args}")

            selected_tool = tools_by_name.get(tool_name)

            if selected_tool is None:
                tool_result = f"Error: Unknown tool '{tool_name}'."
            else:
                try:
                    tool_result = selected_tool.invoke(tool_args)
                except Exception as error:
                    tool_result = (
                        f"Tool execution failed: "
                        f"{type(error).__name__}: {error}"
                    )

            print(f"Tool result: {tool_result}")

            # Return the tool result to the model.
            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call_id,
                )
            )

    raise RuntimeError(
        f"Stopped after {max_steps} tool-calling steps."
    )


if __name__ == "__main__":
    print("=== Smart Data Extractor: Python Tool Calling ===")

    question = input("\nEnter your question: ").strip()

    if question:
        try:
            ask_with_tools(question)
        except Exception as error:
            print(
                f"\nError: {type(error).__name__}: {error}"
            ) 
            