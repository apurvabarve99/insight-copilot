import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from tools.data_tool import get_top_n, get_grouped_summary
from tools.visualization_tool import create_monthly_chart
from utils.data_loader import load_data

load_dotenv()

def analyze_query(state):
    """
    Analyze the user's current question and identify the required
    analysis types and tools.

    Previous conversation is used only to resolve simple follow-up
    references such as "its trend".
    """
    query = state["user_query"].lower()
    chat_history = state.get("chat_history", [])

    selected_tools = []
    context_entity = ""

    # ---------------------------------------------------------
    # Resolve simple follow-up references
    # ---------------------------------------------------------
    if chat_history:
        recent_messages = chat_history[-4:]

        for message in reversed(recent_messages):
            if message["role"] == "assistant":
                content = message["content"]

                # Example:
                # "Tablet generated the highest revenue at 2,929,329."
                if "highest revenue is" in content:
                    context_entity = content.split(
                        "highest revenue is"
                    )[1].split("(")[0].strip()

                break

    # ---------------------------------------------------------
    # Trend / time-based analysis
    # ---------------------------------------------------------
    if (
        "trend" in query
        or "monthly" in query
        or "season" in query
        or "over the year" in query
        or "over time" in query
    ):
        selected_tools.append("trend")

    # ---------------------------------------------------------
    # Anomaly analysis
    # ---------------------------------------------------------
    if (
        "anomal" in query
        or "unusual" in query
    ):
        selected_tools.append("anomaly")

    # ---------------------------------------------------------
    # Ranking analysis
    # ---------------------------------------------------------
    if (
        "top" in query
        or "highest" in query
        or "lowest" in query
        or "best" in query
        or "most" in query
    ):
        selected_tools.append("ranking")

    # ---------------------------------------------------------
    # Comparison analysis
    # ---------------------------------------------------------
    if (
        "compare" in query
        or "comparison" in query
    ):
        selected_tools.append("comparison")

        # ---------------------------------------------------------
    # Calculation / summary analysis
    # ---------------------------------------------------------
    if (
        "total" in query
        or "sum" in query
        or "overall" in query
        or "percentage change" in query
        or "change" in query
    ):
        selected_tools.append("calculation")

    # ---------------------------------------------------------
    # If no supported analysis was detected
    # ---------------------------------------------------------
    if not selected_tools:
        analysis_type = "unsupported"
    else:
        analysis_type = selected_tools[0]

    return {
        "analysis_type": analysis_type,
        "selected_tools": selected_tools,
        "context_entity": context_entity
    }

def create_plan(state):
    """
    Create a short analysis plan based on the selected tools.
    """

    selected_tools = state.get("selected_tools", [])
    analysis_type = state.get("analysis_type")

    # ---------------------------------------------------------
    # Multi-tool plans
    # ---------------------------------------------------------
    if "ranking" in selected_tools and "trend" in selected_tools:
        plan = [
            "Identify the product with the highest revenue",
            "Analyze that product's monthly revenue trend",
            "Summarize the important changes"
        ]

    elif "ranking" in selected_tools and "anomaly" in selected_tools:
        plan = [
            "Identify the top-ranked result",
            "Detect potential anomalies in the dataset",
            "Summarize the important findings"
        ]

    elif "ranking" in selected_tools and "comparison" in selected_tools:
        plan = [
            "Identify the relevant ranking",
            "Compare the requested groups",
            "Summarize the key differences"
        ]

    # ---------------------------------------------------------
    # Single-tool plans
    # ---------------------------------------------------------
    elif analysis_type == "trend":
        plan = [
            "Analyze monthly values",
            "Calculate month-over-month changes",
            "Identify notable trends"
        ]

    elif analysis_type == "anomaly":
        plan = [
            "Analyze the requested metric",
            "Detect unusual values",
            "Summarize notable anomalies"
        ]

    elif analysis_type == "ranking":
        plan = [
            "Group the relevant data",
            "Calculate the requested metric",
            "Identify the top or bottom results"
        ]

    elif analysis_type == "comparison":
        plan = [
            "Group the relevant data",
            "Compare the requested groups",
            "Identify the key difference"
        ]
    
    elif analysis_type == "calculation":
        plan = [
            "Identify the requested metric",
            "Calculate the requested value",
            "Summarize the result"
        ]

    elif analysis_type == "summary":
        plan = [
            "Analyze the relevant data",
            "Calculate key metrics",
            "Summarize the main findings"
        ]

    else:
        plan = [
            "Determine that the question is outside the supported dataset analyses.",
            "Explain which types of questions the assistant can currently answer."
        ]

    return {
        "plan": plan
    }


def run_trend_tool(state):
    """
    Run the trend analysis tool.
    """

    result = get_monthly_trend()

    return {
        "tool_results": {
            "trend": result.to_dict(orient="records")
        }
    }
from tools.anomaly_tool import detect_anomalies


def run_anomaly_tool(state):
    """
    Run the anomaly detection tool.
    """

    result = detect_anomalies()

    return {
        "tool_results": {
            "anomaly": result.to_dict(orient="records")
        }
    }
def process_results(state):
    """
    Process results from all selected tools into a combined summary
    while preserving the original tool results.
    """
    selected_tools = state.get("selected_tools", [])
    tool_results = state.get("tool_results", {})
    execution_log = state.get("execution_log", [])

    processed_results = {}
    trend_data = []

    if "trend" in selected_tools:
        trend_data = tool_results.get("trend", [])

        trend_summary = {}

        if trend_data:
            # Remove the first month because its percentage change is NaN.
            valid_changes = [
                row for row in trend_data
                if row.get("Percentage_Change") is not None
                and str(row.get("Percentage_Change")) != "nan"
            ]

            highest_month = max(
                trend_data,
                key=lambda row: row.get("Revenue", float("-inf"))
            )

            lowest_month = min(
                trend_data,
                key=lambda row: row.get("Revenue", float("inf"))
            )

            if valid_changes:
                largest_increase = max(
                    valid_changes,
                    key=lambda row: row["Percentage_Change"]
                )

                largest_decrease = min(
                    valid_changes,
                    key=lambda row: row["Percentage_Change"]
                )
            else:
                largest_increase = None
                largest_decrease = None

            trend_summary = {
                "first_month": trend_data[0],
                "last_month": trend_data[-1],
                "highest_month": highest_month,
                "lowest_month": lowest_month,
                "largest_increase": largest_increase,
                "largest_decrease": largest_decrease
            }

        processed_results["trend"] = {
            "type": "trend",
            "months_analyzed": len(trend_data),
            "summary": trend_summary,
            "data": trend_data
        }

        execution_log.append(
            "Trend analysis results processed."
        )

    if "anomaly" in selected_tools:
        anomaly_data = tool_results.get("anomaly", [])

        processed_results["anomaly"] = {
            "type": "anomaly",
            "anomalies_found": len(anomaly_data),
            "data": anomaly_data
        }

        execution_log.append(
            "Anomaly detection results processed."
        )

    if "ranking" in selected_tools:
        ranking_data = tool_results.get("ranking", [])

        processed_results["ranking"] = {
            "type": "ranking",
            "results_found": len(ranking_data),
            "data": ranking_data
        }

        execution_log.append(
            "Ranking analysis results processed."
        )

    if "comparison" in selected_tools:
        comparison_data = tool_results.get("comparison", [])

        processed_results["comparison"] = {
            "type": "comparison",
            "groups_compared": len(comparison_data),
            "data": comparison_data
        }

        execution_log.append(
            "Comparison analysis results processed."
        )

    if not processed_results:
        processed_results["summary"] = {
            "type": "summary",
            "data": tool_results
        }

        execution_log.append(
            "Analysis results processed."
        )

    return {
        "tool_results": {
            **tool_results,
            "processed": processed_results
        },
        "execution_log": execution_log
    }
def generate_insight(state):
    """
    Generate an analyst-style answer from processed tool results.

    Simple questions are answered directly from tool results to avoid
    unnecessary LLM latency. Complex multi-tool questions use Qwen.
    """
    tool_results = state["tool_results"]
    user_query = state["user_query"]
    selected_tools = state.get("selected_tools", [])
    execution_log = state.get("execution_log", [])

    # ---------------------------------------------------------
    # FAST PATH 1: Ranking questions
    # ---------------------------------------------------------
    if selected_tools == ["ranking"]:
        ranking = tool_results.get("ranking", [])

        if ranking:
            top_result = ranking[0]

            group_column = next(
                (key for key in top_result if key != "Revenue"),
                "Item"
            )

            top_item = top_result[group_column]
            top_value = top_result["Revenue"]

            return {
                "final_answer": (
                    f"The {group_column.lower()} with the highest revenue is "
                    f"{top_item} ({top_value:,.0f})."
                ),
                "execution_log": state.get("execution_log", []) + [
                    "Fast path used: ranking result answered directly."
                ]
            }
        # ---------------------------------------------------------
    # FAST PATH 2: Ranking + Trend questions
    # ---------------------------------------------------------
    if "ranking" in selected_tools and "trend" in selected_tools:
        ranking = tool_results.get("ranking", [])
        trend_data = tool_results.get("trend", [])
        trend_scope = tool_results.get("trend_scope")

        if ranking and trend_data:
            top_result = ranking[0]

            group_column = next(
                (key for key in top_result if key != "Revenue"),
                "Product"
            )

            top_item = top_result[group_column]
            top_value = top_result["Revenue"]

            first_month = trend_data[0]
            last_month = trend_data[-1]

            highest_month = max(
                trend_data,
                key=lambda row: row["Revenue"]
            )

            lowest_month = min(
                trend_data,
                key=lambda row: row["Revenue"]
            )

            valid_changes = [
                row for row in trend_data
                if row.get("Percentage_Change") is not None
                and str(row.get("Percentage_Change")) != "nan"
            ]

            largest_increase = max(
                valid_changes,
                key=lambda row: row["Percentage_Change"]
            )

            largest_decrease = min(
                valid_changes,
                key=lambda row: row["Percentage_Change"]
            )

            increase_index = trend_data.index(largest_increase)

            if increase_index > 0:
                increase_from = trend_data[increase_index - 1]["Month"]
                increase_to = largest_increase["Month"]
            else:
                increase_from = "previous month"
                increase_to = largest_increase["Month"]

            decrease_index = trend_data.index(largest_decrease)

            if decrease_index > 0:
                decrease_from = trend_data[decrease_index - 1]["Month"]
                decrease_to = largest_decrease["Month"]
            else:
                decrease_from = "previous month"
                decrease_to = largest_decrease["Month"]

            return {
                "final_answer": (
                    f"{top_item} generated the highest revenue at "
                    f"{top_value:,.0f}.\n\n"
                    f"Its monthly revenue ranged from "
                    f"{lowest_month['Revenue']:,.0f} to {highest_month['Revenue']:,.0f} "
                    f"during the year, starting at {first_month['Revenue']:,.0f} in "
                    f"{first_month['Month']} and ending at "
                    f"{last_month['Revenue']:,.0f} in {last_month['Month']}.\n\n"
                    f"- Highest month: {highest_month['Month']} "
                    f"({highest_month['Revenue']:,.0f})\n"
                    f"- Lowest month: {lowest_month['Month']} "
                    f"({lowest_month['Revenue']:,.0f})\n"
                    f"- Largest increase: "
                    f"{largest_increase['Percentage_Change']:+.2f}% "
                    f"({increase_from} → {increase_to})\n"
                    f"- Largest decrease: "
                    f"{largest_decrease['Percentage_Change']:+.2f}% "
                    f"({decrease_from} → {decrease_to})"
                ),
                "execution_log": state.get("execution_log", []) + [
                    "Fast path used: ranking and trend results answered directly."
                ]
            }
        # ---------------------------------------------------------
    # FAST PATH 3: Trend questions
    # ---------------------------------------------------------
    if selected_tools == ["trend"]:
        trend_data = tool_results.get("trend", [])
        trend_scope = tool_results.get("trend_scope")

        if trend_data:
            first_month = trend_data[0]
            last_month = trend_data[-1]

            highest_month = max(
                trend_data,
                key=lambda row: row["Revenue"]
            )

            lowest_month = min(
                trend_data,
                key=lambda row: row["Revenue"]
            )

            valid_changes = [
                row for row in trend_data
                if row.get("Percentage_Change") is not None
                and str(row.get("Percentage_Change")) != "nan"
            ]

            largest_increase = max(
                valid_changes,
                key=lambda row: row["Percentage_Change"]
            )

            largest_decrease = min(
                valid_changes,
                key=lambda row: row["Percentage_Change"]
            )

            increase_index = trend_data.index(largest_increase)

            if increase_index > 0:
                increase_from = trend_data[increase_index - 1]["Month"]
                increase_to = largest_increase["Month"]
            else:
                increase_from = "previous month"
                increase_to = largest_increase["Month"]

            decrease_index = trend_data.index(largest_decrease)

            if decrease_index > 0:
                decrease_from = trend_data[decrease_index - 1]["Month"]
                decrease_to = largest_decrease["Month"]
            else:
                decrease_from = "previous month"
                decrease_to = largest_decrease["Month"]

            scope_text = (
                f"{trend_scope} had "
                if trend_scope
                else ""
            )

            return {
                "final_answer": (
                    f"{scope_text}monthly revenue ranged from "
                    f"{lowest_month['Revenue']:,.0f} to "
                    f"{highest_month['Revenue']:,.0f} during the year.\n\n"
                    f"- Starting month: {first_month['Month']} "
                    f"({first_month['Revenue']:,.0f})\n"
                    f"- Ending month: {last_month['Month']} "
                    f"({last_month['Revenue']:,.0f})\n"
                    f"- Highest month: {highest_month['Month']} "
                    f"({highest_month['Revenue']:,.0f})\n"
                    f"- Lowest month: {lowest_month['Month']} "
                    f"({lowest_month['Revenue']:,.0f})\n"
                    f"- Largest increase: "
                    f"{largest_increase['Percentage_Change']:+.2f}% "
                    f"({increase_from} → {increase_to})\n"
                    f"- Largest decrease: "
                    f"{largest_decrease['Percentage_Change']:+.2f}% "
                    f"({decrease_from} → {decrease_to})"
                ),
                "execution_log": state.get("execution_log", []) + [
                    "Fast path used: trend result answered directly."
                ]
            }

    # ---------------------------------------------------------
    # FAST PATH 4:Comparison questions
    # ---------------------------------------------------------
    if selected_tools == ["comparison"]:
        comparison = tool_results.get("comparison", [])

        if comparison:
            top_result = comparison[0]

            metric_columns = [
                key for key in top_result
                if key not in ["Region", "Product", "Category", "Salesperson"]
            ]

            if metric_columns:
                metric = metric_columns[0]

                group_columns = [
                    key for key in top_result
                    if key != metric
                ]

                group_column = group_columns[0]
                top_item = top_result[group_column]
                top_value = top_result[metric]

                return {
                    "final_answer": (
                        f"{top_item} has the highest {metric.lower()} "
                        f"at {top_value:,.0f}."
                    ),
                    "execution_log": state.get("execution_log", []) + [
                        "Fast path used: comparison result answered directly."
                    ]
                }

    # ---------------------------------------------------------
    # FAST PATH 5:Anomaly questions
    # ---------------------------------------------------------
    if selected_tools == ["anomaly"]:
        anomalies = tool_results.get("anomaly", [])

        return {
            "final_answer": (
                f"I found {len(anomalies)} potential anomalies "
                f"using the IQR-based detection method."
            ),
            "execution_log": state.get("execution_log", []) + [
                "Fast path used: anomaly result summarized directly."
            ]
        }
        # ---------------------------------------------------------
    # FAST PATH 6: Calculation questions
    # ---------------------------------------------------------
    if "calculation" in selected_tools:
        calculation = tool_results.get("calculation", {})

        operation = calculation.get("operation")
        metric = calculation.get("metric")
        result = calculation.get("result")

        # Total / sum calculation
        if operation == "sum" and metric and result is not None:
            formatted_result = f"{result:,.2f}"

            final_answer = (
                f"The total {metric.lower().replace('_', ' ')} "
                f"is {formatted_result}."
            )

            return {
                "final_answer": final_answer,
                "execution_log": execution_log + [
                    "Fast path used: calculation result answered directly."
                ]
            }

        # Percentage change calculation
        if (
            operation == "percentage_change"
            and metric
            and result is not None
        ):
            from_period = calculation.get("from_period")
            to_period = calculation.get("to_period")
            old_value = calculation.get("old_value")
            new_value = calculation.get("new_value")

            final_answer = (
                f"The {metric.lower().replace('_', ' ')} changed by "
                f"{result:.2f}% from {from_period} to {to_period}. "
                f"It changed from {old_value:,.2f} to {new_value:,.2f}."
            )

            return {
                "final_answer": final_answer,
                "execution_log": execution_log + [
                    "Fast path used: percentage change calculation answered directly."
                ]
            }

    # ---------------------------------------------------------
    # LLM PATH
    # Used for trends and multi-tool questions
    # ---------------------------------------------------------
    analysis_context = {
        "ranking": tool_results.get("ranking", []),
        "trend_scope": tool_results.get("trend_scope"),
        "trend": tool_results.get("trend", []),
        "anomaly": tool_results.get("anomaly", []),
        "comparison": tool_results.get("comparison", [])
    }
        # ---------------------------------------------------------
       
    llm = ChatOllama(
        model="qwen3:4b",
        temperature=0,
        think=False
    )

    prompt = f"""
You are a careful data analyst assistant.

User question:
{user_query}

The tools have already performed the analysis.

Tool results:
{analysis_context}

Answer the user's question using ONLY these tool results.

Important rules:

1. Treat every number in the tool results as exact.
2. NEVER divide, multiply, convert, or otherwise modify a number unless
   an explicit calculation result is provided.
3. Do not add a currency symbol unless the data explicitly contains one.
4. Use exact product, region, category, or salesperson names from the results.
5. Do not invent causes or explanations for observed patterns.
6. Do not confuse a product-specific trend with an overall trend.
7. Mention important increases or decreases when directly supported.
8. If a monthly trend is requested, use the structured trend summary.
9. Include the first month, last month, highest month, lowest month,
   largest increase, and largest decrease when available.
10. Do not list all 12 monthly records unless specifically requested.
11. Keep the answer concise and useful.
12. Answer only what the user asked.

Return only the final analyst answer.
"""

    response = llm.invoke(prompt)

    return {
        "final_answer": response.content,
        "execution_log": state.get("execution_log", []) + [
            "Insight generated using Qwen because the question required reasoning."
        ]
    }
def run_ranking_tool(state):
    """
    Run ranking analysis based on the user's query.
    """
    query = state["user_query"].lower()

    # Decide what to rank
    if "product" in query:
        group_by = "Product"
    elif "region" in query:
        group_by = "Region"
    elif "salesperson" in query:
        group_by = "Salesperson"
    elif "category" in query:
        group_by = "Category"
    else:
        group_by = "Product"

    # Decide what metric to use
    if "profit" in query:
        metric = "Profit"
    elif "units" in query or "sold" in query:
        metric = "Units_Sold"
    else:
        metric = "Revenue"

    # Decide how many results to return
    n = 5

    result = get_top_n(
        group_by=group_by,
        metric=metric,
        n=n
    )

    return {
        "tool_results": {
            "ranking": result.to_dict(orient="records")
        },
        "execution_log": state.get("execution_log", []) + [
            f"Ranking analysis completed using {group_by} by {metric}."
        ]
    }
def run_comparison_tool(state):
    """
    Run comparison analysis based on the user's query.
    """
    query = state["user_query"].lower()

    # Decide what groups to compare
    if "region" in query:
        group_by = "Region"
    elif "product" in query:
        group_by = "Product"
    elif "category" in query:
        group_by = "Category"
    elif "salesperson" in query:
        group_by = "Salesperson"
    else:
        group_by = "Region"

    # Decide what metric to compare
    if "profit" in query:
        metric = "Profit"
    elif "units" in query or "sold" in query:
        metric = "Units_Sold"
    else:
        metric = "Revenue"

    result = get_grouped_summary(
        group_by=group_by,
        metric=metric,
        aggregation="sum"
    )

    return {
        "tool_results": {
            "comparison": result.to_dict(orient="records")
        },
        "execution_log": state.get("execution_log", []) + [
            f"Comparison analysis completed using {group_by} by {metric}."
        ]
    }
def run_selected_tools(state):
    """
    Run all analysis tools selected by the query analyzer.
    """
    selected_tools = state.get("selected_tools", [])
    tool_results = {}
    execution_log = state.get("execution_log", [])
    try:
        
        # 1. Ranking analysis
        # --------------------------------------------------
        if "ranking" in selected_tools:
            query = state["user_query"].lower()

            if "product" in query:
                group_by = "Product"
            elif "region" in query:
                group_by = "Region"
            elif "salesperson" in query:
                group_by = "Salesperson"
            elif "category" in query:
                group_by = "Category"
            else:
                group_by = "Product"

            if "profit" in query:
                metric = "Profit"
            elif "units" in query or "sold" in query:
                metric = "Units_Sold"
            else:
                metric = "Revenue"

            result = get_top_n(
                group_by=group_by,
                metric=metric,
                n=5
            )

            tool_results["ranking"] = result.to_dict(
                orient="records"
            )

            execution_log.append(
                f"Ranking analysis completed using {group_by} by {metric}."
            )

            # --------------------------------------------------
        # 2. Trend analysis
        # --------------------------------------------------
        if "trend" in selected_tools:
            from tools.trend_tool import get_monthly_trend

            context_entity = state.get("context_entity", "")

            # --------------------------------------------------
            # Follow-up question using previous context
            # Example: "What was its monthly trend?"
            # --------------------------------------------------
            if context_entity:

                result = get_monthly_trend(
                    filter_column="Product",
                    filter_value=context_entity
                )

                tool_results["trend"] = result.to_dict(
                    orient="records"
                )

                tool_results["trend_chart"] = create_monthly_chart(
                    result,
                    metric="Revenue"
                )

                tool_results["trend_scope"] = (
                    f"Product: {context_entity}"
                )

                execution_log.append(
                    f"Trend analysis completed for product: "
                    f"{context_entity}."
                )

            # --------------------------------------------------
            # Ranking + trend in the same question
            # --------------------------------------------------
            elif (
                "ranking" in selected_tools
                and "ranking" in tool_results
            ):

                ranking_results = tool_results["ranking"]

                if ranking_results:
                    top_product = ranking_results[0]["Product"]

                    result = get_monthly_trend(
                        filter_column="Product",
                        filter_value=top_product
                    )

                    tool_results["trend"] = result.to_dict(
                        orient="records"
                    )

                    tool_results["trend_chart"] = create_monthly_chart(
                        result,
                        metric="Revenue"
                    )

                    tool_results["trend_scope"] = (
                        f"Product: {top_product}"
                    )

                    execution_log.append(
                        f"Trend analysis completed for top product: "
                        f"{top_product}."
                    )

                else:
                    result = get_monthly_trend()

                    tool_results["trend"] = result.to_dict(
                        orient="records"
                    )

                    tool_results["trend_chart"] = create_monthly_chart(
                        result,
                        metric="Revenue"
                    )

                    execution_log.append(
                        "Trend analysis completed."
                    )

            # --------------------------------------------------
            # Overall trend
            # --------------------------------------------------
            else:

                result = get_monthly_trend()

                tool_results["trend"] = result.to_dict(
                    orient="records"
                )

                tool_results["trend_chart"] = create_monthly_chart(
                    result,
                    metric="Revenue"
                )

                execution_log.append(
                    "Trend analysis completed."
                )
        # --------------------------------------------------
        # 3. Anomaly analysis
        # --------------------------------------------------
        if "anomaly" in selected_tools:
            from tools.anomaly_tool import detect_anomalies

            result = detect_anomalies()

            tool_results["anomaly"] = result.to_dict(
                orient="records"
            )

            execution_log.append(
                "Anomaly detection completed."
            )

        # --------------------------------------------------
        # 4. Comparison analysis
        # --------------------------------------------------
        if "comparison" in selected_tools:
            query = state["user_query"].lower()

            if "region" in query:
                group_by = "Region"
            elif "product" in query:
                group_by = "Product"
            elif "category" in query:
                group_by = "Category"
            elif "salesperson" in query:
                group_by = "Salesperson"
            else:
                group_by = "Region"

            if "profit" in query:
                metric = "Profit"
            elif "units" in query or "sold" in query:
                metric = "Units_Sold"
            else:
                metric = "Revenue"

            result = get_grouped_summary(
                group_by=group_by,
                metric=metric,
                aggregation="sum"
            )

            tool_results["comparison"] = result.to_dict(
                orient="records"
            )

            execution_log.append(
                f"Comparison analysis completed using {group_by} by {metric}."
            )
           # 5. Calculation analysis
        if "calculation" in selected_tools:
            from tools.calculation_tool import (
                calculate_sum,
                calculate_percentage_change
            )

            query = state["user_query"].lower()
            df = load_data()

            # Determine which metric the user wants
            if "profit" in query:
                metric = "Profit"
            elif "units" in query or "sold" in query:
                metric = "Units_Sold"
            else:
                metric = "Revenue"

            # ---------------------------------------------------------
            # Percentage change calculation
            # ---------------------------------------------------------
            if "percentage change" in query:
                df["Month"] = df["Date"].dt.to_period("M").astype(str)

                monthly_values = (
                    df.groupby("Month")[metric]
                    .sum()
                    .sort_index()
                )

                if "january" in query and "december" in query:
                    old_value = monthly_values.loc["2024-01"]
                    new_value = monthly_values.loc["2024-12"]

                    percentage_change = calculate_percentage_change(
                        old_value,
                        new_value
                    )

                    tool_results["calculation"] = {
                        "operation": "percentage_change",
                        "metric": metric,
                        "from_period": "January 2024",
                        "to_period": "December 2024",
                        "old_value": old_value,
                        "new_value": new_value,
                        "result": percentage_change
                    }

                    execution_log.append(
                        f"Percentage change calculated for {metric} "
                        f"from January to December 2024."
                    )

            # ---------------------------------------------------------
            # Total calculation
            # ---------------------------------------------------------
            else:
                values = df[metric].dropna().tolist()

                total = calculate_sum(values)

                tool_results["calculation"] = {
                    "operation": "sum",
                    "metric": metric,
                    "result": total
                }

                execution_log.append(
                    f"Calculation completed: total {metric}."
                )

        return {
            "tool_results": tool_results,
            "execution_log": execution_log
        }
    except Exception as e:
        return {
            "tool_results": {
                "error": str(e)
            },
            "execution_log": execution_log + [
                f"Tool execution failed: {str(e)}"
            ]
        }
def handle_unsupported(state):
    """
    Handle questions that cannot be answered by the available tools.
    """
    return {
        "final_answer": (
            "I can currently analyze sales rankings, comparisons, "
            "monthly trends, and potential anomalies in the dataset."
        ),
        "execution_log": state.get("execution_log", []) + [
            "Question could not be mapped to a supported analysis."
        ]
    }