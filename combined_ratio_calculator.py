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
    new_loss_ratio = current_loss_ratio * (1 - loss_ratio_reduction / 100)
    new_expense_ratio = current_expense_ratio * (1 - expense_ratio_reduction / 100)
    return new_loss_ratio, new_expense_ratio

def project_financials(current_gwp, premium_growth_rate, current_loss_ratio, current_expense_ratio,
                       new_loss_ratio, new_expense_ratio, analysis_period, ongoing_costs, initial_investment):
    years = list(range(1, analysis_period + 1))
    gwp_list, underwriting_profit_current, underwriting_profit_new = [], [], []
    annual_savings, cumulative_savings = [], []
    cumulative_cash_flow = -initial_investment
    payback_period = None

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

        # Savings and ROI
        savings = (profit_new - profit_current) - ongoing_costs
        annual_savings.append(savings)

        cumulative_cash_flow += savings + ongoing_costs
        if cumulative_cash_flow >= 0 and payback_period is None:
            payback_period = year

        if cumulative_savings:
            cumulative_savings.append(cumulative_savings[-1] + savings)
        else:
            cumulative_savings.append(savings)

    financial_df = pd.DataFrame({
        "Year": years,
        "Gross Written Premium ($M)": gwp_list,
        "Underwriting Profit Current ($M)": underwriting_profit_current,
        "Underwriting Profit New ($M)": underwriting_profit_new,
        "Annual Savings ($M)": annual_savings,
        "Cumulative Savings ($M)": cumulative_savings,
    })

    total_investment = initial_investment + ongoing_costs * analysis_period
    total_savings = cumulative_savings[-1]
    roi = (total_savings / total_investment) * 100

    return financial_df, roi, payback_period, total_investment, total_savings

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
    "Expected Reduction in Loss Ratio (%):", min_value=0.0, max_value=10.0, value=0.5
)
expense_ratio_reduction = st.sidebar.slider(
    "Expected Reduction in Expense Ratio (%):", min_value=0.0, max_value=10.0, value=1.0
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
ongoing_costs = st.sidebar.number_input(
    "Annual Ongoing Costs (in millions $):", min_value=0.0, value=1.5
)

# --- Calculations ---
current_combined_ratio = calculate_combined_ratio(current_loss_ratio, current_expense_ratio)
new_loss_ratio, new_expense_ratio = calculate_new_ratios(
    current_loss_ratio, loss_ratio_reduction, current_expense_ratio, expense_ratio_reduction
)
new_combined_ratio = calculate_combined_ratio(new_loss_ratio, new_expense_ratio)

financial_df, roi, payback_period, total_investment, total_savings = project_financials(
    current_gwp, premium_growth_rate, current_loss_ratio, current_expense_ratio,
    new_loss_ratio, new_expense_ratio, analysis_period, ongoing_costs, initial_investment
)

# --- Display Results ---
st.header("Results")

# Current vs. Projected Ratios
col1, col2 = st.columns(2)
col1.metric("Current Combined Ratio (%)", f"{current_combined_ratio:.2f}")
col2.metric("Projected Combined Ratio (%)", f"{new_combined_ratio:.2f}")

# Investment Analysis
st.subheader("Investment Analysis")
col3, col4 = st.columns(2)
col3.metric("Total Investment Cost ($M)", f"{total_investment:.2f}")
col4.metric("Total Savings Over Period ($M)", f"{total_savings:.2f}")
col3.metric("Return on Investment (ROI %) ", f"{roi:.2f}%")
col4.metric("Payback Period (Years)", f"{payback_period if payback_period else 'Not Achieved'}")

# --- Financial Impact Table ---
st.subheader("Financial Impact Over Analysis Period")
st.dataframe(
    financial_df.style.format({
        "Gross Written Premium ($M)": "{:,.2f}",
        "Underwriting Profit Current ($M)": "{:,.2f}",
        "Underwriting Profit New ($M)": "{:,.2f}",
        "Annual Savings ($M)": "{:,.2f}",
        "Cumulative Savings ($M)": "{:,.2f}",
    })
)

# --- Visualization ---
st.header("Visualization")

# Combined Ratio Comparison
fig1, ax1 = plt.subplots()
ax1.bar(
    ['Current Combined Ratio', 'New Combined Ratio'],
    [current_combined_ratio, new_combined_ratio],
    color=['blue', 'green']
)
ax1.set_ylabel('Combined Ratio (%)')
ax1.set_title('Combined Ratio Comparison')
st.pyplot(fig1)

# Underwriting Profit Over Time
fig2, ax2 = plt.subplots()
ax2.plot(
    financial_df["Year"],
    financial_df["Underwriting Profit Current ($M)"],
    label='Current Underwriting Profit',
    marker='o'
)
ax2.plot(
    financial_df["Year"],
    financial_df["Underwriting Profit New ($M)"],
    label='New Underwriting Profit',
    marker='o'
)
ax2.set_xlabel('Year')
ax2.set_ylabel('Underwriting Profit ($M)')
ax2.set_title('Underwriting Profit Over Time')
ax2.legend()
st.pyplot(fig2)

# Cumulative Savings Over Time
fig3, ax3 = plt.subplots()
ax3.plot(
    financial_df["Year"],
    financial_df["Cumulative Savings ($M)"],
    label='Cumulative Savings',
    marker='o',
    color='green'
)
ax3.set_xlabel('Year')
ax3.set_ylabel('Cumulative Savings ($M)')
ax3.set_title('Cumulative Savings Over Time')
ax3.legend()
st.pyplot(fig3)