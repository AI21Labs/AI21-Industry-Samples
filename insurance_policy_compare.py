import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
import json

# Set up the main title of the Streamlit app
st.title("Insurance Plan Comparison with Jamba-1.5-Large and Snowflake Cortex:health_worker::snowflake:")

# Get the current Snowflake session
session = get_active_session()

st.write("""
    Welcome to the Insurance Plan Comparison App! This tool empowers you to compare various healthcare plans using detailed plan information loaded into a Snowflake table. With the help of the Jamba-1.5-Large model, you can pose specific questions to guide your decision-making process. Whether your focus is on out-of-pocket costs, prescription coverage, or options for families, this app facilitates the comparison of up to two plans simultaneously!

    By utilizing Jamba 1.5 in Snowflake Cortex, you benefit from its ability to handle long context inputs of up to 256k tokens. This capability is particularly advantageous when comparing extensive healthcare plans, ensuring you receive thorough and comprehensive insights tailored to your needs.

    For more information about specific plans, you can access the [coverage policy documents here](https://www.bluecrossma.org/myblue/learn-and-save/plans-and-benefits/coverage-policy-documents).
""")



# Function to fetch insurance plans from Snowflake
def get_insurance_plans():
    query = "SELECT DISTINCT planname FROM INSURANCE.PUBLIC.HMO2 WHERE planname <> 'filename' ORDER BY planname"
    result = session.sql(query).collect()
    return [row['PLANNAME'] for row in result]

# Function to run a query using Jamba-1.5-Large
def run_jamba_query(question, plan_names):
    # Fetch details for all selected plans
    plan_details_query = f"""
    SELECT planname, detail
    FROM INSURANCE.PUBLIC.HMO2 
    WHERE planname IN ({', '.join([f"'{name}'" for name in plan_names])})
    """
    plan_details = session.sql(plan_details_query).collect()
    
    # Concatenate plan details with delimiters
    def escape_quotes(s):
        return s.replace("'", "''").replace('"', '""')
    
    concatenated_details = " ".join([
        f'<plan name="{escape_quotes(row["PLANNAME"])}">{escape_quotes(row["DETAIL"])}</plan>'
        for row in plan_details
    ])
    
    # Construct the query for Jamba
    jamba_query = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        'jamba-1.5-large',
        ARRAY_CONSTRUCT(
            OBJECT_CONSTRUCT('role', 'user', 'content', '{escape_quotes(question)} {escape_quotes(concatenated_details)}')
        ),
        OBJECT_CONSTRUCT('temperature', 0.3, 'max_tokens', 5000)
    ) AS response;
    """
    
    result = session.sql(jamba_query).collect()
    return result[0]['RESPONSE'] if result else None

# Get all available plans
all_plans = get_insurance_plans()

# Allow user to select up to 2 plans
selected_plans = st.multiselect("Select up to 2 plans to compare:", all_plans, max_selections=2)

st.write("""
    Below, you can select one of the pre-canned questions or enter your own custom question. 
    The app uses this question to analyze the selected plans and provide a tailored response.
""")


# Pre-canned questions
pre_canned_questions = [
    "I need an in-patient procedure, help me choose which plan is best for me?",
    "Which healthcare plan should I choose between these 2?",
    "How much would I pay out of pocket to see my PCP every year?",
    "I have a large family with 4 dependents. Which plan is right for me?",
    "How much prescription coverage is paid for by each of these plans?",
    "I am over 18 years old and the only person who would be covered by my insurance. Is vision covered by these insurance plans?",
    "Custom question"
]



# Dropdown for pre-canned questions
selected_question = st.selectbox("Select a pre-canned question or choose 'Custom question':", pre_canned_questions)

st.markdown("---")
st.header("HC Plan Comparison Question")


# Text input for user's question
if selected_question == "Custom question":
    question = st.text_input("Enter your custom question about the selected plans:")
else:
    question = st.text_input("Question about the selected plans:", value=selected_question)




# Function to escape special markdown characters
def escape_markdown(text):
    markdown_special_chars = r"\*_`[]()#+-.!"
    return ''.join(f"\\{char}" if char in markdown_special_chars else char for char in text)


st.write("""
    The model response will appear below, offering detailed comparisons based on your selected question and plans. 
    You can expand the 'View Full Response' section to see the complete model output in JSON format.
""")


# Button to run the comparison
if st.button('Compare Plans') and len(selected_plans) > 0:
    with st.spinner("Analyzing plans..."):
        # Run Jamba query for selected plans
        jamba_response = run_jamba_query(question, selected_plans)
        
        if jamba_response:
            try:
                # Parse the JSON response
                parsed_response = json.loads(jamba_response)
                
                # Extract the message content from the nested structure
                if 'choices' in parsed_response and len(parsed_response['choices']) > 0:
                    choice = parsed_response['choices'][0]
                    if 'messages' in choice:
                        message = choice['messages']
                    elif 'mesages' in choice:  # Handle potential typo in key name
                        message = choice['mesages']
                    else:
                        message = str(choice)  # Fallback: convert the entire choice to string
                else:
                    message = str(parsed_response)  # Fallback: convert the entire response to string
                
                st.subheader("Model Response:")
                # Escape common Markdown characters and display with st.write
                escaped_message = (
                    message.replace("$", "\\$")
                           .replace("*", "\\*")
                           .replace("_", "\\_")
                           .replace("[", "\\[")
                           .replace("]", "\\]")
                           .replace("(", "\\(")
                           .replace(")", "\\)")
                           .replace("#", "\\#")
                           .replace("+", "\\+")
                           .replace("-", "\\-")
                           .replace(".", "\\.")
                           .replace("!", "\\!")
                )
                
                st.write(escaped_message)
                
                # Add button to view full response JSON
                with st.expander('View Full Response'):
                    st.json(parsed_response)
                
            except json.JSONDecodeError:
                st.error("Failed to parse JSON response. Raw response:")
                st.write(f"<pre>{jamba_response}</pre>")
        else:
            st.error("No response from Jamba-1.5-Large.")
    st.success('Comparison complete!')
    
st.markdown("---")
st.write("Note: This app uses the Jamba-1.5-Large model to analyze insurance plans. The app  makes a single call to Jamba with concatenated plan details for efficient comparison.")