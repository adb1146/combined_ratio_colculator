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
    gwp_list = []
    underwriting_profit_current = []
    underwriting_profit_new = []
    annual_savings = []
    cumulative_savings = []
    annual_savings_salesforce = []
    cumulative_savings_salesforce = []
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
        savings = profit_new - profit_current
        annual_savings.append(savings)
        cumulative_savings.append(sum(annual_savings))

        # Savings Attributable to Salesforce
        loss_savings_salesforce = gwp * loss_ratio_reduction_salesforce / 100
        expense_savings_salesforce = gwp * expense_ratio_reduction_salesforce / 100
        savings_salesforce = loss_savings_salesforce + expense_savings_salesforce
        savings_salesforce -= ongoing_costs_salesforce  # Subtract ongoing Salesforce costs
        annual_savings_salesforce.append(savings_salesforce)
        cumulative_savings_salesforce.append(sum(annual_savings_salesforce))

        # Cumulative Cash Flow
        cumulative_cash_flow += savings - ongoing_costs  # Subtract total ongoing costs
        cumulative_cash_flow_salesforce += savings_salesforce

        # Payback Periods
        if cumulative_cash_flow >= 0 and payback_period is None:
            payback_period = year
        if cumulative_cash_flow_salesforce >= 0 and payback_period_salesforce is None:
            payback_period_salesforce = year

    # Total Investments
    total_investment = initial_investment + ongoing_costs * analysis_period
    total_investment_salesforce = initial_investment + ongoing_costs_salesforce * analysis_period

    # Total Savings
    total_savings = cumulative_savings[-1] - (ongoing_costs * analysis_period)
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

def project_financials_sensitivity(
    current_gwp, premium_growth_rate, current_loss_ratio, current_expense_ratio,
    new_loss_ratio, new_expense_ratio, analysis_period, ongoing_costs, initial_investment,
    loss_ratio_attrib_range, expense_ratio_attrib_range, ongoing_costs_salesforce
):
    # Create a list to hold results for min and max scenarios
    results = []
    for attrib in ['Min', 'Max']:
        if attrib == 'Min':
            loss_ratio_reduction_salesforce = loss_ratio_attrib_range[0]
            expense_ratio_reduction_salesforce = expense_ratio_attrib_range[0]
        else:
            loss_ratio_reduction_salesforce = loss_ratio_attrib_range[1]
            expense_ratio_reduction_salesforce = expense_ratio_attrib_range[1]
        
        # Perform calculations
        (
            financial_df, roi, payback_period, total_investment, total_savings,
            roi_salesforce, payback_period_salesforce, total_investment_salesforce, total_savings_salesforce
        ) = project_financials(
            current_gwp, premium_growth_rate, current_loss_ratio, current_expense_ratio,
            new_loss_ratio, new_expense_ratio, analysis_period, ongoing_costs, initial_investment,
            loss_ratio_reduction_salesforce, expense_ratio_reduction_salesforce, ongoing_costs_salesforce
        )
        # Append results with a label indicating Min or Max
        results.append({
            'Scenario': attrib,
            'Financial_DF': financial_df,
            'ROI': roi,
            'Payback_Period': payback_period,
            'Total_Investment': total_investment,
            'Total_Savings': total_savings,
            'ROI_Salesforce': roi_salesforce,
            'Payback_Period_Salesforce': payback_period_salesforce,
            'Total_Investment_Salesforce': total_investment_salesforce,
            'Total_Savings_Salesforce': total_savings_salesforce
        })
    return results

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

# Other Ongoing Costs (if any)
st.sidebar.subheader("Other Ongoing Costs")
ongoing_costs_other = st.sidebar.number_input(
    "Annual Other Ongoing Costs (in millions $):", min_value=0.0, value=0.0
)

# Total Ongoing Costs
ongoing_costs = ongoing_costs_salesforce + ongoing_costs_other

# Attribution of Improvements to Salesforce
st.sidebar.subheader("Attribution of Improvements to Salesforce")

# Loss Ratio Reduction Attribution Range
loss_ratio_attrib_min = st.sidebar.number_input(
    "Loss Ratio Reduction Attributable to Salesforce (Min %):",
    min_value=0.0,
    max_value=loss_ratio_reduction,
    value=loss_ratio_reduction * 0.5,
    help="Minimum portion of Loss Ratio Reduction due to Salesforce."
)
loss_ratio_attrib_max = st.sidebar.number_input(
    "Loss Ratio Reduction Attributable to Salesforce (Max %):",
    min_value=loss_ratio_attrib_min,
    max_value=loss_ratio_reduction,
    value=loss_ratio_reduction * 1.0,
    help="Maximum portion of Loss Ratio Reduction due to Salesforce."
)

# Expense Ratio Reduction Attribution Range
expense_ratio_attrib_min = st.sidebar.number_input(
    "Expense Ratio Reduction Attributable to Salesforce (Min %):",
    min_value=0.0,
    max_value=expense_ratio_reduction,
    value=expense_ratio_reduction * 0.5,
    help="Minimum portion of Expense Ratio Reduction due to Salesforce."
)
expense_ratio_attrib_max = st.sidebar.number_input(
    "Expense Ratio Reduction Attributable to Salesforce (Max %):",
    min_value=expense_ratio_attrib_min,
    max_value=expense_ratio_reduction,
    value=expense_ratio_reduction * 1.0,
    help="Maximum portion of Expense Ratio Reduction due to Salesforce."
)

# --- Calculations ---
current_combined_ratio = calculate_combined_ratio(current_loss_ratio, current_expense_ratio)
new_loss_ratio, new_expense_ratio = calculate_new_ratios(
    current_loss_ratio, loss_ratio_reduction, current_expense_ratio, expense_ratio_reduction
)
new_combined_ratio = calculate_combined_ratio(new_loss_ratio, new_expense_ratio)

# Perform sensitivity analysis
loss_ratio_attrib_range = [loss_ratio_attrib_min, loss_ratio_attrib_max]
expense_ratio_attrib_range = [expense_ratio_attrib_min, expense_ratio_attrib_max]

sensitivity_results = project_financials_sensitivity(
    current_gwp, premium_growth_rate, current_loss_ratio, current_expense_ratio,
    new_loss_ratio, new_expense_ratio, analysis_period, ongoing_costs, initial_investment,
    loss_ratio_attrib_range, expense_ratio_attrib_range, ongoing_costs_salesforce
)

# --- Display Results ---
st.header("Results")

# Current vs. Projected Ratios
col1, col2 = st.columns(2)
col1.metric("Current Combined Ratio (%)", f"{current_combined_ratio:.2f}")
col2.metric("Projected Combined Ratio (%)", f"{new_combined_ratio:.2f}")

# --- Scenario Comparison ---
st.header("Scenario Comparison")

# Prepare data for comparison
comparison_data = {
    'Scenario': [],
    'Total Investment ($M)': [],
    'Total Savings ($M)': [],
    'ROI (%)': [],
    'Payback Period (Years)': [],
    'Salesforce ROI (%)': [],
    'Salesforce Payback Period (Years)': []
}

for result in sensitivity_results:
    comparison_data['Scenario'].append(result['Scenario'])
    comparison_data['Total Investment ($M)'].append(f"{result['Total_Investment']:.2f}")
    comparison_data['Total Savings ($M)'].append(f"{result['Total_Savings']:.2f}")
    comparison_data['ROI (%)'].append(f"{result['ROI']:.2f}%")
    comparison_data['Payback Period (Years)'].append(result['Payback_Period'] if result['Payback_Period'] else 'N/A')
    comparison_data['Salesforce ROI (%)'].append(f"{result['ROI_Salesforce']:.2f}%")
    comparison_data['Salesforce Payback Period (Years)'].append(result['Payback_Period_Salesforce'] if result['Payback_Period_Salesforce'] else 'N/A')

comparison_df = pd.DataFrame(comparison_data)

st.table(comparison_df)

# --- Sensitivity Analysis Charts ---
st.header("Sensitivity Analysis Charts")

# Prepare data for plotting
attrib_percentages = [loss_ratio_attrib_min, loss_ratio_attrib_max]
roi_values = [result['ROI_Salesforce'] for result in sensitivity_results]
payback_periods = [result['Payback_Period_Salesforce'] if result['Payback_Period_Salesforce'] else analysis_period for result in sensitivity_results]

# Plot ROI vs. Attribution Percentage
fig_roi, ax_roi = plt.subplots()
ax_roi.plot(attrib_percentages, roi_values, marker='o')
ax_roi.set_xlabel('Loss Ratio Reduction Attributable to Salesforce (%)')
ax_roi.set_ylabel('Salesforce ROI (%)')
ax_roi.set_title('ROI Sensitivity to Loss Ratio Attribution')
st.pyplot(fig_roi)

# Plot Payback Period vs. Attribution Percentage
fig_payback, ax_payback = plt.subplots()
ax_payback.plot(attrib_percentages, payback_periods, marker='o', color='orange')
ax_payback.set_xlabel('Loss Ratio Reduction Attributable to Salesforce (%)')
ax_payback.set_ylabel('Salesforce Payback Period (Years)')
ax_payback.set_title('Payback Period Sensitivity to Loss Ratio Attribution')
st.pyplot(fig_payback)

# --- Financial Impact Table for Min Scenario ---
st.header("Financial Impact - Minimum Attribution Scenario")
min_financial_df = sensitivity_results[0]['Financial_DF']

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
    min_financial_df[display_columns].style.format({
        "Gross Written Premium ($M)": "{:,.2f}",
        "Underwriting Profit Current ($M)": "{:,.2f}",
        "Underwriting Profit New ($M)": "{:,.2f}",
        "Annual Savings ($M)": "{:,.2f}",
        "Cumulative Savings ($M)": "{:,.2f}",
        "Annual Savings Attributable to Salesforce ($M)": "{:,.2f}",
        "Cumulative Savings Attributable to Salesforce ($M)": "{:,.2f}",
    })
)

# --- Visualization for Min Scenario ---
st.header("Visualization - Minimum Attribution Scenario")

# Use the financial_df from the Min scenario
financial_df = min_financial_df

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

# Savings Attributable to Salesforce Over Time
fig4, ax4 = plt.subplots()
ax4.plot(
    financial_df["Year"],
    financial_df["Cumulative Savings Attributable to Salesforce ($M)"],
    label='Cumulative Savings Attributable to Salesforce',
    marker='o',
    color='orange'
)
ax4.set_xlabel('Year')
ax4.set_ylabel('Savings ($M)')
ax4.set_title('Cumulative Savings Attributable to Salesforce Over Time')
ax4.legend()
st.pyplot(fig4)

# --- Narrative Explanation ---
st.header("How Salesforce FSC Impacts Your Metrics")

st.markdown("""
Investing in **Salesforce Financial Services Cloud (FSC)** directly contributes to improvements in your key metrics:

- **Loss Ratio Reduction:** Enhanced underwriting accuracy through better data analytics and customer insights.

- **Expense Ratio Reduction:** Automation of manual processes and streamlined operations reduce administrative and acquisition costs.

- **Premium Growth:** Improved customer engagement and cross-selling opportunities lead to increased premiums over time.

The calculations above isolate the savings and ROI attributable directly to your Salesforce investment, providing a clear picture of its financial impact.

By adjusting the attribution percentages, you can see how sensitive your financial outcomes are to the portion of improvements attributed to Salesforce. This helps you make informed decisions even when exact attribution is uncertain.
""")