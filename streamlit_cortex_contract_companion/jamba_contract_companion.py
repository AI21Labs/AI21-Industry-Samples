# Import necessary libraries
import streamlit as st
import pandas as pd
import json
from snowflake.snowpark.context import get_active_session

# Global variable to store contract description
global original_contract_description

# Set up the main title of the Streamlit app
st.title("AI21's Jamba-Instruct in Snowflake Cortex :snake::snowflake:")

# Provide an introduction to Jamba-Instruct and its integration with Snowflake Cortex
st.write("""
Jamba-Instruct, a groundbreaking foundation model from [AI21 Labs](https://www.ai21.com/), is now available on Snowflake Cortex! 
The integration allows users to seamlessly access Jamba-Instruct from within their Snowflake environment. 
Jamba excels in handling long context use cases. With a 256k context window, Jamba enables advanced techniques 
like many-shot prompting and efficient data extraction in fields like finance and healthcare.

**Jamba Use Cases:**
- Contract summarization and analysis
- Legal document review
- General question answering
- Information extraction from complex texts

**Helpful Links:**
- [Jamba Cortext Launch Blog](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
- [Cortex Complete Documentation (SNOWFLAKE.CORTEX)](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
""")

st.markdown("---")

# Get the current Snowflake session
session = get_active_session()

# Function to run a general Snowflake query using the selected language model | FUNCTION NOT USED IN THIS APP
def run_snowflake_query(question):
    params = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        '{option}',
        [
            {{'role': 'system', 'content': 'You are a helpful AI assistant. Answer the question in a helpful and concise way'}},
            {{'role': 'user', 'content': '{question}'}}
        ],
        {{
            'temperature': 0.7,
            'max_tokens': 300
        }}
    );
    """
    result = session.sql(params).collect()
    return result[0][0] if result else None

# Set up the header for the Contract Companion section
st.header("Jamba Contract Companion :snake:")

# Provide an explanation of the Contract Companion functionality
st.write("""
Contract Companion demonstrates Jamba-Instruct's model functionality within Snowflake Cortext. To show examples of reasoning over large amounts of text, contract 
companion uses Cybersyn's [LLM_TRAINING_ESSENTIALS](https://app.snowflake.com/marketplace/listing/GZTSZ290BUX1X/cybersyn-llm-training-essentials) database (specifically the GOVERNMENT_CONTRACT_INDEX view), 
which is available for free in the Snowflake data marketpalce.

This demo uses 1 row of data from GOVERNMENT_CONTRACT_INDEX, which is a long procrument contract for a United States Navy cargo ship. To view the raw table data click 'View Contract Details' below. (To expand 'Contract Description' double click the cell)
""")


# Function to fetch contract data from Snowflake
def run_data_query():
    query = """
    (
    select agency, department, original_contract_title, original_contract_description, length(original_contract_description) as ccount
    from LLM_TRAINING_ESSENTIALS.cybersyn.government_contract_index
    where ccount between 25000 and 32000
    and original_contract_description <> 'null'
    and department <> 'null'
    and agency <> 'null'
    and original_contract_title = 'MAN DIESEL BRAND NAME ENGINE PARTS'
    order by ccount DESC
    limit 1)
    """
    result = session.sql(query).collect()
    return result[0] if result else None

# Function to run a contract-specific query using the selected language model
def run_contract_query(question):
    params = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        '{option}',
        ARRAY_CONSTRUCT(
            OBJECT_CONSTRUCT('role', 'system', 'content', 'You are a helpful AI contract assistant. Answer the question in a helpful and concise way, if you don''t know the answer respond with "I don''t know"'),
            OBJECT_CONSTRUCT('role', 'user', 'content', '{question}')
        ),
        OBJECT_CONSTRUCT('temperature', 0.7, 'max_tokens', 3000)
    );
    """
    result = session.sql(params).collect()
    return result[0][0] if result else None

# Fetch contract data
contract_data = run_data_query()

# Display the SQL query used to fetch contract data
with st.expander("View SQL Query:"):
    st.code('''
    select agency, department, original_contract_title, original_contract_description, length(original_contract_description) as ccount
    from LLM_TRAINING_ESSENTIALS.cybersyn.government_contract_index
    where ccount between 25000 and 32000
    and original_contract_description <> 'null'
    and department <> 'null'
    and agency <> 'null'
    and original_contract_title = 'MAN DIESEL BRAND NAME ENGINE PARTS'
    order by ccount DESC
    limit 1)
    ''')

# Button to display contract details
if st.button('View Contract Details'):
    if contract_data:
        # Create a DataFrame for the main details
        df_main = pd.DataFrame({
            'Agency': [contract_data['AGENCY']],
            'Department': [contract_data['DEPARTMENT']],
            'Contract Title': [contract_data['ORIGINAL_CONTRACT_TITLE']],
            'Description Length': [contract_data['CCOUNT']],
            'Contract Description': [contract_data['ORIGINAL_CONTRACT_DESCRIPTION']]
        })
        
        # Display the main details as a DataFrame
        st.dataframe(df_main)
        
        # Create a DataFrame for the full description
        df_description = pd.DataFrame({
            'Full Contract Description': [contract_data['ORIGINAL_CONTRACT_DESCRIPTION']]
        })
        
        # Uncomment the following lines to display the full description in an expander
        #with st.expander("View Full Contract Description"):
            #st.dataframe(df_description)
    else:
        st.error("No contract data available.")




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
"mistral-7b",
"gemma-7b",))

# Provide information about using Jamba with long contracts
st.write("""
The text in the Contract Description is verbose and has many details, which is typical for a Request for Quote (RFQ) or Request for Proposal (RFP) document. 
Using Jamba, we are able to submit large amounts of text in a single prompt and reason over it quickly. 

Some example prompts for long contracts:
- Summarize | Summarize the key themes in this contract
- Synthesize | Generate a response template for this request for quote, as to be filled out by the bidders
- Q&A | What are the FAR and DFARS provisions that apply to this contract?
- Q&A | What are the key dates that must be met in this contract?
- Q&A | What NAICS codes are mentioned within the contract?
- Q&A | Does the work need to be done on site?

""")

# Text input for user's question
contract_question = st.text_input("Enter your question:", "Summarize the key themes in this contract")


# Button to run the contract query
if st.button('Run Contract Query'):
    with st.spinner("Fetching contract data and running query..."):
        if contract_data:
            original_contract_description = contract_data['ORIGINAL_CONTRACT_DESCRIPTION']
            
            # Prepare the contract question with context
            contract_question_context = f"{contract_question}\n\n\n\n{original_contract_description}".replace('"', '').replace("'", '')
            with st.expander("View Query and Context"):
                st.write(contract_question_context)
            
            # Run the contract query
            query_result = run_contract_query(contract_question_context)
            
            if query_result:
                # Parse the JSON string
                result_json = json.loads(query_result)
                
                # Display the message in a text area
                message = result_json['choices'][0]['messages']
                st.write("Jamba Contract Companion Response:")
                st.write(message)
                
                # Display the full response in an expandable section
                with st.expander("View Full Response"):
                    st.json(result_json)
            else:
                st.error("No result returned from the contract query.")
        else:
            st.error("No result returned from the data query.")
    
    st.success('Done!')
    st.write("""
    The 'View Full Response' expander shows the json response returned from Snowflake Cortex. You can see details such as number of tokens submitted and returned.
    """)

st.markdown("---")

