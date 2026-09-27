from typing import Any, TypedDict


class AgentState(TypedDict, total=False):

    user_query: str

    chat_history: list[dict[str, str]]

    context_entity: str

    plan: list[str]

    selected_tools: list[str]

    tool_results: dict[str, Any]

    execution_log: list[str]

    final_answer: str

    analysis_type: str