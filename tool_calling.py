import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import ToolMessage

from tools import calculate_invoice_total, check_invoice_date
from image_extractor import analyze_image

load_dotenv()

# Supported image formats
IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp",
    ".bmp", ".gif", ".tif", ".tiff"
}


# -----------------------------
# 1. Initialize Groq
# -----------------------------

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
)

tools = [
    calculate_invoice_total,
    check_invoice_date,
]

tools_by_name = {
    tool.name: tool
    for tool in tools
}

llm_with_tools = llm.bind_tools(tools)


# -----------------------------
# 2. Detect an image path
# -----------------------------

def find_image_path(question: str):
    """
    Detect an image path entered by itself or included
    in a question. Handles paths containing spaces.
    """

    text = question.strip()

    # First, check whether the complete input is a path.
    candidate = Path(text.strip('"').strip("'")).expanduser()

    if candidate.is_file() and candidate.suffix.lower() in IMAGE_EXTENSIONS:
        return candidate

    # Check quoted paths, including paths containing spaces.
    quoted_paths = re.findall(r"""["']([^"']+)["']""", text)

    for value in quoted_paths:
        path = Path(value).expanduser()

        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            return path

    # Look for Windows absolute paths, Unix absolute paths,
    # or relative paths such as images/test_image.png.
    pattern = re.compile(
        r"""(?P<path>(?:[A-Za-z]:[\\/]|/|\.{1,2}[\\/]|~[\\/])[^"'\r\n]*?\.(?:png|jpe?g|webp|bmp|gif|tiff?))""",
        re.IGNORECASE,
    )

    for match in pattern.finditer(text):
        value = match.group("path").strip()
        path = Path(value).expanduser()

        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            return path

    # Support a relative path beginning with a folder name,
    # for example: images/my receipt.png
    pattern = re.compile(
        r"""(?<!\S)(?P<path>[\w .()\-]+[\\/][^"'\r\n]*?\.(?:png|jpe?g|webp|bmp|gif|tiff?))""",
        re.IGNORECASE,
    )

    for match in pattern.finditer(text):
        value = match.group("path").strip()
        path = Path(value).expanduser()

        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            return path

    return None


# -----------------------------
# 3. Analyze images with Gemini
# -----------------------------

def handle_image(image_path: Path):
    print("\nImage detected!")
    print(f"File: {image_path.resolve()}")
    print("Sending image to Gemini...\n")

    result = analyze_image(str(image_path))

    output = result.model_dump_json(indent=2)

    print("\n" + "=" * 50)
    print("IMAGE ANALYSIS RESULT")
    print("=" * 50)
    print(output)

    output_path = Path("image_result.json")

    output_path.write_text(
        output,
        encoding="utf-8",
    )

    print(f"\nResult saved to: {output_path.resolve()}")

    return output


# -----------------------------
# 4. Handle text with Groq tools
# -----------------------------

def ask_with_tools(question: str, max_steps: int = 5):
    """Answer text questions and execute requested Python tools."""

    messages = [
        (
            "system",
            "Answer the user's question accurately. "
            "Use the available Python tools when calculations "
            "or invoice date checks are needed. "
            "Do not claim a tool was executed unless it was.",
            "analyze the image and provide a detailed description of its contents, including any text, objects, or notable features.",
        ),
        ("human", question),
    ]

    for step in range(max_steps):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            print("\nAI response:")
            print(response.content)
            return response.content

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

            messages.append(
                ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call_id,
                )
            )

    raise RuntimeError(
        f"Stopped after {max_steps} tool-calling steps."
    )


# -----------------------------
# 5. Unified input handler
# -----------------------------

def process_input(question: str):
    """Route image inputs to Gemini and other inputs to Groq."""

    question = question.strip()

    if not question:
        print("Please enter a question or image path.")
        return

    image_path = find_image_path(question)

    if image_path is not None:
        return handle_image(image_path)

    return ask_with_tools(question)


# -----------------------------
# 6. Run the application
# -----------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("SMART DATA EXTRACTOR")
    print("Text + Invoice Tools + Image Analysis")
    print("=" * 50)

    print("\nExamples:")
    print("  What is 125 multiplied by 8?")
    print("  Check whether this invoice date is valid.")
    print("  images/test_image.png")
    print("  Analyze the image at images/test_image.png")
    print("\nType 'exit' to quit.")

    while True:
        try:
            question = input("\nEnter your question: ").strip()

            if question.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break

            process_input(question)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        except Exception as error:
            print(
                f"\nError: {type(error).__name__}: {error}"
            )
