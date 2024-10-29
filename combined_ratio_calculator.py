import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Configurations ---
st.set_page_config(
    page_title="P&C Carrier Combined Ratio Improvement Calculator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Helper Functions ---
def calculate_combined_ratio(loss_ratio, expense_ratio):
    return loss_ratio + expense_ratio

def calculate_new_ratios(current_loss_ratio, loss_ratio_reduction, current_expense_ratio, expense_ratio_reduction):
    new_loss_ratio = current_loss_ratio - loss_ratio_reduction
    new_expense_ratio = current_expense_ratio - expense_ratio_reduction
    return new_loss_ratio, new_expense_ratio

def project_financials(
    current_gwp, premium_growth_rate, current_loss_ratio, current_expense_ratio,
    new_loss_ratio, new_expense_ratio, analysis_period, ongoing_costs, initial_investment,
    loss_ratio_reduction_salesforce, expense_ratio_reduction_salesforce, ongoing_costs_salesforce
):
    years = list(range(1, analysis_period + 1))
    gwp_list, underwriting_profit_current, underwriting_profit_new = [], [], []
    annual_savings, cumulative_savings = [], []
    annual_savings_salesforce, cumulative_savings_salesforce = [], []
    cumulative_cash_flow = -initial_investment
    cumulative_cash_flow_salesforce = -initial_investment
    payback_period = None
    payback_period_salesforce = None

    for year in years:
        gwp = current_gwp * (1 + premium_growth_rate / 100) ** year
        gwp_list.append(gwp)

        # Current Scenario
        loss_current = gwp * current_loss_ratio / 100
        expense_current = gwp * current_expense_ratio / 100
        profit_current = gwp - loss_current - expense_current
        underwriting_profit_current.append(profit_current)

        # New Scenario
        loss_new = gwp * new_loss_ratio / 100
        expense_new = gwp * new_expense_ratio / 100
        profit_new = gwp - loss_new - expense_new
        underwriting_profit_new.append(profit_new)

        # Total Savings
        savings = profit_new - profit_current - ongoing_costs
        annual_savings.append(savings)
        cumulative_savings.append(sum(annual_savings))

        # Savings Attributable to Salesforce
        loss_savings_salesforce = gwp * loss_ratio_reduction_salesforce / 100
        expense_savings_salesforce = gwp * expense_ratio_reduction_salesforce / 100
        savings_salesforce = loss_savings_salesforce + expense_savings_salesforce - ongoing_costs_salesforce
        annual_savings_salesforce.append(savings_salesforce)
        cumulative_savings_salesforce.append(sum(annual_savings_salesforce))

        # Cumulative Cash Flow
        cumulative_cash_flow += savings + ongoing_costs
        cumulative_cash_flow_salesforce += savings_salesforce + ongoing_costs_salesforce

        # Payback Periods
        if cumulative_cash_flow >= 0 and payback_period is None:
            payback_period = year
        if cumulative_cash_flow_salesforce >= 0 and payback_period_salesforce is None:
            payback_period_salesforce = year

    # Total Investments
    total_investment = initial_investment + ongoing_costs * analysis_period
    total_investment_salesforce = initial_investment + ongoing_costs_salesforce * analysis_period

    # Total Savings
    total_savings = cumulative_savings[-1]
    total_savings_salesforce = cumulative_savings_salesforce[-1]

    # ROI Calculations
    roi = (total_savings / total_investment) * 100 if total_investment != 0 else 0
    roi_salesforce = (total_savings_salesforce / total_investment_salesforce) * 100 if total_investment_salesforce != 0 else 0

    # Create DataFrame
    financial_df = pd.DataFrame({
        "Year": years,
        "Gross Written Premium ($M)": gwp_list,
        "Underwriting Profit Current ($M)": underwriting_profit_current,
        "Underwriting Profit New ($M)": underwriting_profit_new,
        "Annual Savings ($M)": annual_savings,
        "Cumulative Savings ($M)": cumulative_savings,
        "Annual Savings Attributable to Salesforce ($M)": annual_savings_salesforce,
        "Cumulative Savings Attributable to Salesforce ($M)": cumulative_savings_salesforce,
    })

    return (
        financial_df, roi, payback_period, total_investment, total_savings,
        roi_salesforce, payback_period_salesforce, total_investment_salesforce, total_savings_salesforce
    )

# --- Sidebar for User Inputs ---
st.sidebar.header("User Inputs")

# Current Financial Metrics
st.sidebar.subheader("Current Financial Metrics")
current_gwp = st.sidebar.number_input(
    "Annual Gross Written Premiums (in millions $):", min_value=0.0, value=500.0
)
current_loss_ratio = st.sidebar.slider(
    "Current Loss Ratio (%):", min_value=0.0, max_value=100.0, value=65.0
)
current_expense_ratio = st.sidebar.slider(
    "Current Expense Ratio (%):", min_value=0.0, max_value=100.0, value=30.0
)

# Expected Improvements
st.sidebar.subheader("Expected Improvements After Investment")
loss_ratio_reduction = st.sidebar.slider(
    "Expected Reduction in Loss Ratio (%):", min_value=0.0, max_value=5.0, value=0.5
)
expense_ratio_reduction = st.sidebar.slider(
    "Expected Reduction in Expense Ratio (%):", min_value=0.0, max_value=5.0, value=1.0
)
premium_growth_rate = st.sidebar.slider(
    "Annual Premium Growth Rate (%):", min_value=0.0, max_value=5.0, value=2.0
)
analysis_period = st.sidebar.slider(
    "Analysis Period (Years):", min_value=1, max_value=10, value=5
)

# Salesforce Expense Inputs
st.sidebar.subheader("Salesforce FSC Investment Costs")
initial_investment = st.sidebar.number_input(
    "Initial Investment Cost (in millions $):", min_value=0.0, value=7.0
)
ongoing_costs_salesforce = st.sidebar.number_input(
    "Annual Ongoing Costs (in millions $):", min_value=0.0, value=1.5
)
ongoing_costs = ongoing_costs_salesforce  # Assuming all ongoing costs are Salesforce-related

# Attribution of Improvements to Salesforce
st.sidebar.subheader("Attribution of Improvements to Salesforce")
loss_ratio_reduction_salesforce = st.sidebar.slider(
    "Loss Ratio Reduction Attributable to Salesforce (%):",
    min_value=0.0,
    max_value=loss_ratio_reduction,
    value=loss_ratio_reduction * 0.8,
    help="Portion of Loss Ratio Reduction directly due to Salesforce investment."
)
expense_ratio_reduction_salesforce = st.sidebar.slider(
    "Expense Ratio Reduction Attributable to Salesforce (%):",
    min_value=0.0,
    max_value=expense_ratio_reduction,
    value=expense_ratio_reduction * 0.8,
    help="Portion of Expense Ratio Reduction directly due to Salesforce investment."
)

# --- Calculations ---
current_combined_ratio = calculate_combined_ratio(current_loss_ratio, current_expense_ratio)
new_loss_ratio, new_expense_ratio = calculate_new_ratios(
    current_loss_ratio, loss_ratio_reduction, current_expense_ratio, expense_ratio_reduction
)
new_combined_ratio = calculate_combined_ratio(new_loss_ratio, new_expense_ratio)

# Perform financial projections
(
    financial_df, roi, payback_period, total_investment, total_savings,
    roi_salesforce, payback_period_salesforce, total_investment_salesforce, total_savings_salesforce
) = project_financials(
    current_gwp, premium_growth_rate, current_loss_ratio, current_expense_ratio,
    new_loss_ratio, new_expense_ratio, analysis_period, ongoing_costs, initial_investment,
    loss_ratio_reduction_salesforce, expense_ratio_reduction_salesforce, ongoing_costs_salesforce
)

# --- Display Results ---
st.header("Results")

# Current vs. Projected Ratios
col1, col2 = st.columns(2)
col1.metric("Current Combined Ratio (%)", f"{current_combined_ratio:.2f}")
col2.metric("Projected Combined Ratio (%)", f"{new_combined_ratio:.2f}")

# --- Investment Analysis ---
st.subheader("Investment Analysis")

col3, col4 = st.columns(2)
with col3:
    st.metric("Total Investment Cost ($M)", f"{total_investment:.2f}")
    st.metric("Total Savings Over Period ($M)", f"{total_savings:.2f}")
    st.metric("Return on Investment (ROI %) ", f"{roi:.2f}%")
    st.metric("Payback Period (Years)", f"{payback_period if payback_period else 'Not Achieved'}")

with col4:
    st.metric("Salesforce Investment Cost ($M)", f"{total_investment_salesforce:.2f}")
    st.metric("Savings Attributable to Salesforce ($M)", f"{total_savings_salesforce:.2f}")
    st.metric("Salesforce ROI (%)", f"{roi_salesforce:.2f}%")
    st.metric("Salesforce Payback Period (Years)", f"{payback_period_salesforce if payback_period_salesforce else 'Not Achieved'}")

# --- Financial Impact Table ---
st.subheader("Financial Impact Over Analysis Period")

# Select columns to display
display_columns = [
    "Year",
    "Gross Written Premium ($M)",
    "Underwriting Profit Current ($M)",
    "Underwriting Profit New ($M)",
    "Annual Savings ($M)",
    "Cumulative Savings ($M)",
    "Annual Savings Attributable to Salesforce ($M)",
    "Cumulative Savings Attributable to Salesforce ($M)",
]

st.dataframe(
    financial_df[display_columns].style.format({
        "Gross Written Premium ($M)": "{:,.2f}",
        "Underwriting Profit Current ($M)": "{:,.2f}",
        "Underwriting Profit New ($M)": "{:,.2f}",
        "Annual Savings ($M)": "{:,.2f}",
        "Cumulative Savings ($M)": "{:,.2f}",
        "Annual Savings Attributable to Salesforce ($M)": "{:,.2f}",
        "Cumulative Savings Attributable to Salesforce ($M)": "{:,.2f}",
    })
)

# --- Visualization ---
st.header("Visualization")

# Combined Ratio Comparison
# ... (existing charts)

# Savings Attributable to Salesforce Over Time
# ... (new charts as above)

# --- Narrative Explanation ---
# ... (narrative text as above)