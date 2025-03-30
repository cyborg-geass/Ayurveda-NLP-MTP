from agents_graph import run_agentic_rag
from dotenv import load_dotenv
import os
import warnings
warnings.filterwarnings("ignore")

load_dotenv()

if __name__ == "__main__":
    # question = input("Ask a question: ")
    # answer = run_agentic_rag(question)
    # print(answer)
    run_agentic_rag()
