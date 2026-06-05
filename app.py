import streamlit as st
import requests
import time
import os

st.set_page_config(
    page_title="AskDocs-RAG Conversational Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure Styling for dark/sleek theme
st.markdown("""
<style>
    /* Sleek container styles */
    .metric-card {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #334155;
        margin-bottom: 10px;
    }
    .source-block {
        background-color: #0f172a;
        padding: 12px;
        border-radius: 6px;
        border-left: 3px solid #3b82f6;
        margin-top: 8px;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 AskDocs-RAG Conversational AI Agent")
st.caption("Enterprise-grade Agentic Retrieval-Augmented Generation dashboard with RBAC and Tracing")

# Sidebar Configuration for Security, RBAC & Endpoints
st.sidebar.title("🔒 Security & RBAC Configuration")
st.sidebar.write("Simulate user authentication and observe active database filtering.")

username = st.sidebar.text_input("Username", value="sreeram")
role = st.sidebar.selectbox(
    "User Security Role Group", 
    options=["admin", "engineering", "hr", "public"],
    index=1  # Default to engineering
)
backend_url = st.sidebar.text_input("Backend API URL", value="http://localhost:8000")

# Session state initializations
if "messages" not in st.session_state:
    st.session_state.messages = []
if "token" not in st.session_state:
    st.session_state.token = None

# Helper to fetch JWT Access Token from API
def fetch_access_token():
    try:
        response = requests.post(
            f"{backend_url}/auth/token",
            json={"username": username, "role": role},
            timeout=5
        )
        if response.status_code == 200:
            token = response.json().get("access_token")
            st.session_state.token = token
            st.sidebar.success(f"Access token successfully fetched!\nRole: {role.upper()}")
        else:
            detail = response.json().get("detail", "Unknown authentication error")
            st.sidebar.error(f"Auth Error: {detail}")
            st.session_state.token = None
    except Exception as e:
        st.sidebar.error(f"Backend offline or unreachable: {str(e)}")
        st.session_state.token = None

# Auto fetch token on first load or selector changes
if st.sidebar.button("Re-authenticate / Sync Session") or st.session_state.token is None:
    fetch_access_token()

if st.session_state.token:
    st.sidebar.info("🔒 Session Authorized (Token stored in memory)")

# Clear chat history helper
if st.sidebar.button("Clear Conversation History"):
    st.session_state.messages = []
    st.success("Chat history cleared.")
    st.rerun()

# Display conversational chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display stored citations/metadata if available
        if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
            with st.expander("📚 View Document Citations"):
                for idx, src in enumerate(msg["sources"]):
                    filename = src.get("metadata", {}).get("file_name", "unknown")
                    score = src.get("score", 1.0)
                    text = src.get("text", "")
                    req_role = src.get("metadata", {}).get("required_role", "public")
                    
                    st.markdown(f"**Source {idx+1}: `{filename}`** | Relevance: `{score:.4f}` | Category: `{req_role.upper()}`")
                    st.markdown(f"```text\n{text}\n```")
                    
        # Display stored metrics if available
        if msg["role"] == "assistant" and "metrics" in msg:
            m = msg["metrics"]
            st.caption(f"⏱️ Latency: `{m['latency']:.2f} ms` | Sources Used: `{m['sources_count']}`")

# Accept new user query message
if prompt := st.chat_input("Enter your document question here..."):
    # Render user query
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    if st.session_state.token is None:
        st.error("Cannot query: Unauthorized. Please check if your FastAPI backend server is running and authenticated.")
    else:
        # Generate assistant placeholder loader
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("*Agent is thinking and querying knowledge bases...*")
            
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            payload = {
                "message": prompt,
                "session_id": f"streamlit_{username}"
            }
            
            try:
                # Query backend chat endpoint
                response = requests.post(
                    f"{backend_url}/agent/chat",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("response", "")
                    sources = data.get("sources", [])
                    latency = data.get("execution_time_ms", 0.0)
                    
                    # Renders response message
                    message_placeholder.markdown(answer)
                    
                    # Renders expandable sources/citations
                    if sources:
                        with st.expander("📚 View Document Citations"):
                            for idx, src in enumerate(sources):
                                filename = src.get("metadata", {}).get("file_name", "unknown")
                                score = src.get("score", 1.0)
                                text = src.get("text", "")
                                req_role = src.get("metadata", {}).get("required_role", "public")
                                
                                st.markdown(f"**Source {idx+1}: `{filename}`** | Relevance: `{score:.4f}` | Category: `{req_role.upper()}`")
                                st.markdown(f"```text\n{text}\n```")
                    
                    # Latency tracking caption
                    st.caption(f"⏱️ Latency: `{latency:.2f} ms` | Sources Used: `{len(sources)}`")
                    
                    # Append message to persistent chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "metrics": {
                            "latency": latency,
                            "sources_count": len(sources)
                        }
                    })
                    
                else:
                    detail = response.json().get("detail", "Error during inference execution.")
                    message_placeholder.markdown(f"⚠️ **Error from Backend API**: {detail}")
            except Exception as e:
                message_placeholder.markdown(f"⚠️ **Connection Failure**: Failed to communicate with FastAPI agent service. Error: {str(e)}")
