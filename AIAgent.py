
import inspect
from langchain_core.runnables import RunnableSequence
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI


from typing import Dict, List, Callable
from hummingbot_ai.user_intent_classifier import classify_user_intent_chain, UserIntent
from hummingbot_ai.user_generalchat import response_user_generalchat

class AiAgents:
    async def setup(self) -> None:
        #if cmdline_args.ollama:
        #    llm = ChatOllama(model="llama3:70b")
        #elif cmdline_args.google:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite")
        #else:
        #    llm = ChatOpenAI(temperature=0.0)

        self.llm = llm
        self.chain: RunnableSequence[Dict, UserIntent] = classify_user_intent_chain(llm)
        self.chatchain : RunnableSequence[Dict, str] = response_user_generalchat(llm) 
        self.user_input = f""


    async def dispatch(self,intent: UserIntent, params: List[str],user_input):
        function=self.function_table[intent]
        if intent in self.function_table:
            if inspect.iscoroutinefunction(function):
                status= await function(self,params)
            else:
                status=function(self,params)
        else:
            print(f"No handler found" )
        
        print("status", type(status))

        if isinstance(status, str):
            print("dispatch str: " , status)
            #res=f"make a human friendly message for 'based on user input :{user_input}, the detected intent: {intent} , and hummingbot result:  {status}, repeat all parameters precisely, no need ask question to confirm. Do not repeat the intent, classification and user questions. Make simple response \n'"
            #humanreadables : str = await self.chatchain.ainvoke({"message": res})
            humanreadables : str = status
            return humanreadables
        
        elif isinstance(status, dict):
            return status
            #return status.get('html', 'No HTML content provided')



    async def handle_chat(self,params: List[str] = None) -> str:
        keyword="keyword=others, interpret the question and provide a friendly answer, goal is to engage new users for interests and sign up"
        botAnswers: str = await self.chatchain.ainvoke({"message": keyword+self.user_input})
        return botAnswers
    
    async def handle_subscribe(self,params: List[str] = None) -> str:
        keyword="keyword=subscribe, interpret the question and provide a friendly answer, goal is to engage new users for interests and sign up"
        botAnswers: str = await self.chatchain.ainvoke({"message": keyword+self.user_input})
        return botAnswers

    async def handle_product(self,params: List[str] = None) -> str:
        keyword="keyword=product, interpret the question and provide a friendly answer, goal is to engage new users for interests and sign up"
        botAnswers: str = await self.chatchain.ainvoke({"message": keyword+self.user_input})
        return botAnswers

    async def handle_greeting(self,params: List[str] = None) -> str:
        keyword="keyword=greetings, interpret the question and provide a friendly answer, goal is to engage new users for interests and sign up"
        botAnswers: str = await self.chatchain.ainvoke({"message": keyword+self.user_input})
        return botAnswers


    async def chat_with_agent(self, user_input):
            classification: UserIntent
            parameters: List[str]
            aianswers : str
            self.user_input=user_input
            classification, parameters ,aianswers = await self.chain.ainvoke({"message": user_input})
            results = f"  Intent : {classification}\n"
            results += f" param :  {parameters}\n"
            print(results)
            
            #botAnswers: str = await self.chatchain.ainvoke({"message": user_input})
            botAnswers: str = await self.dispatch(classification,parameters,user_input)
            #botAnswers +=aianswers
            print(botAnswers)
            print(aianswers)
            
            return {"msg": botAnswers, "status": 1}
    

    function_table: Dict[UserIntent, Callable[[List[str]], None]] = {
        UserIntent.Chat: handle_chat,
        UserIntent.Subscribe: handle_subscribe,
        UserIntent.Greeting: handle_greeting,
        UserIntent.Product: handle_product,
    }

