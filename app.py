from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from pkl_file import load_from_file
from langchain.document_loaders import DirectoryLoader,AmazonTextractPDFLoader
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers import ParentDocumentRetriever
from langchain.chains import ConversationalRetrievalChain
from langchain.callbacks.openai_info import OpenAICallbackHandler
from langchain.callbacks import get_openai_callback
from prompt import prompt_template, guidelines_template
from langchain.schema.runnable.config import RunnableConfig
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.document_loaders import TextLoader,PyPDFLoader

import os
os.environ["LANGCHAIN_API_KEY"] = "ls__fc0449a57dd74dae99130bd4f90d0005"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Business Chatbot2"

from langsmith import Client
client = Client()
from data_access import DataAccess
data_access= DataAccess()
key = "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"
llm_name = 'gpt-3.5-turbo-1106'

def chroma_setup():
    embeddings = OpenAIEmbeddings(api_key=key)
    vectorstore = Chroma( collection_name="user_stories",persist_directory="chroma/", embedding_function=embeddings)
    return vectorstore
def retriver_setup(vectorstore):
    
    file_path = 'ids_docs_new.pkl'
    ids_docs = load_from_file(file_path)
    store = InMemoryStore()
    store.mset(ids_docs)

    child_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
    parent_splitter = RecursiveCharacterTextSplitter(chunk_size=5000)
    retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
        search_kwargs = {"k": 5}
    )
    return retriever

def chain_setup(model_name, retriever):
    openai_llm = ChatOpenAI(model_name=model_name, temperature=0.1,callbacks=[OpenAICallbackHandler()])

    mq_retriver =  MultiQueryRetriever.from_llm(
            llm=ChatOpenAI(model_name=llm_name, temperature=0),
            retriever=retriever
        )
    qa = ConversationalRetrievalChain.from_llm(
    llm=openai_llm,
    chain_type="stuff",
    retriever=mq_retriver,
    condense_question_prompt=prompt_template(),
    return_source_documents=True,
    return_generated_question=True,
    combine_docs_chain_kwargs={"prompt": guidelines_template()},
    verbose = True
    )
    return qa





loader = DirectoryLoader(
    "guidelines",
    "**/[!.]*",
    {
        ".pdf": lambda path: AmazonTextractPDFLoader(path),
        "recursive": True
    }
    )
guidelines = loader.load()

def out_db_retriever(docs):
    output_string = ""
    for i in range(len(docs)):
        source_info = docs[i].metadata.get('source', 'N/A')
    
        # Concatenate the source information to the output string
        output_string += f"Document {i+1}:\n Source: {source_info}\n"
    return output_string

import chainlit as cl
from typing import Optional

@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
  # Fetch the user matching username from your database
  # and compare the hashed password with the value stored in the database
  user = data_access.login_user(username,password)
  if user:
    return cl.User(identifier=user.userName, metadata={"role": "admin", "provider": "credentials"})
  else:
    return None

@cl.on_chat_start
async def on_chat_start():
    app_user = cl.user_session.get("user")
    serial = cl.user_session.get("id")
    sId = data_access.add_new_session(serial,app_user.identifier)
    model_name = "gpt-3.5-turbo-1106"
    chroma = chroma_setup()
    retriever = retriver_setup(chroma)
    chain = chain_setup(model_name,retriever)
    chat_history = [('', '')]
    cl.user_session.set("chroma", chroma)
    cl.user_session.set("retriever", retriever)
    cl.user_session.set("chain", chain)
    cl.user_session.set("chat_history", chat_history)
    cl.user_session.set("sId", sId)



@cl.on_message
async def on_message(message: cl.Message):
    if message.elements:
        retriever = cl.user_session.get("retriever")         
        if message.elements:
            docs = []
            sId = cl.user_session.get("sId")
            # Processing images exclusively
            for file in message.elements:
                if file.mime == "text/plain":
                    loader = TextLoader(file_path=file.path)
                    documents = loader.load()
                    print(documents)
                    docs.extend(documents) 

                elif file.mime == "application/pdf":
                    loader = PyPDFLoader(file_path=file.path)
                    documents = loader.load()
                    print(documents)
                    docs.extend(documents)
            
            if(len(docs) > 0):
                ids = []
                for i, doc in enumerate(docs):
                    ids.append(f'temp_file_{i}_{sId}')
                cl.user_session.set("docs_ids", ids)
                retriever.add_documents(docs,ids=ids)
    app_user = cl.user_session.get("user")
    check_balance = data_access.check_user_balance(app_user.identifier)
    if(check_balance):
        chain = cl.user_session.get("chain") 
        sId = cl.user_session.get("sId")

        chat_history= cl.user_session.get("chat_history")
        with get_openai_callback() as cb:
            res = await chain.ainvoke(
            input = {"question": message.content, "chat_history": chat_history, "guidelines": guidelines},
                config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()],metadata= {"username": app_user.identifier, "session_id":sId})
            )
            answer = res["answer"]
            db_response = res["source_documents"]
            text_elements = []  

            for i in range(len(db_response)):
                source_info = db_response[i].metadata.get('source', 'N/A')
                text_elements.append(
                cl.Text(content=f"""```text {db_response[i].page_content} 
                        """, name=source_info)
            )
            chat_history.extend([(message.content, answer)])
            docs = out_db_retriever(db_response)
            response = answer + '\n\n' + docs
            await cl.Message(content=response,elements=text_elements).send()  
            cost = cb.total_cost
            print(f"Total Cost (USD): ${cost}")
            message_id = data_access.add_new_message(
            question=message.content,
            answer=answer,
            resources=docs,
            cost= float(cost),
            session_id=sId
            )
            data_access.increment_user_usage(app_user.identifier,cost)
        res = await cl.AskActionMessage(
        content="Do you want to write feedback on this answer?",
        actions=[
            cl.Action(name="feedback", value="feedback", label="✉️ Send feedback"),
            cl.Action(name="No", value="No", label="No")
        ]
        ).send()
        if res and res.get("value") == "feedback":
            feedback = await cl.AskUserMessage(content="Write your feedback in the message field").send()     
            if feedback:
                data_access.add_feedback(description=feedback['output'],message_id=message_id)
                await cl.Message(
                    content=f"Thank you for your feedback: \n {feedback['output']}",
                ).send()
    else:
        await cl.Message(content="").send() 
        res = await cl.AskActionMessage(
            content="You have exceeded the limit, Contact with R&D or request new quota",
            actions=[
                cl.Action(name="request", value="request", label="✉️ Send Request"),
            ],
        ).send()
        if res and res.get("value") == "request":
            result = data_access.request_quota(app_user.identifier)
            await cl.Message(
                content=result,
            ).send()


@cl.on_chat_end
def end():
    doc_id = cl.user_session.get("docs_ids")
    if doc_id:
        chroma = cl.user_session.get("chroma")    
        for id in doc_id:
            out = chroma.get(where={"doc_id": id})
            chroma.delete(out["ids"])
            print(f"Document '{id}' has been deleted")
    sId = cl.user_session.get("sId")
    data_access.set_total_cost(sId)
    data_access.end_session(sId)

