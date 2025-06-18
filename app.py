from flask import Flask, render_template, request, redirect, url_for, jsonify
import asyncio
import nest_asyncio
import sqlite3
import os


import argparse
from models import db,add_user
from typing import Optional
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
        
            