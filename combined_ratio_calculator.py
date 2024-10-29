import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Set page configuration
st.set_page_config(
    page_title="P&C Carrier Combined Ratio Calculator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title
st.title("P&C Carrier Combined Ratio Improvement Calculator")

# Sidebar Inputs
st.sidebar.header("User Inputs")

# Current Financial Metrics
st.sidebar.subheader("Current Financial Metrics")
current_gwp = st.sidebar.number_input(
    "Annual Gross Written Premiums (in millions $):", min_value=0.0, value=500.0, step=10.0
)
current_loss_ratio = st.sidebar.slider(
    "Current Loss Ratio (%):", min_value=0.0, max_value=100.0, value=65.0, step=0.5
)
current_expense_ratio = st.sidebar.slider(
    "Current Expense Ratio (%):", min_value=0.0, max_value=100.0, value=30.0, step=0.5
)

# Expected Improvements
st.sidebar.subheader("Expected Improvements After Salesforce FSC Investment")
loss_ratio_reduction = st.sidebar.slider(
    "Expected Reduction in Loss Ratio (%):", min_value=0.0, max_value=10.0, value=2.0, step=0.1
)
expense_ratio_reduction = st.sidebar.slider(
    "Expected Reduction in Expense Ratio (%):", min_value=0.0, max_value=10.0, value=3.0, step=0.1
)
premium_growth_rate = st.sidebar.slider(
    "Annual Premium Growth Rate (%):", min_value=0.0, max_value=20.0, value=5.0, step=0.5
)
investment_initial = st.sidebar.number_input(
    "Initial Investment Cost (in millions $):", min_value=0.0, value=5.0, step=0.5
)
investment_ongoing = st.sidebar.number_input(
    "Annual Ongoing Costs (in millions $):", min_value=0.0, value=1.0, step=0.1
)
analysis_period = st.sidebar.slider(
    "Analysis Period (Years):", min_value=1, max_value=10, value=5, step=1
)

# Calculate New Ratios
new_loss_ratio = current_loss_ratio * (1 - loss_ratio_reduction / 100)
new_expense_ratio = current_expense_ratio * (1 - expense_ratio_reduction / 100)
current_combined_ratio = current_loss_ratio + current_expense_ratio
new_combined_ratio = new_loss_ratio + new_expense_ratio

# Display Results
st.header("Results")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Current Ratios")
    st.metric("Current Loss Ratio (%)", f"{current_loss_ratio:.2f}")
    st.metric("Current Expense Ratio (%)", f"{current_expense_ratio:.2f}")
    st.metric("Current Combined Ratio (%)", f"{current_combined_ratio:.2f}")

with col2:
    st.subheader("Projected Ratios After Investment")
    st.metric("New Loss Ratio (%)", f"{new_loss_ratio:.2f}")
    st.metric("New Expense Ratio (%)", f"{new_expense_ratio:.2f}")
    st.metric("New Combined Ratio (%)", f"{new_combined_ratio:.2f}")

# Financial Impact Over Analysis Period
years = list(range(1, analysis_period + 1))
gwp_list = []
losses_current = []
losses_new = []
expenses_current = []
expenses_new = []
underwriting_profit_current = []
underwriting_profit_new = []
savings = []
cumulative_savings = []
total_investment = investment_initial + investment_ongoing * analysis_period
roi = 0
payback_period = 0
cumulative_cash_flow = -investment_initial

for year in years:
    if year == 1:
        gwp = current_gwp * (1 + premium_growth_rate / 100)
    else:
        gwp = gwp_list[-1] * (1 + premium_growth_rate / 100)
    gwp_list.append(gwp)
    
    # Current Scenario
    loss_current = gwp * current_loss_ratio / 100
    expense_current = gwp * current_expense_ratio / 100
    profit_current = gwp - loss_current - expense_current
    losses_current.append(loss_current)
    expenses_current.append(expense_current)
    underwriting_profit_current.append(profit_current)
    
    # New Scenario
    loss_new = gwp * new_loss_ratio / 100
    expense_new = gwp * new_expense_ratio / 100
    profit_new = gwp - loss_new - expense_new
    losses_new.append(loss_new)
    expenses_new.append(expense_new)
    underwriting_profit_new.append(profit_new)
    
    # Savings and ROI
    annual_savings = (profit_new - profit_current) - investment_ongoing
    savings.append(annual_savings)
    
    if year == 1:
        cumulative_savings.append(annual_savings)
    else:
        cumulative_savings.append(cumulative_savings[-1] + annual_savings)
    
    cumulative_cash_flow += annual_savings + investment_ongoing  # Account for ongoing costs
    if cumulative_cash_flow >= 0 and payback_period == 0:
        payback_period = year

# ROI Calculation
total_savings = cumulative_savings[-1]
roi = ((total_savings) / total_investment) * 100

# Display Financial Impact
st.header("Financial Impact Over Analysis Period")

financial_df = pd.DataFrame({
    "Year": years,
    "Gross Written Premium ($M)": gwp_list,
    "Underwriting Profit Current ($M)": underwriting_profit_current,
    "Underwriting Profit New ($M)": underwriting_profit_new,
    "Annual Savings ($M)": savings,
    "Cumulative Savings ($M)": cumulative_savings,
})

st.dataframe(financial_df.style.format({"Gross Written Premium ($M)": "{:,.2f}",
                                        "Underwriting Profit Current ($M)": "{:,.2f}",
                                        "Underwriting Profit New ($M)": "{:,.2f}",
                                        "Annual Savings ($M)": "{:,.2f}",
                                        "Cumulative Savings ($M)": "{:,.2f}"}))

# Display ROI and Payback Period
st.subheader("Investment Analysis")
col3, col4 = st.columns(2)

with col3:
    st.metric("Total Investment Cost ($M)", f"{total_investment:.2f}")
    st.metric("Total Savings Over Period ($M)", f"{total_savings:.2f}")

with col4:
    st.metric("Return on Investment (ROI %) ", f"{roi:.2f}%")
    st.metric("Payback Period (Years)", f"{payback_period}")

# Visualization
st.header("Visualization")

# Combined Ratio Comparison
fig1, ax1 = plt.subplots()
ax1.bar(['Current Combined Ratio', 'New Combined Ratio'], [current_combined_ratio, new_combined_ratio], color=['blue', 'green'])
ax1.set_ylabel('Combined Ratio (%)')
ax1.set_title('Combined Ratio Comparison')
st.pyplot(fig1)

# Underwriting Profit Over Time
fig2, ax2 = plt.subplots()
ax2.plot(years, underwriting_profit_current, label='Current Underwriting Profit', marker='o')
ax2.plot(years, underwriting_profit_new, label='New Underwriting Profit', marker='o')
ax2.set_xlabel('Year')
ax2.set_ylabel('Underwriting Profit ($M)')
ax2.set_title('Underwriting Profit Over Time')
ax2.legend()
st.pyplot(fig2)

# Cumulative Savings Over Time
fig3, ax3 = plt.subplots()
ax3.plot(years, cumulative_savings, label='Cumulative Savings', marker='o', color='green')
ax3.set_xlabel('Year')
ax3.set_ylabel('Cumulative Savings ($M)')
ax3.set_title('Cumulative Savings Over Time')
ax3.legend()
st.pyplot(fig3)

