import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_chat import message
import openai
import os  # Import the os module

# --- Configurations ---
st.set_page_config(
    page_title="P&C Carrier Combined Ratio Improvement Calculator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Set up OpenAI API Key ---
# Load the API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Check if the API key was successfully loaded
if openai.api_key is None:
    st.error("OpenAI API key is missing. Please set the OPENAI_API_KEY environment variable.")
    st.stop()

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
    profit_current_list = []
    profit_new_list = []
    annual_savings = []
    cumulative_savings = []
    annual_savings_salesforce = []
    cumulative_savings_salesforce = []
    cumulative_cash_flow = -initial_investment
    cumulative_cash_flow_salesforce = -initial_investment
    payback_period = None
    payback_period_salesforce = None

    for year in years:
        gwp = current_gwp * (1 + premium_growth_rate / 100) ** (year - 1)
        gwp_list.append(gwp)

        # Current Scenario
        loss_current = gwp * current_loss_ratio / 100
        expense_current = gwp * current_expense_ratio / 100
        profit_current = gwp - loss_current - expense_current
        profit_current_list.append(profit_current)

        # New Scenario
        loss_new = gwp * new_loss_ratio / 100
        expense_new = gwp * new_expense_ratio / 100
        profit_new = gwp - loss_new - expense_new
        profit_new_list.append(profit_new)

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
        "Projected Premiums ($M)": gwp_list,
        "Current Operating Profit ($M)": profit_current_list,
        "Projected Operating Profit ($M)": profit_new_list,
        "Annual Savings ($M)": annual_savings,
        "Cumulative Savings ($M)": cumulative_savings,
        "Annual Savings from Salesforce ($M)": annual_savings_salesforce,
        "Cumulative Salesforce Savings ($M)": cumulative_savings_salesforce,
    })

    return (
        financial_df, roi, payback_period, total_investment, total_savings,
        roi_salesforce, payback_period_salesforce, total_investment_salesforce, total_savings_salesforce
    )

# --- Create Tabs ---
tab1, tab2 = st.tabs(["Calculator", "User Guide & AI Assistant"])

with tab1:
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
        "Annual Premium Growth Rate (%):", min_value=0.0, max_value=10.0, value=2.0
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
    loss_ratio_reduction_salesforce = st.sidebar.number_input(
        "Loss Ratio Reduction Attributable to Salesforce (%):",
        min_value=0.0,
        max_value=loss_ratio_reduction,
        value=loss_ratio_reduction * 0.8,
        help="Portion of Loss Ratio Reduction directly due to Salesforce investment."
    )
    expense_ratio_reduction_salesforce = st.sidebar.number_input(
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
    st.header("Executive Summary")

    # Summarize key improvements and financial impacts
    st.markdown(f"""
    **Projected Improvement in Combined Ratio:**

    - The combined ratio is projected to improve from **{current_combined_ratio:.2f}%** to **{new_combined_ratio:.2f}%**, indicating enhanced profitability.

    **Total Financial Impact:**

    - **Total Investment:** \${total_investment:.2f} million
    - **Total Savings Over {analysis_period} Years:** \${total_savings:.2f} million
    - **Return on Investment (ROI):** {roi:.2f}%
    - **Payback Period:** {payback_period if payback_period else 'Not Achieved'} years
    """)

    # --- Financial Highlights ---
    st.subheader("Financial Highlights")

    col3, col4 = st.columns(2)
    with col3:
        st.metric("Reduction in Loss Ratio (%)", f"{loss_ratio_reduction:.2f}%", help="Includes improvements from Salesforce's Advanced Data Analytics.")
        st.metric("Reduction in Expense Ratio (%)", f"{expense_ratio_reduction:.2f}%", help="Includes savings from Salesforce's Process Automation.")
        st.metric("Annual Premium Growth Rate (%)", f"{premium_growth_rate:.2f}%")
    with col4:
        st.metric("Return on Investment (ROI)", f"{roi:.2f}%", help="Overall ROI from the investment.")
        st.metric("Payback Period", f"{payback_period if payback_period else 'Not Achieved'} years")
        st.metric("Salesforce ROI", f"{roi_salesforce:.2f}%")
        st.metric("Salesforce Payback Period", f"{payback_period_salesforce if payback_period_salesforce else 'Not Achieved'} years")

    # --- Salesforce Feature Impact ---
    st.subheader("How Salesforce FSC Drives These Improvements")

    feature_impact_df = pd.DataFrame({
        "Salesforce Feature": [
            "Advanced Data Analytics",
            "Process Automation",
            "Unified Customer View",
        ],
        "Operational Improvement": [
            "Better underwriting decisions",
            "Reduced administrative workload",
            "Enhanced customer relationships"
        ],
        "Financial Impact": [
            f"Reduction in Loss Ratio by {loss_ratio_reduction_salesforce:.2f}%",
            f"Reduction in Expense Ratio by {expense_ratio_reduction_salesforce:.2f}%",
            f"Premium Growth Rate of {premium_growth_rate:.2f}%"
        ]
    })

    st.table(feature_impact_df)

    # --- Detailed Financial Projections ---
    st.subheader("Detailed Financial Projections")

    # Display the financial projections
    st.dataframe(
        financial_df.style.format({
            "Projected Premiums ($M)": "{:,.2f}",
            "Current Operating Profit ($M)": "{:,.2f}",
            "Projected Operating Profit ($M)": "{:,.2f}",
            "Annual Savings ($M)": "{:,.2f}",
            "Cumulative Savings ($M)": "{:,.2f}",
            "Annual Savings from Salesforce ($M)": "{:,.2f}",
            "Cumulative Salesforce Savings ($M)": "{:,.2f}",
        })
    )

    # --- Visualization ---
    st.header("Visualizing the Impact")

    # Combined Ratio Comparison
    fig1, ax1 = plt.subplots()
    bars = ax1.bar(
        ['Current Combined Ratio', 'Projected Combined Ratio'],
        [current_combined_ratio, new_combined_ratio],
        color=['#1f77b4', '#ff7f0e']
    )
    ax1.set_ylabel('Combined Ratio (%)')
    ax1.set_title('Improvement in Combined Ratio')
    ax1.bar_label(bars, fmt='%.2f%%')
    st.pyplot(fig1)

    # Operating Profit Over Time
    fig2, ax2 = plt.subplots()
    ax2.plot(
        financial_df["Year"],
        financial_df["Current Operating Profit ($M)"],
        label='Current Operating Profit',
        marker='o',
        linestyle='--'
    )
    ax2.plot(
        financial_df["Year"],
        financial_df["Projected Operating Profit ($M)"],
        label='Projected Operating Profit',
        marker='o'
    )
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Operating Profit ($M)')
    ax2.set_title('Operating Profit Over Time')
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

    # --- Narrative Explanation ---
    st.header("Transforming Our Business with Salesforce FSC")

    st.markdown(f"""
    **The Challenge:**

    Our company is seeking ways to improve profitability and operational efficiency in a competitive market.

    **The Salesforce Solution:**

    By investing in **Salesforce Financial Services Cloud (FSC)**, we leverage cutting-edge technology to address these challenges.

    - **Advanced Data Analytics:** Enables better underwriting decisions, directly reducing our Loss Ratio by **{loss_ratio_reduction_salesforce:.2f}%**.

    - **Process Automation:** Streamlines operations, reducing our Expense Ratio by **{expense_ratio_reduction_salesforce:.2f}%**.

    - **Unified Customer View:** Enhances customer relationships, contributing to a Premium Growth Rate of **{premium_growth_rate:.2f}%**.

    **Financial Impact:**

    Over the next **{analysis_period} years**, these improvements result in:

    - **Total Savings:** \${total_savings:.2f} million
    - **Return on Investment:** {roi:.2f}%
    - **Payback Period:** {payback_period if payback_period else 'Not Achieved'} years

    **Conclusion:**

    Investing in Salesforce FSC not only improves our financial performance but also positions us for sustainable growth and competitive advantage.
    """)

    # --- Download Options ---
    st.subheader("Download Your Results")

    csv = financial_df.to_csv(index=False)
    st.download_button(
        label="Download Financial Projections as CSV",
        data=csv,
        file_name='financial_projections.csv',
        mime='text/csv',
    )

    # Save the executive summary text for copying
    executive_summary_text = f"""
    **Projected Improvement in Combined Ratio:**

    - The combined ratio is projected to improve from **{current_combined_ratio:.2f}%** to **{new_combined_ratio:.2f}%**, indicating enhanced profitability.

    **Total Financial Impact:**

    - **Total Investment:** \${total_investment:.2f} million
    - **Total Savings Over {analysis_period} Years:** \${total_savings:.2f} million
    - **Return on Investment (ROI):** {roi:.2f}%
    - **Payback Period:** {payback_period if payback_period else 'Not Achieved'} years
    """

    st.markdown("""
    ### **Copy of Executive Summary for Reports**

    *You can copy the text below for use in your presentations or reports.*

    ---
    """ + executive_summary_text)

with tab2:
    # --- User Guide Content ---
    st.title("User Guide & AI Assistant")

    st.header("Introduction")
    st.markdown("""
    Welcome to the **P&C Carrier Combined Ratio Improvement Calculator**. This tool helps you project the financial impact of investing in Salesforce Financial Services Cloud (FSC) on your company's combined ratio and profitability.

    The calculator allows you to input your company's current financial metrics, expected improvements, and investment costs to estimate potential savings and return on investment (ROI).
    """)

    # --- AI Assistant Section ---
    st.header("Chat with the AI Assistant")
    st.markdown("""
    **Need help estimating input values?** Ask our AI assistant for suggestions and guidance.
    """)

    # Initialize session state for messages
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [
            {'role': 'system', 'content': 'You are an AI assistant that helps users estimate reasonable values for financial metrics in an insurance calculator. Provide clear and helpful suggestions based on industry standards and best practices.'}
        ]

    # Display previous messages
    for i, msg in enumerate(st.session_state['messages'][1:]):  # Skip the system prompt
        if msg['role'] == 'user':
            message(msg['content'], is_user=True, key=str(i) + '_user')
        else:
            message(msg['content'], key=str(i))

    # User input
    user_input = st.text_input("Type your question here...", key='input')

    if user_input:
        # Append user message
        st.session_state['messages'].append({'role': 'user', 'content': user_input})

        # Generate AI response
        try:
            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=st.session_state['messages'],
                temperature=0.7,
                max_tokens=150,
                n=1,
                stop=None,
            )

            ai_message = response['choices'][0]['message']['content']

            # Append assistant's response
            st.session_state['messages'].append({'role': 'assistant', 'content': ai_message})

            # Display assistant's response
            message(ai_message, key=str(len(st.session_state['messages'])))

        except openai.error.AuthenticationError:
            st.error("Authentication Error: Please check your OpenAI API key in the environment variables.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    st.header("How the Calculator Works")
    st.markdown("""
    The calculator uses a financial model that projects the impact of changes in loss ratio and expense ratio on your company's profitability over a specified analysis period. It takes into account:

    - **Gross Written Premiums (GWP):** The total premiums before deductions.
    - **Loss Ratio:** The percentage of premiums paid out in claims.
    - **Expense Ratio:** The percentage of premiums used to cover operating expenses.
    - **Combined Ratio:** The sum of the loss ratio and expense ratio; a key measure of underwriting profitability.

    By inputting expected reductions in the loss ratio and expense ratio due to operational improvements (such as those from implementing Salesforce FSC), the calculator projects:

    - **New Combined Ratio**
    - **Annual and Cumulative Savings**
    - **Return on Investment (ROI)**
    - **Payback Period**
    """)

    st.header("Step-by-Step Instructions")

    st.markdown("""
    **Step 1: Enter Current Financial Metrics**

    - **Annual Gross Written Premiums ($M):** Input your company's total annual premiums in millions of dollars.
    - **Current Loss Ratio (%):** Enter your company's current loss ratio.
    - **Current Expense Ratio (%):** Enter your company's current expense ratio.

    **Step 2: Input Expected Improvements After Investment**

    - **Expected Reduction in Loss Ratio (%):** Estimate the percentage reduction in the loss ratio due to improvements.
    - **Expected Reduction in Expense Ratio (%):** Estimate the percentage reduction in the expense ratio.
    - **Annual Premium Growth Rate (%):** Enter the expected annual growth rate of premiums.
    - **Analysis Period (Years):** Choose the number of years over which to analyze the impact.

    **Step 3: Provide Salesforce FSC Investment Costs**

    - **Initial Investment Cost ($M):** Input the upfront cost of investing in Salesforce FSC.
    - **Annual Ongoing Costs ($M):** Enter the expected annual costs associated with Salesforce FSC.

    **Step 4: Add Other Ongoing Costs (Optional)**

    - **Annual Other Ongoing Costs ($M):** Include any additional annual costs not related to Salesforce.

    **Step 5: Attribute Improvements to Salesforce**

    - **Loss Ratio Reduction Attributable to Salesforce (%):** Estimate the portion of the loss ratio reduction directly due to Salesforce.
    - **Expense Ratio Reduction Attributable to Salesforce (%):** Estimate the portion of the expense ratio reduction directly due to Salesforce.

    **Step 6: Review the Results**

    - The calculator will display an **Executive Summary** with key financial impacts.
    - **Financial Highlights** provide detailed metrics.
    - **Visualizations** help you see the projected improvements over time.
    - The **Narrative Explanation** summarizes how Salesforce FSC contributes to these improvements.

    **Step 7: Download Your Results**

    - Use the **Download** option to export the financial projections as a CSV file.
    - Copy the **Executive Summary** for use in reports or presentations.
    """)

    st.header("Understanding the Model")

    st.markdown("""
    The calculator's model projects financial outcomes based on the inputs provided:

    - **Gross Written Premiums (GWP):** Projected to grow annually based on the **Annual Premium Growth Rate**.
    - **Current Operating Profit:** Calculated by subtracting losses and expenses from GWP using the current loss and expense ratios.
    - **Projected Operating Profit:** Calculated using the new, improved loss and expense ratios.
    - **Annual Savings:** The difference between the projected and current operating profits.
    - **Cumulative Savings:** The total savings accumulated over the analysis period.
    - **Return on Investment (ROI):** Calculated by dividing the total savings by the total investment cost.
    - **Payback Period:** The time it takes for cumulative savings to equal the total investment cost.

    **Attribution to Salesforce:**

    - The model separates the portion of savings directly attributable to Salesforce FSC based on the percentages provided.
    - This helps in understanding the specific financial impact of the Salesforce investment.
    """)

    st.header("Tips for Using the Calculator")

    st.markdown("""
    - **Use Realistic Estimates:** Input conservative and realistic numbers for expected improvements.
    - **Understand Attribution:** Carefully consider what portion of improvements can be directly attributed to Salesforce FSC.
    - **Explore Scenarios:** Try different inputs to see how changes affect the financial outcomes.
    - **Consult Stakeholders:** Engage with your finance and operations teams to gather accurate data.
    """)

    st.header("Need Assistance?")

    st.markdown("""
    If you have any questions or need further assistance:

    - **Chat with the AI Assistant:** Use the chat above to get suggestions and answers.
    - **Provide Feedback:** We welcome your feedback to improve the calculator.
    """)

    st.header("Disclaimer")

    st.markdown("""
    This calculator is a decision-support tool intended to provide estimates based on the inputs provided. Actual results may vary. Always consult with a financial professional before making investment decisions.
    """)