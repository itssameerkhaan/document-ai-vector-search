import google.generativeai as genai
from typing import TypedDict, Literal
from pprint import pprint
import os
import shutil
import json
import re
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma
from datetime import datetime, timedelta



gen_api = "AIzaSyAZxVjn4kkIzig1Y1Bgx2PGcCceV6TFgQA"
genai.configure(api_key=gen_api)
# model = genai.GenerativeModel("gemini-2.5-flash")


class state(TypedDict):
    Query : str
    Result : str
    Embedding : bool
    File_count : int
    File_paths : list
    Previouse_result : list
    Output : str
    Memory : list


DB_PATH = r"D:\RAG_document_queries\root\vectore_db"
COLLECTION_NAME = "my_documents_vectoreDB"


embedding = HuggingFaceBgeEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

chroma_db = Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=embedding,
    persist_directory=DB_PATH
)

def retrieve_from_chroma(State: state) -> state:
    """Search the Chroma DB using user query."""
    print("I AM IN OUTPUT QUERY MODE")
    if len(State['Memory'])  < 1 :
        print("I AM GETTING THE FILE FORM CFHOMA")
        query = State["Query"]
        results = chroma_db.similarity_search(query, k=3)
        print("RESULT IS :- ",results)
        print("LENGTH OF RESULT IS :- ",len(results))
        formatted = [
            {
                "content": r.page_content,
                "metadata": r.metadata
            }
            for r in results
        ]
        State["Result"] = formatted
    else:
        print("I AM ANSWERING YOU QUERY USING MEMEORY")
    return State


def summarize_results(State: state) -> state:
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content([f"""You are an expert AI assistant specializing in technical document comprehension.
                                            You are provided with {State['Result']}, previouse query answers and results in this memory {State['Memory']}, and a {State['Query']} query.

                                            Your task is to answer the query only using information contained in the document and memory.
                                            Do not generate, assume, or hallucinate any external information.
                                            If the document does not contain a clear answer, respond exactly with:

                                            "The document does not provide a specific answer to this query."""])
    return {'Output':response.text}