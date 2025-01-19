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

    # Create document objects properly
    documents = []
    for ticket in tickets:
        content = f"ID: {ticket['id']}\nSummary: {ticket['summary']}\nStatus: {ticket['status']}\nDescription: {ticket['description']}\nCreated: {ticket['created']}"
        documents.append(Document(content=content, metadata={"id": ticket["id"], "status": ticket["status"]}))

    print(documents)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    splits = text_splitter.split_documents(documents)  # Using `split_documents` instead of `split_text`

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

def search_jira_rag(query):
    """ Search for relevant JIRA tickets using RAG from ChromaDB """

    # Load vector store
    embeddings = GoogleAIEmbeddings()
    vectorstore = Chroma(persist_directory=VECTORSTORE_FILE_PATH, embedding_function=embeddings)

    # Set up retriever
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

    # Retrieve documents
    print(f"🔍 Searching for: {query}")
    retrieved_docs = retriever.get_relevant_documents(query)
    print(f"📌 Retrieved {len(retrieved_docs)} documents for query: {query}")

    # Convert Documents to JSON serializable format
    formatted_docs = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in retrieved_docs
    ]

    if not formatted_docs:
        return {"error": "⚠️ No relevant JIRA tickets found in ChromaDB."}

    return formatted_docs  # JSON serializable list of dictionaries

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




db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize Flask-Migrate
migrate = Migrate(app, db)

#user login endpoints
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



# Define a list of blacklisted video IDs
BLACKLISTED_VIDEOS = [
    'd-N3XV-oIz8' # Replace with actual video IDs you want to exclude
]
# Function to get the latest video IDs from the YouTube channel
def get_latest_videos():
    # Construct the YouTube API URL
    url = f'https://www.googleapis.com/youtube/v3/search?key={API_KEY}&channelId={CHANNEL_ID}&part=snippet,id&order=date&maxResults={MAX_RESULTS}'
    response = requests.get(url)
    data = response.json()

    # Extract video IDs and titles from the response
    videos = [
        {
            'videoId': item['id']['videoId'],
            'title': item['snippet']['title']
        }
        for item in data.get('items', [])
        if item['id'].get('videoId') and item['id']['videoId'] not in BLACKLISTED_VIDEOS
    ]

    return videos



# Initialize database
def init_chatdb():
    conn = sqlite3.connect(CHATDB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def init_db():
    conn = sqlite3.connect(YT_DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS youtube_videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            yt_id TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    # Create transcript table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS transcript
                      (yt_id TEXT, start REAL, text TEXT,
                       FOREIGN KEY (yt_id) REFERENCES youtube_videos (yt_id))''')    

    conn.commit()
    conn.close()




def search_videos_by_keyword(query,channel_id=""):
    print("search_videos_by_keyword",query,channel_id)
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'key': API_KEY,
        'channelId': channel_id,
        'maxResults': 20
    }
    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        search_response = response.json()
        videos = [(
                    item['id']['videoId'],         
                    int(time.time())) 
                  for item in search_response['items']]
        save_videos_to_db(videos)
        return search_response['items']
    else:
        print(f"Failed to retrieve videos: {response.status_code}")
        return None

def save_videos_to_db(videos):
    conn = sqlite3.connect(YT_DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS youtube_videos 
                      (yt_id TEXT PRIMARY KEY, timestamp INTEGER)''')

    # Print the existing entries for debugging
    cursor.execute('SELECT yt_id FROM youtube_videos')
    existing_videos = cursor.fetchall()
    existing_yt_ids = set(video[0] for video in existing_videos)
    print("Existing videos in DB:", existing_videos)

    for yt_id, timestamp in videos:
        if yt_id not in existing_yt_ids:
            print(f"Attempting to insert: {yt_id} with timestamp: {timestamp}")
            cursor.execute('INSERT INTO youtube_videos (yt_id, timestamp) VALUES (?, ?)', (yt_id, timestamp))
        #else:
            #print(f"Skipping duplicate: {yt_id}")

    # Print the entries after insertion for debugging
    cursor.execute('SELECT yt_id FROM youtube_videos')
    updated_videos = cursor.fetchall()
    print("Videos in DB after insertion:", updated_videos)

    conn.commit()
    conn.close()




def get_channel_id(username):
    YOUTUBE_API_URL = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': username,
        'type': 'channel',
        'key': API_KEY
    }

    response = requests.get(YOUTUBE_API_URL, params=params, timeout=2)
    if response.status_code == 200:
        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]['snippet']['channelId']
        else:
            print("No channel found")
            return None
    else:
        print(f"Error: {response.status_code}")
        return None


class Document:
    def __init__(self, content, metadata=None):
        self.page_content = content
        self.metadata = metadata if metadata else {}

def add_transcripts_to_vectorstore(db=YT_DB_FILE_PATH, q="SELECT * FROM transcript"):
    conn = sqlite3.connect(db)
    transcripts_df = pd.read_sql_query(q, conn)
    conn.close()
    documents = []
    for index, row in transcripts_df.iterrows():
        yt_id = row['yt_id']
        doc_content = f"Title:'' \nLink: '' \nDate:'' \n Content: {row['text']}"
        documents.append(Document(doc_content))

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    vectorstore = Chroma.from_documents(documents=splits, embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001"), persist_directory=VECTORSTORE_FILE_PATH)
    return vectorstore

def initRag(vectorstore):

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-001")

    retriever = vectorstore.as_retriever()
    prompt = hub.pull("rlm/rag-prompt")
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain


def get_live_video_ids(api_key, channel_id):
    YOUTUBE_API_URL = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'id',
        'channelId': channel_id,
        'eventType': 'live',
        'type': 'video',
        'key': api_key
    }
    response = requests.get(YOUTUBE_API_URL, params=params, timeout=2)
    if response.status_code == 200:
        data = response.json()
        current_timestamp = int(time.time())
        video_ids = [{'yt_id': item['id']['videoId'], 'timestamp': current_timestamp} for item in data['items']]
        print("video ids", video_ids)
        return video_ids
    else:
        print(f"Error: {response.status_code}")
        return None

@app.route('/searchv', methods=['GET'])
def search_videos():
    q = request.args.get('q')
    if not q:
        return jsonify({'error': 'q is required'}), 400
    
    video_ids = search_videos_by_keyword(q)
    if video_ids:
        return jsonify(video_ids)
    else:
        return jsonify({'error': 'Unable to fetch videos'}), 500


def get_videos_from_db():
    conn = sqlite3.connect(YT_DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT yt_id, timestamp FROM youtube_videos ORDER BY timestamp DESC')
    videos = cursor.fetchall()
    conn.close()
    return [{'yt_id': video[0], 'timestamp': video[1]} for video in videos]

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript
    except Exception as e:
        print(f"Error retrieving transcript: {e}")
        return None

def search_transcript(transcript, keyword):
    results = []
    for entry in transcript:
        if keyword.lower() in entry['text'].lower():
            results.append(entry)
    return results


def fetch_videos():
    try:
        response = get_yt_videos() #requests.get('getYTVideo',timeout=1)
        if response.status_code == 200:
            videos = response.json()
            save_videos_to_db([(video['yt_id'], video['timestamp']) for video in videos])
            return videos
        else:
            return get_videos_from_db()
    except requests.RequestException:
        return get_videos_from_db()

def validate_image_url(url):
    try:
        response = requests.head(url, timeout=5)
        if response.status_code == 200 and 'image' in response.headers['Content-Type']:
            return True
    except requests.RequestException as e:
        print(f"Error validating image URL {url}: {e}")
    return False

def format_detail_text(detail):
    if detail is None:
        detail =""
    paragraphs = detail.split('\n')
    formatted_detail = ''.join([f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()])
    return formatted_detail


def save_transcript_to_db(yt_id, transcript):
    conn = sqlite3.connect(YT_DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS transcript
                      (yt_id TEXT, start REAL, text TEXT,
                       PRIMARY KEY (yt_id, start),
                       FOREIGN KEY (yt_id) REFERENCES youtube_videos (yt_id))''')

    # Fetch existing transcript entries for this yt_id
    cursor.execute('SELECT yt_id, start FROM transcript WHERE yt_id = ?', (yt_id,))
    existing_entries = cursor.fetchall()
    existing_entries_set = {(entry[0], entry[1]) for entry in existing_entries}

    for entry in transcript:
        start = entry['start']
        text = entry['text']
        if (yt_id, start) not in existing_entries_set:
            cursor.execute('''INSERT INTO transcript (yt_id, start, text)
                              VALUES (?, ?, ?)''', (yt_id, start, text))
        #else:
         #   print(f"Skipping duplicate transcript entry for yt_id: {yt_id}, start: {start}")

    conn.commit()
    conn.close()



def merge_transcript_segments(transcript, max_gap=1.0):
    """
    Merges transcript segments into longer sentences based on the time gap between segments.
    :param transcript: List of transcript segments
    :param max_gap: Maximum allowed time gap between segments to be merged
    :return: Merged list of transcript segments
    """
    merged_transcript = []
    current_segment = None

    for entry in transcript:
        start = entry['start']
        text = entry['text']

        if current_segment is None:
            current_segment = {'start': start, 'text': text}
        else:
            # Calculate the gap between the current segment and the new entry
            gap = start - (current_segment['start'] + len(current_segment['text']) / 15.0)  # Approximate reading speed: 15 chars/sec
            if gap <= max_gap:
                current_segment['text'] += ' ' + text
            else:
                merged_transcript.append(current_segment)
                current_segment = {'start': start, 'text': text}

    if current_segment is not None:
        merged_transcript.append(current_segment)

    return merged_transcript


def clear_transcript_table():
    conn = sqlite3.connect(YT_DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transcript')
    conn.commit()
    conn.close()

def clear_videos_table():
    conn = sqlite3.connect(YT_DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM youtube_videos')
    conn.commit()
    conn.close()

def generate_nonce():
    return base64.b64encode(os.urandom(16)).decode('utf-8')

################################
##    API endpoints
################################


@app.route('/getYTVideo', methods=['GET'])
def get_yt_videos():
    videos = get_videos_from_db()
    return jsonify(videos)


@app.route('/setYTVideo', methods=['POST', 'DELETE'])
def set_yt_video():
    conn = sqlite3.connect(YT_DB_FILE_PATH)
    cursor = conn.cursor()
    yt_id = request.args.get('yt_id')
    
    if request.method == 'POST':
        timestamp = request.args.get('timestamp', 'N/A')
        cursor.execute('INSERT INTO youtube_videos (yt_id, timestamp) VALUES (?, ?)', (yt_id, 0))
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM youtube_videos WHERE yt_id = ?', (yt_id,))

    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


@app.route('/news')
def get_news():
    limit = request.args.get('limit', default=5, type=int)
    offset = request.args.get('offset', default=0, type=int)

    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, link, author, content, detail, date, image_url FROM news ORDER BY date ASC LIMIT ? OFFSET ?", (limit, offset))
    
    news = cursor.fetchall()

    validated_news_items = []
    for item in news:
        title, link, content, author, date, detail, image_url = item
        formatted_detail = format_detail_text(detail)
        if not validate_image_url(image_url):
            image_url = ''
        validated_news_items.append((title, link, content, author, date, formatted_detail, image_url))

    conn.close()

    return jsonify(validated_news_items)


@app.route('/alpha')
def alpha():
    return render_template('alpha.html')

@app.route('/alpha_investor')
def alpha_investor():
    return render_template('alpha_investor.html')

@app.route('/ainews')
def ainews():
    return render_template('alpha_ainews.html')


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



@app.route('/appterms')
def aps():
    return render_template('serviceterms.html')
@app.route('/privacy')
def p():
    return render_template('privacy.html')
@app.route('/investor')
def investor():
    return render_template('investor.html')

@login_required
@app.route('/landing')
def landing():
    return render_template('landing.html')


@app.route('/alpha_landing')
def alanding():
    return render_template('alpha_landing.html')

@app.route('/creator')
def ct():
    return render_template('creator.html')

@app.route('/m1')
def index():
    show_checkbox = is_running_on_localhost()
    return render_template('index.html', show_checkbox=show_checkbox)

@app.route('/detail')
def detail():
    title = request.args.get('title')
    conn = sqlite3.connect(DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT detail FROM news WHERE title = ?", (title,))
    detail = cursor.fetchone()
    conn.close()
    return render_template('detail.html', title=title, detail=detail[0])

@app.route('/get_videos')
def get_videos():
    videos = fetch_videos()
    return jsonify(videos)



@app.route('/updateVideoMeta', methods=['GET'])
def update_video_meta():
    videos = get_videos_from_db()
    for video in videos:
        yt_id = video['yt_id']
        try:
            transcript = YouTubeTranscriptApi.get_transcript(yt_id)
            mtranscript = merge_transcript_segments(transcript,1)
            #print(mtranscript)
            save_transcript_to_db(yt_id, mtranscript)
        except Exception as e:
            print(f"An error occurred for video {yt_id}: {e}")

    return jsonify({"status": "updated"})

@app.route('/dumpTranscript', methods=['GET'])
def dump_transcript():
    conn = sqlite3.connect(YT_DB_FILE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transcript")
    transcripts = cursor.fetchall()
    conn.close()
    return jsonify(transcripts)


@app.route('/cleart', methods=['DELETE'])
def cleart():
    clear_transcript_table()
    return jsonify({"status": "transcripts cleared"})

@app.route('/clearv', methods=['DELETE'])
def clearv():
    clear_videos_table()
    return jsonify({"status": "videos cleared"})


@app.route('/searchfragment', methods=['POST'])
def search_fragment():
    keyword = request.form.get('keyword')
    keyword_list = [k.strip() for k in keyword.split(',') if k.strip()]

    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400

    #search_videos_by_keyword(keyword)
    conn = sqlite3.connect(YT_DB_FILE_PATH)
    cursor = conn.cursor()
    query = "SELECT yt_id, start, text FROM transcript WHERE " + " AND ".join(["text LIKE ?"] * len(keyword_list))
    params = ['%' + keyword + '%' for keyword in keyword_list]
    cursor.execute(query, params)
    matches = cursor.fetchall()
    conn.close()

    results = []
    for match in matches:
        yt_id, start, text = match
        link = f"https://www.youtube.com/watch?v={yt_id}&t={int(start)}s"
        results.append(link)

    return jsonify(results)

# Add the askRag endpoint
@app.route('/askRag', methods=['POST'])
def ask_rag():
    global agent
    usermsg = request.form.get('msg')
    if not usermsg:
        return jsonify({"error": "Missing usermsg"}), 400
    
    try:
        result = agent.invoke(usermsg)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Function to check if the server is running on localhost
def is_running_on_localhost():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(hostname,local_ip)
    return local_ip.startswith("127.") or local_ip == "localhost"

def scheduled_task():
    with app.app_context():
        while True:
            if os.path.isfile('/tmp/pollnews'):
                videos=search_videos_by_keyword("cryptonews")
            response=update_video_meta()
            time.sleep(24*3600)  # Sleep for 1 hour


def get_video_statistics(video_ids):
    """
    Get statistics for a list of video IDs.
    :param video_ids: A list of video IDs.
    :return: A dictionary mapping video IDs to their view counts.
    """
    ids = ','.join(video_ids)
    url = f'https://www.googleapis.com/youtube/v3/videos?key={API_KEY}&id={ids}&part=statistics'
    response = requests.get(url)
    data = response.json()

    video_stats = {
        item['id']: int(item['statistics'].get('viewCount', 0))
        for item in data.get('items', [])
    }
    return video_stats

def get_latest_popular_videos(query):
    """
    Fetch the latest videos related to a query and sort them by popularity.
    :param query: The search query (e.g., #ainews).
    :return: A list of videos with title and videoId, sorted by date and view count.
    """
    # Step 1: Search for the latest videos
    url = f'https://www.googleapis.com/youtube/v3/search?key={API_KEY}&q={query}&part=snippet&type=video&order=date&maxResults={MAX_RESULTS}'
    response = requests.get(url)
    data = response.json()

    # Extract video IDs, titles, and publish dates from the response
    videos = [
        {
            'videoId': item['id']['videoId'],
            'title': item['snippet']['title'],
            'publishedAt': item['snippet']['publishedAt']
        }
        for item in data.get('items', [])
        if item['id'].get('videoId')
    ]

    # Step 2: Get view counts for the videos
    video_ids = [video['videoId'] for video in videos]
    video_stats = get_video_statistics(video_ids)

    # Add view count to each video entry
    for video in videos:
        video['viewCount'] = video_stats.get(video['videoId'], 0)

    # Step 3: Sort videos first by published date and then by view count
    videos.sort(key=lambda x: (x['publishedAt'], x['viewCount']), reverse=True)

    # Return only title and videoId in the expected format
    return [{'title': video['title'], 'videoId': video['videoId']} for video in videos]

def get_trending_keywords():
    """
    Fetch trending search queries using Google Trends.
    :return: A list of trending search queries.
    """
    pytrends = TrendReq()
    # Get trending searches
    trending_searches = pytrends.trending_searches(pn='united_states')  # You can change the location as needed
    # Extract the top trending keywords
    trending_keywords = trending_searches[0].tolist()  # Get the top trend as a list of strings
    return trending_keywords


####Google SSO
@app.route('/google_login')
def google_login():
    global ghost
    if not google.authorized:
        #return redirect(url_for('google.login'))
        return google_login_m()
    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    info = resp.json()
    user = User.query.filter_by(email=info["email"]).first()
    if user:
        
        if ghost == 'alphaaie.org' or host == 'www.alphaaie.org':
            return redirect(url_for('alpha_landing'))
        else:
            return redirect(url_for('landing'))
    else:
        #return redirect(url_for('register', email=info["email"], name=info["name"]))
        return redirect(url_for('/', email=info["email"], name=info["name"]))


def google_login_m():
    token_request_uri = "https://accounts.google.com/o/oauth2/auth"
    response_type = "code"
    client_id = gcid
    redirect_uri = GOOG_AUTH_URL
    scope = "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email"
    url = "{token_request_uri}?response_type={response_type}&client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}".format(
        token_request_uri = token_request_uri,
        response_type = response_type,
        client_id = client_id,
        redirect_uri = redirect_uri,
        scope = scope)
    return redirect(url)



@app.route('/login/google/authorized', methods=['GET', 'POST'])
def googlelogin():
    global authorization_code
    if not google.authorized:
        error_description = request.args.get('error_description')
        error = request.args.get('error')
        print("error!")

    authorization_code = request.args.get('code')
    print("auth code------> ",authorization_code)
    

    if os.path.exists(ACCESSTOKEN_FILE):
        with open(ACCESSTOKEN_FILE, 'r') as token_file:
            cred = json.load(token_file)
            token=cred["access_token"]
    else:
        cred = get_access_token(request.args.get("code"),GOOG_AUTH_URL)
        token=cred['access_token']
        print("got access token------",token)
        #with open(ACCESSTOKEN_FILE, 'w') as token_file:
        #    token_file.write(json.dumps(cred))
    xresp = 0
    if token:
        xresp = get_user_profile(token)

    if xresp and xresp.ok:
        resp = xresp.json()
        email = resp["emailAddresses"][0]["value"] if resp["emailAddresses"] else None
        display_name = resp["names"][0]["displayName"] if resp["names"] else None
        print("resp----", resp)
        user = User.query.filter_by(email=email).first()
        if user:
            #login_user(user)
            return redirect(url_for('landing'))
        else:
            return redirect(url_for('register', email=email, name=display_name))
    else:
        flash('Failed to authenticate with Google.')
        return render_template('main.html')





@app.route('/register_alpha', methods=['GET', 'POST'])
def aregister():
    if request.method == 'POST':
        name = request.form.get('name')
        org = request.form.get('org')
        email = request.form.get('email')
        phone = request.form.get('phone')
        company = request.form.get('company')
        pre_signup = request.form.get('pre_signup')
        interest = request.form.get('interest')
        message = request.form.get('message')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists.')
            print('Email address already exists.')
            #return redirect(url_for('alpha_landing'))
            return alanding()
        
        add_user(name, email, phone, company, pre_signup, interest, message,org)
        return alanding()
    else:
        email = request.args.get('email', '')
        name = request.args.get('name', '')
        return render_template('alpha_investor.html', default_email=email, default_name=name)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        org = request.form.get('org')
        email = request.form.get('email')
        phone = request.form.get('phone')
        company = request.form.get('company')
        pre_signup = request.form.get('pre_signup')
        interest = request.form.get('interest')
        message = request.form.get('message')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists.')
            print('Email address already exists.')
            return redirect(url_for('landing'))

        add_user(name, email, phone, company, pre_signup, interest, message,org)
        return redirect(url_for('landing'))
    else:
        email = request.args.get('email', '')
        name = request.args.get('name', '')
        return render_template('investor.html', default_email=email, default_name=name)

@app.route('/delete_users', methods=['POST'])
def delete_users():
    if not session.get('logged_in') :
        return redirect(url_for('login'))
    
    user_ids = request.form.getlist('ids')
    if user_ids:
        users_to_delete = User.query.filter(User.ids.in_(user_ids)).all()
        for user in users_to_delete:
            db.session.delete(user)
        db.session.commit()
        flash(f'Deleted {len(users_to_delete)} users.')

    return redirect(url_for('admin'))

@app.route('/update_users', methods=['POST'])
def update_users():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    user_ids = request.form.getlist('ids')
    if user_ids:
        # This is just an example, you can add more update logic here
        users_to_update = User.query.filter(User.ids.in_(user_ids)).all()
        for user in users_to_update:
            user.interest = 'Updated Interest'  # Example update
        db.session.commit()
        flash(f'Updated {len(users_to_update)} users.')

    return redirect(url_for('admin'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = User.query.filter_by(email=username).first()
        if email and password == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            session['email'] = username
            return redirect(url_for('admin'))
        else:
            flash('Incorrect username or password.')
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in') or session.get('email') != 'chingrex60@gmail.com':
        return redirect(url_for('login'))
    users = User.query.all()
    print(users)
    return render_template('admin.html', users=users)


@app.route('/logout')
def logout():
    token = google.token["access_token"]
    resp = requests.post(
        'https://accounts.google.com/o/oauth2/revoke',
        params={'token': token},
        headers={'content-type': 'application/x-www-form-urlencoded'}
    )
    if resp.status_code == 200:
        del google.token  # Delete the token from the session
        logout_user()  # Log out the user from Flask-Login
        flash('You have been logged out.', 'success')
    else:
        flash('Failed to revoke token.', 'danger')  

    session.pop('logged_in', None)
    session.pop('username', None)
    return render_template('main.html')




def get_user_profile(access_token):
    url = "https://people.googleapis.com/v1/people/me"
    params = {'personFields': 'names,emailAddresses'}
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers, params=params)
    if response.ok:
        print("User Profile response:", response.json())
    else:
        print("Failed to fetch user profile:", response.text)
    return response

def get_access_token(code,rurl):
    url = "https://oauth2.googleapis.com/token"
    payload = {
        'code': code,
        'client_id': gcid,
        'client_secret': gsecret,
        'redirect_uri': rurl,
        'grant_type': 'authorization_code'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, data=payload, headers=headers)
    if response.ok:
        #return response.json()['access_token']
        return response.json()
    else:
        return None


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
    """ Check if the user's issue is a known issue in the JIRA database. """

    # Load vectorstore and explicitly specify the embedding model
    vectorstore = Chroma(
        persist_directory=VECTORSTORE_FILE_PATH, 
        embedding_function=GoogleGenerativeAIEmbeddings(model="models/embedding-001")  # Ensure embeddings are provided
    )

    # Use retriever with embeddings
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    query = f"Find known issues related to: {user_message}"
    response = retriever.invoke(query)  # Use invoke instead of deprecated method

    if response:
        issue = response[0].page_content  # Extract relevant JIRA issue
        return {"id": "JIRA-XXX", "status": "Open", "description": issue}  # Example response
    else:
        return None  # No matching JIRA ticket found



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

    return jsonify(response)



def save_trendingvideos_to_db(videos, trending_keyword):
    """
    Save the videos to the SQLite database.
    :param videos: List of videos to save.
    :param trending_keyword: The keyword used for fetching videos.
    """
    with sqlite3.connect(YT_DB_FILE_PATH) as conn:
        cursor = conn.cursor()
        create_trendingtable()

        # Create the table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trendingnews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                videoId TEXT UNIQUE,
                title TEXT,
                trendingKeyword TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert videos into the table
        for video in videos:
            cursor.execute('''
                INSERT OR REPLACE INTO trendingnews (videoId, title, trendingKeyword)
                VALUES (?, ?, ?)
            ''', (video['videoId'], video['title'], trending_keyword))
        
        conn.commit()

def create_trendingtable():
    """
    Create the SQLite database and table if they don't exist.
    """
    with sqlite3.connect(YT_DB_FILE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trendingnews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                videoId TEXT UNIQUE,
                title TEXT,
                trendingKeyword TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


def fetch_trendingvideos_from_db():
    """
    Fetch videos from the database if they are less than 24 hours old.
    :return: List of videos or None if data is outdated.
    """
    with sqlite3.connect(YT_DB_FILE_PATH) as conn:
        cursor = conn.cursor()

        # Check if the table exists and fetch data
        cursor.execute('''
            SELECT videoId, title, trendingKeyword, timestamp FROM trendingnews
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()

        # If there's no data or it's older than 24 hours, return None
        if row is None or datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S') < datetime.now() - timedelta(hours=24):
            return None

        # Fetch all videos
        cursor.execute('''
            SELECT videoId, title FROM trendingnews
        ''')
        rows = cursor.fetchall()

        # Return the videos
        return [{'videoId': r[0], 'title': r[1]} for r in rows]


@app.route('/api/getchannel', methods=['GET'])
def get_channel():
    try:
        # Check if we can use cached data
        create_trendingtable()
        cached_videos = fetch_trendingvideos_from_db()
        if cached_videos is not None:
            print("Using cached data")
            latest_videos = get_latest_videos()
            return jsonify({'videoIds': latest_videos + cached_videos})

        # If cache is not usable, fetch fresh data
        trending_keywords = get_trending_keywords()
        if trending_keywords:
            top_trend = trending_keywords[0]
            videos = get_latest_popular_videos(top_trend)
            latest_videos = get_latest_videos()

            # Save videos to the database
            save_trendingvideos_to_db(videos, top_trend)
            save_trendingvideos_to_db(latest_videos,"ainews")

            return jsonify({'videoIds': latest_videos + videos})
        else:
            return jsonify({'videoIds': [], 'trendingKeyword': 'No trending keywords found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/getchannelold', methods=['GET'])
def get_channelold():
    try:
        video_ids = get_latest_videos()
        return jsonify({'videoIds': video_ids})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
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
        parser.add_argument('--prod', action='store_true', help='Run the server in production mode')
        parser.add_argument('--alpha', action='store_true', help='Run for alpha main or not')
        args = parser.parse_args()

    #user DB init
        with app.app_context():
            db.create_all()
    #Video DB init
        init_db()
        init_chatdb()

       
        
        #Chat AI Loop
        main_ev_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        main_ev_loop.run_until_complete(initAgent())  # Await the initialization of the agent


        threading.Thread(target=scheduled_task, daemon=True).start()



        if args.prod:
            # Production mode settings
            app.run(debug=False, host='0.0.0.0', port=5643)
        else:
            # Development mode settings
            app.run(debug=True, host='0.0.0.0', port=8888)
            #app.run(ssl_context=('cert.pem', 'key.pem') ,debug=True,host='0.0.0.0', port=8888)

            