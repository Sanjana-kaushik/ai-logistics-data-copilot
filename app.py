from pathlib import Path
import streamlit as st
import plotly.express as px
import pandas as pd


from ai_service import (
    generate_business_summary,
    generate_sql,
)


from database import (
    create_database,
    run_query,
)
from data_quality import get_data_quality_results

if not Path("logistics_backup.db").exists():
    create_database()

st.set_page_config(
    page_title="AI Logistics Data Copilot",
    page_icon="🚚",
    layout="wide",
)

st.title("AI Logistics Data Copilot")

st.caption(
    "An enterprise analytics and data-governance portfolio project."
)
with st.expander("About this project"):
    st.write(
        """
        The AI Logistics Data Copilot demonstrates how
        generative AI can support enterprise analytics,
        metadata discovery, data-quality monitoring,
        SQL generation, and business reporting.

        The application combines Python, SQLite, Pandas,
        Streamlit, Plotly, and an LLM API.

        AI-generated SQL is restricted to read-only queries
        and requires human review before execution.
        """
    )

page = st.sidebar.radio(
    "Navigation",
    [
        "Executive Dashboard",
        "Data Quality Monitor",
        "Metadata Catalog",
        "Ask Your Data",
    ],
)
if page == "Executive Dashboard":
    dashboard_data = run_query(
    """
    SELECT
        o.order_id,
        o.order_date,
        o.order_value,
        o.order_status,
        c.customer_name,
        c.country,
        c.customer_segment,
        p.product_name,
        p.category,
        s.carrier,
        s.delay_days,
        s.shipment_status
    FROM orders o
    LEFT JOIN customers c
        ON o.customer_id = c.customer_id
    LEFT JOIN products p
        ON o.product_id = p.product_id
    LEFT JOIN shipments s
        ON o.order_id = s.order_id
    """
)

    st.sidebar.header("Dashboard Filters")

    countries = sorted(
                    dashboard_data["country"]
                    .dropna()
                    .unique()
                    .tolist()
                )

    carriers = sorted(
                    dashboard_data["carrier"]
                    .dropna()
                    .unique()
                    .tolist()
                )

    segments = sorted(
                    dashboard_data["customer_segment"]
                    .dropna()
                    .unique()
                    .tolist()
                )

    selected_countries = st.sidebar.multiselect(
                    "Select Country",
                    countries,
                    default=countries,
                )

    selected_carriers = st.sidebar.multiselect(
                    "Select Carrier",
                    carriers,
                    default=carriers,
                )

    selected_segments = st.sidebar.multiselect(
                    "Select Customer Segment",
                    segments,
                    default=segments,
                )

    dashboard_data = dashboard_data[
                    dashboard_data["country"].isin(selected_countries)
                    & dashboard_data["carrier"].isin(selected_carriers)
                    & dashboard_data["customer_segment"].isin(selected_segments)
                ]

    st.subheader("Project Data Preview")

    total_orders = dashboard_data["order_id"].nunique()

    total_revenue = dashboard_data["order_value"].sum()

    delayed_shipments = (
                    dashboard_data["shipment_status"] == "Delayed"
                ).sum()

    shipment_count = dashboard_data[
                    "shipment_status"
                ].notna().sum()

    on_time_shipments = (
                    dashboard_data["shipment_status"] == "Delivered"
                ).sum()

    if shipment_count > 0:
                    on_time_rate = (
                        on_time_shipments / shipment_count
                    ) * 100
    else:
                    on_time_rate = 0

    column1, column2, column3, column4 = st.columns(4)

    column1.metric(
                    "Total Orders",
                    f"{total_orders:,}",
                )

    column2.metric(
                    "Total Revenue",
                    f"${total_revenue:,.0f}",
                )

    column3.metric(
                    "Delayed Shipments",
                    f"{delayed_shipments:,}",
                )

    column4.metric(
                    "On-Time Delivery Rate",
                    f"{on_time_rate:.1f}%",
                )

    st.subheader("Average Delay by Carrier")

    carrier_summary = (
                    dashboard_data.groupby(
                        "carrier",
                        dropna=False,
                    )
                    .agg(
                        total_shipments=("order_id", "count"),
                        average_delay_days=("delay_days", "mean"),
                    )
                    .reset_index()
                )

    carrier_chart = px.bar(
                    carrier_summary,
                    x="carrier",
                    y="average_delay_days",
                    title="Average Delay Days by Carrier",
                )

    st.plotly_chart(
                    carrier_chart,
                    use_container_width=True,
                )
    st.dataframe(
                    dashboard_data,
                    use_container_width=True,
                )

    st.subheader("Monthly Revenue Trend")

    dashboard_data["order_date"] = pd.to_datetime(
                    dashboard_data["order_date"],
                    errors="coerce",
                )

    dashboard_data["order_month"] = (
                    dashboard_data["order_date"]
                    .dt.to_period("M")
                    .astype(str)
                )

    monthly_revenue = (
                    dashboard_data.groupby("order_month")["order_value"]
                    .sum()
                    .reset_index()
                    .sort_values("order_month")
                )

    monthly_revenue_chart = px.line(
                    monthly_revenue,
                    x="order_month",
                    y="order_value",
                    markers=True,
                    title="Revenue by Month",
                    labels={
                        "order_month": "Month",
                        "order_value": "Revenue",
                    },
                )

    st.plotly_chart(
                    monthly_revenue_chart,
                    use_container_width=True,
                )

    st.subheader("Delayed Shipments by Country")

    delayed_data = dashboard_data[
                    dashboard_data["shipment_status"] == "Delayed"
                ]

    delays_by_country = (
                    delayed_data.groupby("country")
                    .size()
                    .reset_index(name="delayed_shipments")
                    .sort_values(
                        "delayed_shipments",
                        ascending=False,
                    )
                )

    delay_country_chart = px.bar(
                    delays_by_country,
                    x="country",
                    y="delayed_shipments",
                    title="Number of Delayed Shipments by Country",
                    labels={
                        "country": "Country",
                        "delayed_shipments": "Delayed Shipments",
                    },
                )

    st.plotly_chart(
                    delay_country_chart,
                    use_container_width=True,
                )

    st.subheader("Revenue by Product Category")

    category_revenue = (
                    dashboard_data.groupby("category")["order_value"]
                    .sum()
                    .reset_index()
                    .sort_values(
                        "order_value",
                        ascending=False,
                    )
                )

    category_chart = px.bar(
                    category_revenue,
                    x="category",
                    y="order_value",
                    title="Revenue by Product Category",
                    labels={
                        "category": "Product Category",
                        "order_value": "Revenue",
                    },
                )

    st.plotly_chart(
                    category_chart,
                    use_container_width=True,
                )


elif page == "Data Quality Monitor":
    st.header("Data Quality Monitor")

    st.write(
        "This page evaluates key data-quality rules "
        "for the shipment dataset."
    )

    quality_results = get_data_quality_results()

    total_rules = len(quality_results)

    passed_rules = (
        quality_results["status"] == "Passed"
    ).sum()

    failed_rules = (
        quality_results["status"] == "Failed"
    ).sum()

    column1, column2, column3 = st.columns(3)

    column1.metric(
        "Rules Evaluated",
        int(total_rules),
    )

    column2.metric(
        "Rules Passed",
        int(passed_rules),
    )

    column3.metric(
        "Rules Failed",
        int(failed_rules),
    )

    st.subheader("Rule Results")

    st.dataframe(
        quality_results,
        use_container_width=True,
    )

    if failed_rules > 0:
        st.warning(
            "Data-quality issues were detected."
        )
    else:
        st.success(
            "All data-quality rules passed."
)
        
elif page == "Metadata Catalog":
    st.header("Metadata Catalog")

    st.write(
        "Search business definitions for tables "
        "and columns used in the project."
    )

    metadata = run_query(
        """
        SELECT
            table_name,
            column_name,
            description,
            data_type
        FROM metadata
        ORDER BY
            table_name,
            column_name
        """
    )

    search_term = st.text_input(
        "Search table names, column names, or definitions"
    )

    if search_term:
        search_value = search_term.lower()

        metadata = metadata[
            metadata.astype(str)
            .apply(
                lambda row: (
                    row.str.lower()
                    .str.contains(
                        search_value,
                        na=False,
                    )
                    .any()
                ),
                axis=1,
            )
        ]

    st.dataframe(
        metadata,
        use_container_width=True,
)


elif page == "Ask Your Data":
    st.header("Ask Your Data")

    st.write(
        "Ask a business question in plain English. "
        "The AI assistant will generate a read-only SQL query "
        "for your review."
    )

    st.info(
    "AI-generated SQL may be imperfect. "
    "Review every query before approving execution."
    )

    example_questions = [
        "Which carrier has the highest average delay?",
        "Show delayed shipments by country.",
        "Which product category generated the most revenue?",
        "Show revenue by customer segment.",
        "Which customer segment has the most orders?",
        "Show the top five customers by total order value.",
        "Show monthly revenue.",
    ]

    selected_example = st.selectbox(
        "Example questions",
        ["Select an example"] + example_questions,
    )

    default_question = (
        ""
        if selected_example == "Select an example"
        else selected_example
    )

    question = st.text_input(
        "Enter a business question",
        value=default_question,
    )

    if "generated_sql" not in st.session_state:
        st.session_state.generated_sql = None

    if "current_question" not in st.session_state:
        st.session_state.current_question = None

    if "query_result" not in st.session_state:
        st.session_state.query_result = None

    if "business_summary" not in st.session_state:
        st.session_state.business_summary = None

    generate_button = st.button(
        "Generate SQL",
        type="primary",
    )

    if generate_button:
        if not question.strip():
            st.warning(
                "Please enter a business question."
            )
        else:
            try:
                with st.spinner("Generating SQL..."):
                    st.session_state.generated_sql = (
                        generate_sql(question)
                    )

                    st.session_state.current_question = question
                    st.session_state.query_result = None
                    st.session_state.business_summary = None

            except Exception as error:
                error_message = str(error)

                if "insufficient_quota" in error_message:
                     st.error(
            "The AI service has insufficient API quota. "
            "Check the API billing and usage settings."
        )
                elif "authentication" in error_message.lower():
                      st.error(
            "The API key could not be authenticated."
        )
                else:
                     st.error(
            f"Unable to generate SQL: {error}"
        )

    if st.session_state.generated_sql:
        st.subheader("Generated SQL")

        st.code(
            st.session_state.generated_sql,
            language="sql",
        )

        st.caption(
            "Review the generated query before approving execution."
        )

        run_button = st.button(
            "Run Approved Query"
        )

        if run_button:
            try:
                with st.spinner(
                    "Running the approved query..."
                ):
                    query_result = run_query(
                        st.session_state.generated_sql
                    )

                    st.session_state.query_result = (
                        query_result
                    )

                    if query_result.empty:
                        st.session_state.business_summary = (
                            "The query completed successfully, "
                            "but no records were returned."
                        )
                    else:
                        result_text = (
                            query_result
                            .head(30)
                            .to_csv(index=False)
                        )

                        st.session_state.business_summary = (
                            generate_business_summary(
                                question=(
                                    st.session_state
                                    .current_question
                                ),
                                sql=(
                                    st.session_state
                                    .generated_sql
                                ),
                                result_text=result_text,
                            )
                        )

            except Exception as error:
                st.error(
                    f"Unable to run the query: {error}"
                )

    if st.session_state.query_result is not None:
        st.subheader("Query Result")

        if st.session_state.query_result.empty:
            st.info(
                "The query ran successfully, "
                "but no records were returned."
            )
        else:
            st.dataframe(
                st.session_state.query_result,
                width="stretch",
            )
        result_dataframe = (
            st.session_state.query_result
        )

        numeric_columns = (
            result_dataframe
            .select_dtypes(include="number")
            .columns
            .tolist()
        )

        text_columns = [
            column
            for column in result_dataframe.columns
            if column not in numeric_columns
        ]

        if (
            len(numeric_columns) >= 1
            and len(text_columns) >= 1
            and len(result_dataframe) <= 30
        ):
            chart = px.bar(
                result_dataframe,
                x=text_columns[0],
                y=numeric_columns[0],
                title="AI Query Result Visualization",
            )

            st.plotly_chart(
                chart,
                width="stretch",
            )

    if st.session_state.business_summary:
        st.subheader("AI Business Summary")

        st.write(
            st.session_state.business_summary
        )