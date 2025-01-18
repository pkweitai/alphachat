import enum
from langchain.schema import AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import HumanMessagePromptTemplate, ChatPromptTemplate
from typing import cast
import sqlite3

from hummingbot_ai.prompt_templates import user_general_chat_template,user_alpha_chat_template


DB_FILE = "chat_prompts.db"
def load_user_general_chat_template():
    """Fetch the latest saved chat prompt from the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT prompt FROM prompts ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "Default fallback prompt template"



def get_response(ai_message: AIMessage) -> str:
    ai_answer: str = ai_message.content
    return ai_answer 


def response_user_generalchat(llm: BaseChatModel) -> RunnableSequence:
    return cast(
        RunnableSequence,
        ChatPromptTemplate.from_messages([
            load_user_general_chat_template(),
            HumanMessagePromptTemplate.from_template("{message}")]
        ) | llm | get_response
    )

def response_user_alphachat(llm: BaseChatModel) -> RunnableSequence:
    return cast(
        RunnableSequence,
        ChatPromptTemplate.from_messages([
            user_alpha_chat_template(),
            HumanMessagePromptTemplate.from_template("{message}")]
        ) | llm | get_response
    )
