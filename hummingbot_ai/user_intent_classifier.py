import enum
from langchain.schema import AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import HumanMessagePromptTemplate, ChatPromptTemplate
from typing import cast,List
import re

from hummingbot_ai.prompt_templates import user_intent_classification_template


class UserIntent(enum.Enum):
    Greeting = 1
    Product = 2
    Subscribe = 3
    Chat = 4
 

def extract_parameters(message: str) -> List[str]:
    # Use regex to find the parameters part
    match = re.search(r'parameters: \[(.*?)\]', message)
    if not match:
        return []

    # Extract the parameters and split them into a list
    params_str = match.group(1)
    params_list = re.findall(r'"(.*?)"', params_str)
    return params_list


def get_user_intent(ai_message: AIMessage) -> UserIntent:
    ai_answer: str = ai_message.content
    print("\nraw ai answers: --> " +ai_answer)
    if "Greeting" in ai_answer:
        intent= UserIntent.Greeting
    elif "product" in ai_answer:
        intent= UserIntent.Product
    elif "subscribe" in ai_answer:
        intent= UserIntent.Subscribe
    else:
        intent= UserIntent.Chat
    
    params = extract_parameters(ai_answer)

    return intent,params,ai_answer


def classify_user_intent_chain(llm: BaseChatModel) -> RunnableSequence:
    return cast(
        RunnableSequence,
        ChatPromptTemplate.from_messages([
            user_intent_classification_template(),
            HumanMessagePromptTemplate.from_template("{message}")]
        ) | llm | get_user_intent
    )
