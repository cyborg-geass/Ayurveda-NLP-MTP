import os
from typing import TypedDict, Dict, List, Annotated
from langchain_core.messages import HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
import operator
from operator import itemgetter
import numpy as np
import warnings
warnings.filterwarnings("ignore")

os.environ["GROQ_API_KEY"] = "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"
os.environ["TAVILY_API_KEY"] = "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"

llm = ChatGroq(
    temperature=0,
    model_name="qwen-2.5-32b"
)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def document_grader_agent():
    NUMERIC_GRADE_PROMPT = ChatPromptTemplate.from_messages([
        ("system", "You are an expert grader. Rate the relevance of a document to a question on a scale of 1 to 5, where 1 means not relevant at all and 5 means highly relevant. Respond with only the number."),
        ("human", "Retrieved document:\n{document}\nUser question:\n{question}\nScore (1-5):")
    ])
    # Create the chain with the updated prompt
    doc_grader = NUMERIC_GRADE_PROMPT | llm | StrOutputParser()
    return doc_grader

def qa_agent():
    # Define system and human messages separately
    system_template = """You are an assistant for question-answering tasks. 
    Use the provided context to answer questions accurately.
    If no context is present or you don't know the answer, say so.
    Do not make up answers - only use information from the context.
    Give detailed and focused answers."""

    human_template = """Context: {context}
    
    Question: {question}"""

    # Create chat prompt from messages
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("human", human_template),
    ])

    # Create QA chain
    qa_rag_chain = (
        {
            "context": (itemgetter("context") | RunnableLambda(format_docs)),
            "question": itemgetter("question")
        }
        | chat_prompt
        | llm
        | StrOutputParser()
    )
    
    return qa_rag_chain

def query_rewriter_agent(state):
    # Get question from state
    question = state["question"]
    
    # System prompt remains unchanged
    SYS_PROMPT = """Act as a question re-writer and perform the following task:
                 - Convert the following input question to a better version that is optimized for web search.
                 - When re-writing, look at the input question and try to reason about the underlying semantic intent / meaning.
                 """
    
    re_write_prompt = ChatPromptTemplate.from_messages([
        ("system", SYS_PROMPT),
        ("human", """Here is the initial question:
                    {question}

                    Formulate an improved question.""")
    ])

    # Create rephraser chain
    question_rewriter = (
        re_write_prompt
        | llm
        | StrOutputParser()
    )
    
    # Invoke chain with question
    rewritten_question = question_rewriter.invoke({"question": question})
    
    # Return updated state
    return {"question": rewritten_question}

def emotion():
    emotion_prompt = ChatPromptTemplate.from_template("""
    Analyze this message's emotion. Respond ONLY with one word:
    happy, sad, angry, or neutral. Message: {input}""")
    emotion_chain = emotion_prompt | llm | StrOutputParser()
    return emotion_chain

def search_agent():
    tv_search = TavilySearchResults(
        max_results=8,
        search_depth="advanced",
        max_tokens=10000,
    )
    return tv_search
