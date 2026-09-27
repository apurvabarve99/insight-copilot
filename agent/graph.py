from langgraph.graph import StateGraph, START, END

from agent.state import AgentState
from agent.nodes import (
    analyze_query,
    create_plan,
    run_selected_tools,
    process_results,
    generate_insight,
    handle_unsupported
)


def route_after_plan(state):
    """
    Decide whether the question is supported
    by the available analyses.
    """
    if state.get("analysis_type") == "unsupported":
        return "unsupported"

    return "supported"


graph_builder = StateGraph(AgentState)

graph_builder.add_node("analyze_query", analyze_query)
graph_builder.add_node("create_plan", create_plan)
graph_builder.add_node("run_selected_tools", run_selected_tools)
graph_builder.add_node("process_results", process_results)
graph_builder.add_node("generate_insight", generate_insight)
graph_builder.add_node("handle_unsupported", handle_unsupported)

graph_builder.add_edge(START, "analyze_query")
graph_builder.add_edge("analyze_query", "create_plan")

graph_builder.add_conditional_edges(
    "create_plan",
    route_after_plan,
    {
        "supported": "run_selected_tools",
        "unsupported": "handle_unsupported"
    }
)

graph_builder.add_edge(
    "run_selected_tools",
    "process_results"
)

graph_builder.add_edge(
    "process_results",
    "generate_insight"
)

graph_builder.add_edge(
    "generate_insight",
    END
)

graph_builder.add_edge(
    "handle_unsupported",
    END
)

graph = graph_builder.compile()