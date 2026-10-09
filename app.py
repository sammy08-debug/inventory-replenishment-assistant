
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# -------------------------------
# Page configuration
# -------------------------------
st.set_page_config(
    page_title="Inventory Replenishment Assistant",
    page_icon="📦",
    layout="wide"
)

st.title("📦 AI/ML Inventory Replenishment Assistant")
st.caption(
    "A demonstration dashboard for demand analysis, "
    "inventory monitoring and replenishment planning."
)

# -------------------------------
# Load project data
# -------------------------------
BASE_DIR = Path(__file__).parent

inventory_file = BASE_DIR / "inventory_recommendations.csv"
sales_file = BASE_DIR / "sales_history.csv"

if not inventory_file.exists() or not sales_file.exists():
    st.error(
        "The required CSV files are missing. Please ensure "
        "both CSV files are uploaded to the GitHub repository."
    )
    st.stop()

inventory = pd.read_csv(inventory_file)
sales = pd.read_csv(sales_file)

# -------------------------------
# Validate required columns
# -------------------------------
required_inventory = [
    "sku",
    "average_daily_demand",
    "current_stock",
    "lead_time_days",
    "safety_stock",
    "reorder_point",
    "suggested_order_qty",
    "status"
]

missing_inventory = [
    col for col in required_inventory if col not in inventory.columns
]

if missing_inventory:
    st.error(
        "Missing columns in inventory_recommendations.csv: "
        + ", ".join(missing_inventory)
    )
    st.stop()

if "date" not in sales.columns or "sku" not in sales.columns:
    st.error(
        "sales_history.csv must contain 'date' and 'sku' columns."
    )
    st.stop()

# -------------------------------
# Sidebar filters
# -------------------------------
st.sidebar.header("Dashboard Filters")

sku_options = sorted(inventory["sku"].dropna().unique().tolist())

selected_skus = st.sidebar.multiselect(
    "Select products",
    options=sku_options,
    default=sku_options
)

filtered_inventory = inventory[
    inventory["sku"].isin(selected_skus)
].copy()
filtered_inventory["estimated_order_cost"] = (
    filtered_inventory["suggested_order_qty"]
    * filtered_inventory["unit_cost"]
)

filtered_sales = sales[
    sales["sku"].isin(selected_skus)
].copy()

# -------------------------------
# KPI metrics
# -------------------------------



# Inventory Overview
st.header("Inventory Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Products Selected",
    len(filtered_inventory)
)

col2.metric(
    "Products to Reorder",
    int((filtered_inventory["status"] == "REORDER").sum())
)

col3.metric(
    "Total Units in Stock",
    int(filtered_inventory["current_stock"].sum())
)

col4.metric(
    "Suggested Units to Order",
    int(filtered_inventory["suggested_order_qty"].sum())
)

total_order_cost = (
    filtered_inventory["suggested_order_qty"]
    * filtered_inventory["unit_cost"]
).sum()

col5.metric(
    "Estimated Purchasing Cost",
    f"{total_order_cost:,.0f}"
)

# -------------------------------
# Inventory recommendations
# -------------------------------
st.subheader("Replenishment Recommendations")

# Calculate estimated replenishment cost
filtered_inventory["estimated_order_cost"] = (
    filtered_inventory["suggested_order_qty"]
    * filtered_inventory["unit_cost"]
)


display_columns = [
    "sku",
    "average_daily_demand",
    "current_stock",
    "lead_time_days",
    "safety_stock",
    "reorder_point",
    "suggested_order_qty",
    "unit_cost",
    "estimated_order_cost",
    "status"
]

display_inventory = filtered_inventory[display_columns].copy()

display_inventory = display_inventory.rename(columns={
    "sku": "Product",
    "average_daily_demand": "Avg. Daily Demand",
    "current_stock": "Current Stock",
    "lead_time_days": "Lead Time (Days)",
    "safety_stock": "Safety Stock",
    "reorder_point": "Reorder Point",
    "suggested_order_qty": "Suggested Order Qty",
    "unit_cost": "Unit Cost",
    "estimated_order_cost": "Estimated Order Cost",
    "status": "Recommendation"
})
display_inventory["Unit Cost"] = display_inventory["Unit Cost"].map(
    lambda x: f"{x:,.0f}"
)

display_inventory["Estimated Order Cost"] = display_inventory[
    "Estimated Order Cost"
].map(lambda x: f"{x:,.0f}")

st.dataframe(
    display_inventory,
    use_container_width=True,
    hide_index=True
)


# -------------------------------
# Inventory chart
# -------------------------------
st.subheader("Current Stock vs. Reorder Point")

if not filtered_inventory.empty:
    chart_data = filtered_inventory.set_index("sku")[
        ["current_stock", "reorder_point"]
    ]

    fig, ax = plt.subplots(figsize=(9, 4))

    x = list(range(len(chart_data)))
    bar_width = 0.35

    ax.bar(
        [i - bar_width / 2 for i in x],
        chart_data["current_stock"],
        width=bar_width,
        label="Current Stock"
    )

    ax.bar(
        [i + bar_width / 2 for i in x],
        chart_data["reorder_point"],
        width=bar_width,
        label="Reorder Point"
    )

    ax.set_xticks(x)
    ax.set_xticklabels(chart_data.index)
    ax.set_ylabel("Units")
    ax.set_title("Current Stock vs. Reorder Point by Product")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# -------------------------------
# Sales trend chart
# -------------------------------
st.subheader("Historical Sales Trends")

if not filtered_sales.empty:
    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    filtered_sales["date"] = pd.to_datetime(
        filtered_sales["date"], errors="coerce"
    )

    possible_sales_columns = [
    "sales_units",
    "sales",
    "daily_sales",
    "units_sold"
]
    sales_column = next(
        (col for col in possible_sales_columns if col in filtered_sales.columns),
        None
    )

    if sales_column:
        filtered_sales = filtered_sales.dropna(subset=["date"])

        sales_trend = (
            filtered_sales.groupby(["date", "sku"])[sales_column]
            .sum()
            .unstack(fill_value=0)
            .sort_index()
        )

        st.line_chart(sales_trend)
    else:
        st.info(
            "Couldn't identify the sales quantity column. "
            "Expected one of: sales, daily_sales, units_sold. "
            "Please check the column names in sales_history.csv."
        )
else:
    st.info("No sales records are available for the selected products.")

# -------------------------------
# Download recommendations
# -------------------------------
st.subheader("Export Recommendations")

csv_data = filtered_inventory.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered recommendations (CSV)",
    data=csv_data,
    file_name="inventory_recommendations_filtered.csv",
    mime="text/csv"
)

# -------------------------------
# Methodology and limitations
# -------------------------------
with st.expander("How the recommendations work"):
    st.write(
        "The uploaded inventory recommendations use average demand, "
        "supplier lead time, safety stock, reorder points and a target "
        "stock policy to suggest replenishment quantities."
    )
    st.write(
        "The original demonstration uses synthetic data. The recommendations "
        "are illustrative and should not be used for actual purchasing "
        "without validating demand, available stock, incoming orders, "
        "supplier constraints and business requirements."
    )

st.caption(
    "Portfolio demonstration • Synthetic data • "
    "Forecasting accuracy and replenishment rules should be validated "
    "before operational use."
)
