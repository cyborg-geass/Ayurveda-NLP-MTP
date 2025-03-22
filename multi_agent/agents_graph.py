from retrieval import retrieval
from agents import document_grader_agent, search_agent, qa_agent, query_rewriter_agent, emotion, llm
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from typing import List, TypedDict, Literal, Dict
from langgraph.graph import StateGraph, END, START
from langchain.memory import ConversationBufferMemory

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM response generation
        web_search_needed: flag of whether to add web search - yes or no
        documents: list of context documents
    """

    question: str
    generation: str
    web_search_needed: str
    documents: List[Document]
    emotion: Literal["happy", "sad", "angry", "neutral"]
    history: List[Dict[str, str]]

memory = ConversationBufferMemory()


def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents - that contains retrieved context documents
    """
    print("---RETRIEVAL FROM VECTOR DB---")
    question = state["question"]

    # Retrieval
    retriever = None
    try:
        retriever = retrieval("RAG_MultiAgent_Ayurveda")
    except Exception as e:
        print(f"Error initializing retriever: {e}")
    
    if retriever is None:
        raise ValueError("Retriever could not be initialized.")
    # retriever = retriever("../RAG_MultiAgent_Ayurveda")
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}

def detect_emotion(state):
    emotion_chain = emotion()
    emotion_det = emotion_chain.invoke({"input": state["question"]}).strip().lower()
    return {**state, "emotion": emotion_det}

def format_history(history: List[Dict[str, str]]) -> str:
    """Format a list of chat message dictionaries into a readable string.
    
    Args:
        history: List of dictionaries with 'user' and 'bot' keys containing messages
        
    Returns:
        Formatted string of chat history with user and bot messages
        
    Example:
        >>> messages = [
        ...     {"user": "Hello", "bot": "Hi there"},
        ...     {"user": "How are you?", "bot": "I'm good"}
        ... ]
        >>> print(format_history(messages))
        User: Hello
        Bot: Hi there
        User: How are you?
        Bot: I'm good
    """
    if not history:
        return ""
        
    formatted_messages = []
    for message in history:
        try:
            user_msg = message.get('user', '')
            bot_msg = message.get('bot', '')
            formatted_messages.append(f"User: {user_msg}\nBot: {bot_msg}")
        except (KeyError, AttributeError) as e:
            continue
            
    return "\n".join(formatted_messages)

def grade_documents(state):
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]

    relevant_docs = []
    total_score = 0
    num_docs = len(documents)

    for d in documents:
        # Get the numeric score from the LLM
        doc_grader = document_grader_agent()
        score_str = doc_grader.invoke({"question": question, "document": d.page_content}).strip()
        try:
            score = float(score_str)
        except ValueError:
            # If parsing fails, assume a low score
            score = 1
        total_score += score

        # Consider the document relevant if score >= 3 (adjust threshold as needed)
        if score >= 3:
            print(f"---GRADE: Document scored {score} and is relevant ---")
            relevant_docs.append(d)
        else:
            print(f"---GRADE: Document scored {score} and is not relevant ---")

    # Option 1: Use average score to decide if web search is needed
    avg_score = total_score / num_docs if num_docs > 0 else 0
    web_search_needed = "Yes" if avg_score < 4 else "No"

    # Option 2: We could also set a rule based on the number of relevant docs if you prefer
    # For example, trigger web search if fewer than half the documents are relevant:
    # web_search_needed = "Yes" if len(relevant_docs) < (num_docs / 2) else "No"

    return {"documents": relevant_docs, "web_search_needed": web_search_needed}

from langchain_core.documents import Document
def web_search(state):
    """
    Web search based on the re-written question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with appended web results
    """

    print("---WEB SEARCH---")
    question = state["question"]
    documents = state["documents"]

    # Web search
    tv_search = search_agent()
    docs = tv_search.invoke(question)
    # Check if 'docs' is a list of strings, if so, convert to expected format
    if all(isinstance(item, str) for item in docs):
        web_results = "\n\n".join(docs)
        web_results = Document(page_content=web_results)
    else:  # Assuming it's the expected list of dictionaries
        web_results = "\n\n".join([d.get("content", "") for d in docs])  # Handle missing 'content'
        web_results = Document(page_content=web_results)
    documents.append(web_results)

    return {"documents": documents, "question": question}

# Modified RAG Prompt with Emotion Context
response_prompt = ChatPromptTemplate.from_template("""
[Role] You're an Ayurveda expert. Consider the user's emotion: {emotion}
[Emotion Guidelines]
- Happy 😊: Be enthusiastic, use emojis occasionally
- Sad 😢: Show empathy, offer gentle suggestions
- Angry 😠: Stay calm, be solution-focused
- Neutral 😐: Be concise and factual

[Chat History]
{history}

[Relevant Context]
{context}

[Current Question]
{question}

[Response]
""")


# Modified Generate Answer Node
def generate_answer(state: GraphState):
    """Node: Generate emotion-aware response"""
    print("---GENERATING EMOTION-AWARE RESPONSE---")
    history_str = format_history(state["history"])
    
    # Build prompt with emotion context
    prompt = response_prompt.format(
        question=state["question"],
        context="\n\n".join(doc.page_content for doc in state["documents"]),
        emotion=state["emotion"],
        history=history_str
    )
    
    # Generate response
    response = llm.invoke(prompt).content
    
    # Update memory
    memory.save_context(
        {"input": state["question"]}, 
        {"output": response}
    )
    
    return {
        **state, 
        "generation": response,
        "history": state["history"] + [
            {"user": state["question"], "bot": response}
        ]
    }


def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    print("---ASSESS GRADED DOCUMENTS---")
    web_search_needed = state["web_search_needed"]

    if web_search_needed == "Yes":
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print("---DECISION: SOME or ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, REWRITE QUERY---")
        return "rewrite_query"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE RESPONSE---")
        return "generate_answer"

# rewrite_query = query_rewriter_agent(state)
agentic_rag = StateGraph(GraphState)

# Define the nodes
agentic_rag.add_node("detect_emotion", detect_emotion)
agentic_rag.add_node("retrieve", retrieve)
agentic_rag.add_node("grade_documents", grade_documents)  # Your existing grading function
agentic_rag.add_node("generate_answer", generate_answer)
agentic_rag.add_node("web_search", web_search)  # Your existing web search

# Define workflow
agentic_rag.set_entry_point("detect_emotion")
agentic_rag.add_edge("detect_emotion", "retrieve")
agentic_rag.add_edge("retrieve", "grade_documents")
agentic_rag.add_conditional_edges(
    "grade_documents",
    decide_to_generate,  # Your existing decision function
    {
        "rewrite_query": "web_search",
        "generate_answer": "generate_answer"
    }
)
agentic_rag.add_edge("web_search", "generate_answer")
agentic_rag.add_edge("generate_answer", END)

# Compile
agentic_rag = agentic_rag.compile()

def run_agentic_rag() -> str:
    """
    Run the agentic RAG graph

    Args:
        question (str): The question to answer

    Returns:
        str: The generated answer
    """
    print("🌿 Welcome to Ayurveda Companion! (Type 'exit' to quit)")
    history = []
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Bot: Until next time! 🙏")
                break
                
            # Initialize state
            state = {
                "question": user_input,
                "generation": "",
                "web_search_needed": "no",
                "documents": [],
                "emotion": "neutral",
                "history": history
            }
            
            # Execute workflow
            result = agentic_rag.invoke(state)
            response = result["generation"]
            history = result["history"]
            
            # Display with emotion indicator
            emotion_icon = {
                "happy": "😊",
                "sad": "😢",
                "angry": "😠",
                "neutral": "📚"
            }.get(result["emotion"], "📝")
            
            print(f"\nBot {emotion_icon}: {response}")
            
        except Exception as e:
            print(f"⚠️ Error: {str(e)}")
            continue

