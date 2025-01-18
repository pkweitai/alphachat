from langchain import hub
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from CustomLoader import LocalDocumentLoader
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
import os
import pickle
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from threading import Thread



VECTORSTORE_FILE_PATH = './vector/vector.db'
DATABASE_PATH = "./databases"

class Watcher(Thread):
      def __init__(self, directory=DATABASE_PATH,debounce_time=10.0):
        Thread.__init__(self)
        self.directory = directory
        self.debounce_time = debounce_time
        self.last_modified = {}   

      def run(self):
        class Handler(FileSystemEventHandler):
            @staticmethod
            def on_any_event(event):
                current_time = time.time()
                last_event_time = self.last_modified.get(event.src_path, 0)
   
                if (current_time - last_event_time) > self.debounce_time:
                    if not event.is_directory and not event.src_path.endswith('.DS_Store'):
                         print(f"Event type: {event.event_type} - Path: {event.src_path}")
                         reloadVector()
                         self.last_modified[event.src_path] = current_time

        event_handler = Handler()
        observer = Observer()
        observer.schedule(event_handler, self.directory, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        finally:
            observer.stop()
            observer.join()

def save_vectorstore_to_file(vectorstore):
    filename=VECTORSTORE_FILE_PATH
    with open(filename, 'wb') as file:
        pickle.dump(vectorstore, file)
    print(f"Vectorstore saved to {filename}")

def load_vectorstore_from_file():
    # Initialize Chroma with the persistence directory
    
    # Initialize the embedding function, e.g., using OpenAI's API
    embedding_function = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Set the embedding function to the vectorstore
    # vectorstore.set_embedding_function(embedding_function.embed_text)
    vectorstore = Chroma(persist_directory=VECTORSTORE_FILE_PATH , embedding_function=embedding_function)

    
    print("Vectorstore loaded and embedding function set.")
    return vectorstore

def reloadVector():
    loader = LocalDocumentLoader(DATABASE_PATH ,enable_debug=True)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings(), persist_directory=VECTORSTORE_FILE_PATH)
    return vectorstore
    #save_vectorstore_to_file(vectorstore,)





# Function to add new documents to the vectorstore
def add_documents_to_vectorstore(document_loader_path,enable_debug=True):
    new_loader = LocalDocumentLoader(document_loader_path, enable_debug=True)
    new_docs = new_loader.load()
    print(new_docs)
    new_splits = text_splitter.split_documents(new_docs)
    # Assuming Chroma has a method `add_documents`
    vectorstore.add_documents(documents=new_splits)


# cleanup
def cleanup():
    vectorstore.delete_collection()


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


'''LLM'''
os.environ["OPENAI_API_KEY"] = "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"
llm = ChatOpenAI(model="gpt-3.5-turbo-0125")

'''init RAG settings'''
if os.path.exists(VECTORSTORE_FILE_PATH):
    vectorstore = load_vectorstore_from_file()
    #if vectorstore is None:
    print(" Existing vectorstore initialized. ")
else:
    print("No existing vectorstore file found. Initializing a new one.")
    vectorstore=reloadVector()

# Retrieve and generate using the relevant snippets of the blog.
retriever = vectorstore.as_retriever()
prompt = hub.pull("rlm/rag-prompt")
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# monitor_folder()



