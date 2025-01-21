from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, abort, session,send_file,flash
from pytrends.request import TrendReq
import asyncio
import nest_asyncio
import glob, json, shutil
import sqlite3
import os
import requests
import time
import threading
from youtube_transcript_api import YouTubeTranscriptApi
from langchain import hub
from atlassian import Jira
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough




import socket
import argparse
import pandas as pd
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user, logout_user
from models import db, User,add_user
from flask_dance.contrib.google import make_google_blueprint, google
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit
import base64
from datetime import datetime, timedelta




from typing import Optional
from typing import Dict
from AIAgent import AiAgents  as AiAgents # Ensure this import is correct


nest_asyncio.apply()

# Global variables for bot instance and chat ID
global LLM_AGENT
global LLM_AGENT_ALPHA
global agent
        #vectorstore=add_transcripts_to_vectorstore()
        #agent=initRag(vectorstore)
global gcid, gsecret

LLM_AGENT: Optional[AiAgents] = None  # Initialize agent as None
LLM_AGENT_ALPHA: Optional[AiAgents] = None  # Initialize agent as None
API_KEY = 'AIzaSyDQTCpvB-otclBvsQ6xYgbzrD13zjIjwe0'  # Replace with your actual API key
DB_FILE_PATH = "coinmarketcap_news.db"
YT_DB_FILE_PATH = "youtube_videos.db"
CHATDB_FILE = "chat_prompts.db"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
VECTORSTORE_FILE_PATH = './vector/vector.db'
ACCESSTOKEN_FILE ="atoken.json"
TOKEN_FILE = "token.json"
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/contacts.readonly",
    "openid"
]
GOOG_AUTH_URL="https://storyflix.live/login/google/authorized"
GOOG_AUTH_URL_TEST="http://storyflix.live:5643/login/google/authorized"

ORG="storyflix"
ORG2="alpha"
CHANNEL_ID = 'UCGnflSHJHQNxLqWtl9WlT5g'
MAX_RESULTS = 5  # Number of videos to fetch

app = Flask(__name__)

#Login DB
db_dir = os.path.join(BASE_DIR, 'data')
db_file = os.path.join(db_dir, 'users.db')
os.makedirs(db_dir, exist_ok=True)

app.secret_key = os.urandom(24)  # Replace with a real secret key
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_file}"
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_PASSWORD'] = 'qqqq'  # Store the admin password securely

#socketio = SocketIO(app)
db.init_app(app)

#JIRA init

# JIRA Credentials (Replace with your credentials)
JIRA_URL = "https://nuwa-ai.atlassian.net"
JIRA_USER = "chingrex60@gmail.com"
JIRA_API_TOKEN = os.getenv("JIRA_TOKEN")
JIRA_PROJECT = "KAN"

# Vectorstore location
VECTORSTORE_JIRA_FILE_PATH = "./vector/jira_tickets.db"

# Initialize JIRA API
jira = Jira(
    url=JIRA_URL,
    username=JIRA_USER,
    password=JIRA_API_TOKEN
)

def fetch_jira_tickets():
    """ Fetch JIRA tickets and return as a list of dictionaries """

    JIRA_PROJECT = "KAN"  # Replace with the correct project key

    try:
        jql_query = f'project="{JIRA_PROJECT}" ORDER BY created DESC'
        tickets = jira.jql(jql_query, limit=50)  # Fetch latest 50 tickets

        if "issues" not in tickets:
            return {"error": "Invalid JIRA response. Check project key and permissions."}

        ticket_data = []
        for issue in tickets.get("issues", []):
            ticket_data.append({
                "id": issue["key"],
                "summary": issue["fields"]["summary"],
                "status": issue["fields"]["status"]["name"],
                "created": issue["fields"]["created"],
                "description": issue["fields"].get("description", "No description available"),
            })

        return ticket_data

    except Exception as e:
        return {"error": f"Failed to fetch JIRA tickets: {str(e)}"}

def create_rag_on_jira():
    """ Extract ticket data and store in a vector database for RAG """

    tickets = fetch_jira_tickets()
    documents = []

    for ticket in tickets:
        # Include explicit metadata in embeddings
        content = f"""
        ID: {ticket['id']}
        Summary: {ticket['summary']}
        Status: {ticket['status']}
        Description: {ticket['description']}
        Keywords: {ticket['summary']} {ticket['status']} {ticket['description']}
        Created: {ticket['created']}
        """

        documents.append(Document(content=content, metadata={"id": ticket["id"], "status": ticket["status"]}))

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(documents)

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001"),
        persist_directory=VECTORSTORE_FILE_PATH
    )

    return vectorstore


from google.generativeai import configure, embed_content
# Configure Google Generative AI
configure(api_key=os.getenv("GOOGLE_API_KEY"))  # Ensure API key is set in the environment

class GoogleAIEmbeddings:
    """Wrapper class to make Google Generative AI embeddings compatible with Chroma"""
    
    def embed_query(self, query):
        """Generates an embedding for a single query"""
        response = embed_content(model="models/embedding-001", content=query)
        return response["embedding"] if response else None

    def embed_documents(self, texts):
        """Generates embeddings for a list of documents"""
        return [self.embed_query(text) for text in texts]

def search_jira_rag(query, similarity_threshold=0.7):
    """ Search for relevant JIRA tickets using RAG from ChromaDB with strict keyword filtering """

    # Load vector store
    embeddings = GoogleAIEmbeddings()
    vectorstore = Chroma(persist_directory=VECTORSTORE_FILE_PATH, embedding_function=embeddings)

    # Perform similarity search and get scores
    retrieved_docs_with_scores = vectorstore.similarity_search_with_score(query, k=10)  # Fetch more results to filter

    # Apply similarity threshold **and strict keyword matching**
    relevant_docs = []
    for doc, score in retrieved_docs_with_scores:
        content_lower = doc.page_content.lower()
        query_lower = query.lower()

        # Ensure similarity score is above threshold AND the query is inside the content
        if score >= similarity_threshold or query_lower in content_lower:
            relevant_docs.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })

    print(f"🔍 Searching for: {query}")
    print(f"📌 Retrieved {len(relevant_docs)} relevant documents above threshold {similarity_threshold}")

    if not relevant_docs:
        return {"error": "⚠️ No relevant JIRA tickets found in ChromaDB."}

    return relevant_docs  # Return only filtered results



@app.route('/fetch_jira', methods=['GET'])
def api_fetch_jira():
    tickets = fetch_jira_tickets()
    return jsonify(tickets)

@app.route('/build_jira_rag', methods=['POST'])
def api_build_rag():
    vectorstore = create_rag_on_jira()
    return jsonify({"message": "JIRA RAG database built successfully."})

@app.route('/query_jira', methods=['POST'])
def api_query_jira():
    data = request.json
    query = data.get('query', '')

    if not query:
        return jsonify({"error": "Query parameter is required."}), 400

    response = search_jira_rag(query)  # This now returns a list of dictionaries

    return jsonify({"response": response})  # Now JSON serializable






@app.route('/')
def mainpage():
    # Get the domain from the Host header
    host = request.headers.get('Host')
    global ghost
    ghost=host
    # Check the domain and redirect accordingly
    if host == 'alphaaie.org' or host == 'www.alphaaie.org':
        return redirect(url_for('alpha'))
    else:
        #return render_template('main.html')
        return render_template('demo.html')


# AI Chatbot

#@socketio.on('send_message')
#def handle_send_message(json):
#    global LLM_AGENT
#    message = json['message']
#    response=message
#    print(response)
#    emit('receive_message', {'response': response})


async def initAgent():
    global LLM_AGENT  # Declare agent as global to modify it
    global LLM_AGENT_ALPHA  # Declare agent as global to modify it
    try:
        LLM_AGENT = AiAgents()
        if LLM_AGENT is None :
            raise ValueError("Agent initialization failed!")
        await LLM_AGENT.setup()
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        raise



@app.route('/save_prompt', methods=['POST'])
def save_prompt():
    """ Save user prompt template to SQLite """
    data = request.json
    prompt_text = data.get('prompt', '')

    if not prompt_text.strip():
        return jsonify({"error": "Prompt cannot be empty"}), 400

    conn = sqlite3.connect(CHATDB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO prompts (prompt) VALUES (?)", (prompt_text,))
    conn.commit()
    conn.close()
    restart_ai_loop()

    return jsonify({"message": "Prompt template saved successfully"})

@app.route('/get_prompt', methods=['GET'])
def get_prompt():
    """ Retrieve the latest saved user prompt template from SQLite """
    conn = sqlite3.connect(CHATDB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT prompt FROM prompts ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    return jsonify({"prompt": row[0] if row else ""})

def check_jira_issues(user_message):
    """ Check if the user's issue is a known issue in JIRA using RAG-based retrieval """

    jira_issues = search_jira_rag(user_message)  # Directly call the RAG search function

    if isinstance(jira_issues, dict) and "error" in jira_issues:
        return None  # No relevant JIRA tickets found or an error occurred

    if jira_issues:
        top_issue = jira_issues[0]  # Assuming the first result is the most relevant
        return {
            "id": top_issue.get("metadata", {}).get("id", "Unknown"),
            "status": top_issue.get("metadata", {}).get("status", "Unknown"),
            "description": top_issue.get("content", "No description available")
        }
    print*("No issues queried")
    return None  # No relevant issues found



@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    agent = data.get('agent', 'default')

    global main_ev_loop

    print("Agent Selected:", agent)
    if agent == "alpha":
        llmagent = LLM_AGENT_ALPHA
    else:
        llmagent = LLM_AGENT

    # Check if the message is related to troubleshooting
    if any(keyword in message.lower() for keyword in ["error", "issue", "problem", "not working", "bug", "stuck"]):
        jira_issue = check_jira_issues(message)

        if jira_issue:
            response = {
                "response": f"This issue is being tracked (JIRA Ticket **{jira_issue['id']}**). Status: {jira_issue['status']}. Suggested fix: {jira_issue['description']}."
            }
        else:
            response = {
                "response": "Try restarting your Telly and checking your internet connection. If the issue persists, visit [https://www.telly.com/support](https://www.telly.com/support)."
            }
    else:
        # Process normal chat response
        response = main_ev_loop.run_until_complete(llmagent.chat_with_agent(message))

    print(response)
    return response 
#jsonify(response)


                

def restart_ai_loop():
    """ Stop the current event loop and restart it with `initAgent()` """
    global main_ev_loop

    if main_ev_loop and main_ev_loop.is_running():
        print("Stopping the existing AI event loop...")
        main_ev_loop.stop()

    # Create a new event loop and run `initAgent()`
    print("Restarting AI event loop...")
    main_ev_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(main_ev_loop)
    main_ev_loop.run_until_complete(initAgent())


#####main

if __name__ == '__main__':
         # Argument parsing
        global main_ev_loop
        parser = argparse.ArgumentParser(description='Run the Flask application.')
        args = parser.parse_args()

    #user DB init
        with app.app_context():
            db.create_all()
    #Video DB init

       
        
        #Chat AI Loop
        main_ev_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        main_ev_loop.run_until_complete(initAgent())  # Await the initialization of the agent


        #threading.Thread(target=scheduled_task, daemon=True).start()



        app.run(debug=True, host='0.0.0.0', port=8888)
        
            