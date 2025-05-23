# import streamlit as st
# import requests

# # Set Streamlit page configuration
# st.set_page_config(page_title="AI Query Tool", page_icon="🧠", layout="wide")  # Set layout to wide

# # Define session state for navigation
# if "page" not in st.session_state:
#     st.session_state.page = "connect"  # Start on the connect page

# # Custom styling for wider SQL box and DataFrame
# st.markdown(
#     """
#     <style>
#         /* Make SQL query result box wider */
#         .stCode {
#             width: 100% !important;
#             max-width: 1000px !important;
#             overflow-x: auto;
#             font-size: 14px;
#         }

#         /* Make Query Result table wider */
#         .stDataFrame {
#             width: 100% !important;
#         }

#         /* Center the content */
#         .block-container {
#             max-width: 1200px;
#             margin: auto;
#         }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# st.title("🚀 Multi-Database AI Query Tool")

# # -------------------- Page 1: Database Connection --------------------
# if st.session_state.page == "connect":
#     with st.container():
#         st.markdown("### 🔗 Connect to a Database")

#         col1, col2 = st.columns(2)
#         with col1:
#             db_type = st.selectbox("Database Type", ["PostgreSQL", "MongoDB", "MySQL", "MSSQL"])

#         with col2:
#             host = st.text_input("Host")

#         col3, col4 = st.columns(2)
#         with col3:
#             port = st.text_input("Port")

#         with col4:
#             user = st.text_input("Username")

#         password = st.text_input("Password", type="password")

#         if st.button("🔌 Connect"):
#             if not host or not port or not user or not password:
#                 st.error("⚠️ Please fill in all fields before connecting.")
#             else:
#                 db_config = {"host": host, "port": port, "user": user, "password": password}
#                 response = requests.post("http://127.0.0.1:5000/connect", json={"db_type": db_type, "db_config": db_config})

#                 if response.status_code == 200:
#                     st.success(f"✅ Connected to {db_type} successfully!")
#                     st.session_state.db_type = db_type
#                     st.session_state.db_config = db_config
#                     st.session_state.page = "query"  # Move to next page
#                     st.rerun()
#                 else:
#                     st.error("❌ Connection failed! Please check your credentials.")

# # -------------------- Page 2: Query the Database --------------------
# elif st.session_state.page == "query":
#     st.markdown(f"### 🤖 Ask a question for `{st.session_state.db_type}`")

#     database = st.text_input("📂 Enter Database Name")
#     user_query = st.text_area("💬 Enter your question")

#     col1, col2 = st.columns(2)
#     with col1:
#         if st.button("🔍 Get Answer"):
#             if not database or not user_query:
#                 st.error("⚠️ Please enter both database name and query.")
#             else:
#                 db_config = st.session_state.db_config
#                 db_config["database"] = database  # Include the database name

#                 response = requests.post(
#                     "http://127.0.0.1:5000/ask",
#                     json={"query": user_query, "db_type": st.session_state.db_type, "db_config": db_config},
#                 )

#                 if response.status_code == 200:
#                     result = response.json()
#                     st.markdown("#### 📝 Generated SQL Query:")
#                     st.code(result["sql"], language="sql" if st.session_state.db_type != "MongoDB" else "json")

#                     st.markdown("#### 📊 Query Result:")
#                     if result["result"].get("data"):
#                         import pandas as pd
#                         df = pd.DataFrame(result["result"]["data"], columns=result["result"].get("columns", []))
#                         st.dataframe(df, width=1000)  # Increase width of DataFrame
#                     else:
#                         st.write("🔍 No results found.")
#                 else:
#                     st.error("❌ Error processing request.")

#     with col2:
#         if st.button("🔙 Back"):
#             st.session_state.page = "connect"  # Go back to connection page
#             st.rerun()




import streamlit as st
import requests

st.title("Multi-Database AI Query Tool")

# Step 1: Select Database Type
db_type = st.selectbox("Select Database Type", ["PostgreSQL", "MongoDB", "MySQL", "MSSQL"])

# Step 2: Enter Connection Details
st.subheader("Enter Database Connection Details")
host = st.text_input("Host", "")
port = st.text_input("Port", "")
database = st.text_input("Database Name", "")
user = st.text_input("Username", "")
password = st.text_input("Password", type="password")

if st.button("Connect"):
    db_config = {
        "host": host,
        "port": port,
        "database": database,
        "user": user,
        "password": password,
    }
    response = requests.post("http://127.0.0.1:5000/connect", json={"db_type": db_type, "db_config": db_config})

    if response.status_code == 200:
        st.success(f"Connected to {db_type} successfully!")
        st.session_state["db_type"] = db_type
        st.session_state["db_config"] = db_config
    else:
        st.error(response.json().get("error", "Unknown error"))

# Step 3: Ask Query
if "db_type" in st.session_state:
    st.subheader(f"Ask a question for {st.session_state['db_type']}")

    user_query = st.text_input("Enter your question:")

    if st.button("Get Answer"):
        response = requests.post(
            "http://127.0.0.1:5000/ask",
            json={"query": user_query, "db_type": st.session_state["db_type"], "db_config": st.session_state["db_config"]},
        )

        if response.status_code == 200:
            result = response.json()
            st.subheader("Generated SQL Query:")
            st.code(result["sql"], language="sql")

            st.subheader("Query Result:")
            if result["result"].get("data"):
                import pandas as pd
                df = pd.DataFrame(result["result"]["data"], columns=result["result"]["columns"])
                st.dataframe(df)
            else:
                st.write("No results found.")
        else:
            st.error(response.json().get("error", "Unknown error"))