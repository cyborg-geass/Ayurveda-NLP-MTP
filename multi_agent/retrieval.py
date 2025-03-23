import os
from langchain_community.vectorstores import FAISS, Qdrant
from langchain_community.document_loaders import PyPDFLoader, PyPDFDirectoryLoader, PyMuPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import pandas as pd
import fitz
import warnings
warnings.filterwarnings("ignore")

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

def extract_pdf_content(pdf_path):
    """
    Extract content from a PDF. For each page, extract the full text and
    any tables (converted to Markdown), then return a list of tuples (page_num, content).
    """
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        # Extract full page text
        page_text = page.get_text("text")

        # Extract tables and convert to Markdown if any exist
        table_markdowns = []
        tables = page.find_tables()
        if tables.tables:  # if any tables found
            for tab in tables:
                table_data = tab.extract()
                if len(table_data) >= 2:
                    # Assume first row as header
                    df = pd.DataFrame(table_data[1:], columns=table_data[0])
                else:
                    df = pd.DataFrame(table_data)
                markdown_table = df.to_markdown(index=False)
                table_markdowns.append(markdown_table)

        # Combine page text with table markdown if available
        combined = page_text
        if table_markdowns:
            combined += "\n\n---\nTables:\n" + "\n\n".join(table_markdowns)

        pages.append((i + 1, combined))
    doc.close()
    return pages

def get_documents_from_directory(directory):
    """
    Iterates over PDF files in the specified directory.
    For each PDF, it extracts page-level content and returns a list of Document objects,
    with metadata containing the file path and page number.
    """
    documents = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(".pdf"):
            file_path = os.path.join(directory, filename)
            pages = extract_pdf_content(file_path)
            for page_num, content in pages:
                metadata = {"source": file_path, "page": page_num}
                documents.append(Document(page_content=content, metadata=metadata))
    return documents

def vectorstore_save(directory, vector_path):
    """
    Extracts content from PDFs in the specified directory and returns a list of Document objects.
    """
    docs = get_documents_from_directory(directory)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, 
        chunk_overlap=500,
    )
    split_chunks = text_splitter.split_documents(docs)
    vectorstore = FAISS.from_documents(split_chunks, embeddings)
    vectorstore.save(vector_path)

def retrieval(vectorstore_path, save=True):
    """
    Load the vectorstore and return a retriever object.
    """
    if not os.path.exists(vectorstore_path) and save is False:
        raise FileNotFoundError(f"Vectorstore not found at path: {vectorstore_path}")
    elif not os.path.exists(vectorstore_path) and save is True:
        vectorstore_save("PDF_Data_Directory", vectorstore_path)
    vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever()
    return retriever
