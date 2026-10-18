from langchain_core.messages import AIMessage

import tool_calling


def test_conversation_history_is_reused_across_turns(monkeypatch):
    observed_messages = []

    class FakeModel:
        def invoke(self, messages):
            observed_messages.append(list(messages))
            return AIMessage(content="I will remember Ali's name.")

    monkeypatch.setattr(tool_calling, "llm_with_tools", FakeModel())
    conversation = []

    tool_calling.ask_with_tools(
        "My name is Ali.",
        messages=conversation,
    )
    tool_calling.ask_with_tools(
        "I am learning Python.",
        messages=conversation,
    )
    tool_calling.ask_with_tools(
        "I am building an invoice extractor.",
        messages=conversation,
    )
    response = tool_calling.ask_with_tools(
        "What is my name?",
        messages=conversation,
    )

    assert response == "I will remember Ali's name."
    assert len(observed_messages) == 4
    assert len(observed_messages[-1]) > len(observed_messages[0])
    assert any(
        getattr(message, "content", None) == "My name is Ali."
        or message == ("human", "My name is Ali.")
        for message in observed_messages[-1]
    )
