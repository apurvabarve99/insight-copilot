import streamlit as st

from agent.graph import graph


st.set_page_config(
    page_title="Insight Copilot",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Insight Copilot")
st.write(
    "Ask questions about the sales dataset and get "
    "data-driven insights."
)


# --------------------------------------------------
# Conversation History
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []


# --------------------------------------------------
# Display Previous Messages
# --------------------------------------------------
for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])


# --------------------------------------------------
# User Input
# --------------------------------------------------
user_query = st.chat_input("Ask a question about the sales data...")


if user_query:

    # --------------------------------------------------
    # Store and Display User Message
    # --------------------------------------------------
    st.session_state.messages.append({
        "role": "user",
        "content": user_query
    })

    with st.chat_message("user"):
        st.write(user_query)


    # --------------------------------------------------
    # Run LangGraph
    # --------------------------------------------------
    with st.chat_message("assistant"):

        with st.status(
            "🤔 Analyzing your question...",
            expanded=True
        ):
            result = graph.invoke({
                "user_query": user_query,
                "chat_history": st.session_state.messages[:-1]
            })


        # --------------------------------------------------
        # Analysis Plan
        # --------------------------------------------------
        plan = result.get("plan", [])

        if plan:
            with st.expander(
                "🧠 Analysis Plan",
                expanded=True
            ):
                for step in plan:
                    st.write(f"• {step}")


        # --------------------------------------------------
        # Tools Used
        # --------------------------------------------------
        selected_tools = result.get(
            "selected_tools",
            []
        )

        if selected_tools:
            with st.expander("🔧 Tools Used"):
                for tool in selected_tools:
                    st.write(f"✓ {tool}")


        # --------------------------------------------------
        # Execution Log
        # --------------------------------------------------
        execution_log = result.get(
            "execution_log",
            []
        )

        if execution_log:
            with st.expander("⚙️ Execution Log"):
                for log in execution_log:
                    st.write(f"✓ {log}")


        # --------------------------------------------------
        # Final Answer
        # --------------------------------------------------
        final_answer = result["final_answer"]

        st.markdown("### 💡 Insight")
        st.write(final_answer)

        # Display visualization when available
        trend_chart = result.get("tool_results", {}).get("trend_chart")

        if trend_chart is not None:
            st.markdown("### 📈 Visualization")
            st.plotly_chart(
                trend_chart,
                use_container_width=True
            )


        # --------------------------------------------------
        # Store Assistant Response
        # --------------------------------------------------
        st.session_state.messages.append({
            "role": "assistant",
            "content": final_answer
        })