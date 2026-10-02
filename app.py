import streamlit as st
import pandas as pd
from google import genai
import re
import matplotlib.pyplot as plt

# 1. AI API Setup 
API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=API_KEY)

# Page Configuration
st.set_page_config(page_title="My AI Data Agent", layout="wide")
st.title("🤖 My Autonomous Data Analyst")

# Sidebar for Data Upload
with st.sidebar:
    st.header("📂 Data Upload")
    uploaded_file = st.file_uploader("Upload Excel or CSV file", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        # File loading
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.session_state['data'] = df
        st.success(f"File '{uploaded_file.name}' loaded successfully!")
        
        # Schema extracting
        schema_info = str(df.dtypes)
        
        # UI Previews
        with st.expander("🔍 View Raw Data & Schema"):
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(df.head())
            with col2:
                st.write(df.dtypes)

        # Chat Interface
        st.divider()
        user_query = st.chat_input("Ask me anything about this data...")
        
        if user_query:
            st.chat_message("user").write(user_query)
            
            with st.chat_message("assistant"):
                status_text = st.empty()
                status_text.info("Data analyze kar raha hoon...")
                
                # THE BRAIN: System Prompt
                prompt = f"""
                You are an expert Data Analyst AI.
                I have a pandas DataFrame named 'df'.
                Here is the schema (columns and data types):
                {schema_info}
                
                User Request: "{user_query}"
                
                Write strictly Python code to solve this request.
                Rules:
                1. Assume 'df', 'pd', 'plt', and 'st' (streamlit) are already imported.
                2. Do not use print(). Use 'st.write()', 'st.dataframe()', or Streamlit chart functions to display the final output.
                3. If you create a matplotlib plot, display it using 'st.pyplot(plt.gcf())'.
                4. Write ONLY the code inside ```python ``` tags. No explanations.
                """
                
                python_code = None # Code variable pehle se define kar diya
                
                # --- STEP 1: API SE BAAT KARNA (Google Server Error Handle) ---
                try:
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt
                    )
                    
                    # Regex se code nikalna
                    code_match = re.search(r'```python\n(.*?)\n```', response.text, re.DOTALL)
                    if code_match:
                        python_code = code_match.group(1).strip()
                    else:
                        st.error("AI couldn't generate proper code. Raw response:")
                        st.write(response.text)
                        
                except Exception as api_error:
                    status_text.error(f"Google API Error: {api_error}")
                    st.warning("⚠️ Yeh Google Server ka issue hai (Bheed/Traffic). Thodi der me dobara try karo. Tumhara code bilkul sahi hai!")
                
                # --- STEP 2: PYTHON CODE RUN KARNA (Execution Error Handle) ---
                if python_code:
                    with st.expander("🛠️ View AI Generated Code"):
                        st.code(python_code, language='python')
                    
                    status_text.empty() 
                    
                    try:
                        exec(python_code, {'df': df, 'pd': pd, 'st': st, 'plt': plt})
                    except Exception as exec_error:
                        st.error(f"Python Execution Error: {exec_error}")
                        st.warning("🤖 Ye error AI ne jo Code likha hai usme aaya hai. Aap simply likh sakte ho: 'Fix this error'.")

    except Exception as e:
        st.error(f"Error loading file: {e}")
else:
    st.info("👈 Please upload a file to start analysis.")
