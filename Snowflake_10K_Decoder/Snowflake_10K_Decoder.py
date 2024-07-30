# Import necessary libraries
import streamlit as st
import pandas as pd
import json
from snowflake.snowpark.context import get_active_session


# Set up the main title of the Streamlit app
st.title("AI21's Jamba-Instruct in Snowflake Cortex :snake::snowflake:")

# Provide an introduction to Jamba-Instruct and its integration with Snowflake Cortex
st.write("""
Jamba-Instruct, a groundbreaking foundation model from [AI21 Labs](https://www.ai21.com/), is now available on Snowflake Cortex! 
The integration allows users to seamlessly access Jamba-Instruct from within their Snowflake environment. 
Jamba excels in handling long context use cases. With a 256k context window, Jamba enables advanced techniques 
like many-shot prompting and efficient data extraction in fields like finance and healthcare.

**Jamba Use Cases:**
- Multi-Document summarization and analysis
- Legal document review
- General question answering
- Information extraction from complex texts

**Helpful Links:**
- [Jamba Cortex Launch Blog](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
- [Cortex Complete Documentation (SNOWFLAKE.CORTEX)](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
""")

st.markdown("---")

# Get the current Snowflake session
session = get_active_session()


st.header("Jamba 10-K Decoder :snake:")

# Provide an explanation of the app functionality
st.write("""
10-K Decoder demonstrates Jamba-Instruct's model functionality within Snowflake Cortex. To show examples of reasoning over large amounts of text, 10K Decoder 
uses Cybersyn's [SEC_FILINGS](https://app.snowflake.com/marketplace/listing/GZTSZAS2KH9/cybersyn-sec-filings?originTab=provider&providerName=Cybersyn%2C&ref=blog.streamlit.io) database (specifically the SEC_REPORT_TEXT_ATTRIBUTES and SEC_REPORT_INDEX tables), 
which is available for free in the Snowflake data marketpalce.

This app uses the last 3 Fiscal Years of NVIDIA Corp's SEC 10-K filings. To view the raw table data click 'View 10K Detail' below. (To expand 'VALUE' double click the cell)
""")


sec_query = """
    (
select A.*, B.* from "SEC_FILINGS"."CYBERSYN".SEC_REPORT_TEXT_ATTRIBUTES A
left join "SEC_FILINGS"."CYBERSYN".SEC_REPORT_INDEX B
on A.CIK = B.CIK
where B.company_name = 'NVIDIA CORP' --limit the results to only show NVIDIA
and B.form_type = '10-K' --10K filing only
and A.variable_name = '10-K Filing Text' --10K filing only
and ((A.PERIOD_END_DATE = '2024-01-28' and B.FISCAL_YEAR = 2023) 
    or (A.PERIOD_END_DATE = '2023-01-29' and B.FISCAL_YEAR = 2022) 
    or (A.PERIOD_END_DATE = '2022-01-30' and B.FISCAL_YEAR = 2021)) --NVIDIA 10K filings for the last 3 years
order by FILED_DATE desc, PERIOD_END_DATE desc)
    """

# Function to fetch sec data from Snowflake
def run_data_query():
    query = sec_query
    result = session.sql(query).collect()
    return result

# Function to run a specific query using the selected language model
def run_query(question):
    params = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        '{option}',
        ARRAY_CONSTRUCT(
            OBJECT_CONSTRUCT('role', 'user', 'content', '{question}')
        ),
        OBJECT_CONSTRUCT('temperature', 0.3, 'max_tokens', 2000)
    );
    """
    result = session.sql(params).collect()
    return result[0][0] if result else None

# Fetch the data
filing_data = run_data_query()

# Display the SQL query used to fetch the data
with st.expander("View SQL Query:"):
    st.code(sec_query)

# Button to display the filing details
if st.button('View 10K Detail'):
    if filing_data:
        # Create a DataFrame for the main details
        df_main = pd.DataFrame([{
            'SEC_DOCUMENT_ID': row['SEC_DOCUMENT_ID'],
            'VARIABLE_NAME': row['VARIABLE_NAME'],
            'COMPANY_NAME': row['COMPANY_NAME'],
            'FILED_DATE': row['FILED_DATE'],
            'FISCAL_YEAR': row['FISCAL_YEAR'],
            'VALUE': row['VALUE']
        } for row in filing_data])
        
        # Display the main details as a DataFrame
        st.dataframe(df_main)

        # Create a string variable with all VALUE data concatenated
        all_values = ' '.join(df_main['VALUE'].astype(str))
        
        # Display the concatenated string
        # st.write("All VALUES concatenated:")
        # st.text(all_values)
    else:
        st.error("No filing data available.")


st.write("""
Of the language models available in Snowflake Cortex, only Jamba-Instruct can handle context lenghts up to 256K tokens!
""")

# Dropdown to select a language model
option = st.selectbox(
"Select a language model:",
("snowflake-arctic",
"mistral-large",
"reka-flash",
"jamba-instruct",
"mixtral-8x7b",
"llama2-70b-chat",
"llama3-8b",
"llama3-70b",
"llama3.1-405b",
"mistral-7b",
"gemma-7b",))

# Provide information about using Jamba with long text
st.write("""
The amount of text in an annual 10k filing is dense, and will push the context limits of language models to their breaking point. The most recent NVIDIA 10K is ~75K tokens long. 

Using Jamba, we are able to submit large amounts of text in a single prompt and reason over it quickly. This means we can use Jamba as a RAG alternative as it supports up to 256K tokens! The token limit is so high, that we can analyze 3 years of NVIDIA 10K filings within a single prompt.

Some example prompts for long 10K filings:
- How was the financial performance in each filing?
- How has NVIDIA Corp's revenue and profit changed over the years?
- How has the company's market share in its primary industries changed?
- What major acquisitions or partnerships has the company engaged in?
- How has the company's discussion of sustainability initiatives or environmental impact changed across the filings?

""")

# Text input for user's question
question = st.text_input("Enter your question:", "Summarize the key themes in these 10K filings")
question = question + "##################\n\n"



# Button to run the sec filing query
if st.button('Run Filing Query'):
    with st.spinner("Fetching filing data and running query..."):
        if filing_data:
            df_main = pd.DataFrame([{
                'SEC_DOCUMENT_ID': row['SEC_DOCUMENT_ID'],
                'VARIABLE_NAME': row['VARIABLE_NAME'],
                'COMPANY_NAME': row['COMPANY_NAME'],
                'FILED_DATE': row['FILED_DATE'],
                'FISCAL_YEAR': row['FISCAL_YEAR'],
                'VALUE': row['VALUE']
            } for row in filing_data])
            
            # Create a string variable with all VALUE data concatenated
            all_values = ' '.join(df_main['VALUE'].astype(str))
            
            # Prepare the question with context
            question_context = f"{question}\n\n\n\n{all_values}".replace('"', '').replace("'", '')
            with st.expander("View Query and Context"):
                st.write(question_context)
            
            # Run the query
            query_result = run_query(question_context)
            
            if query_result:
                # Parse the JSON string
                result_json = json.loads(query_result)
                
                # Display the message in a text area
                message = result_json['choices'][0]['messages']
                st.write("Jamba-Instruct Response:")
                st.write(message)
                
                # Display the full response in an expandable section
                with st.expander("View Full Response"):
                    st.json(result_json)
            else:
                st.error("No result returned from the query.")
        else:
            st.error("No result returned from the data query.")
    
    st.success('Done!')
    st.write("""
    The 'View Full Response' expander shows the json response returned from Snowflake Cortex. You can see details such as number of tokens submitted and returned.
    """)

st.markdown("---")