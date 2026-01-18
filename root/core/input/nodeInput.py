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
    File_count : int
    Extracted : bool
    Embedding : bool
    VDB_upload : bool
    File_names : list
    Results : list
    Paths : list


def safe_json_extract(raw_output):
    """
    Safely extract and parse JSON-like text from LLM responses.
    Returns dict with keys: category, confidence, summary
    """
    match = re.search(r'\{.*\}', raw_output, re.DOTALL)
    json_str = match.group(0) if match else raw_output

    json_str = json_str.encode("utf-8", "ignore").decode("utf-8")
    json_str = re.sub(r'[\x00-\x1f]+', ' ', json_str)

    # Step 3: Fix single quotes, unquoted keys, etc.
    # Add quotes around keys if missing
    json_str = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:\s*)', r'\1"\2"\3', json_str)
    # Replace single quotes with double quotes
    json_str = json_str.replace("'", '"')

    # Step 4: Try parsing, fallback to partial recovery
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print("JSON still malformed, attempting deep recovery...", e)
        # Soft fallback: find category manually
        category_match = re.search(r'Category[:\s"]+(Technical_Docs|Business_Reports)', raw_output, re.IGNORECASE)
        conf_match = re.search(r'confidence[:\s"]*([0-9.]+)', raw_output, re.IGNORECASE)
        summary_match = re.search(r'summary[:\s"]+(.+)', raw_output, re.IGNORECASE | re.DOTALL)
        data = {
            "category": category_match.group(1) if category_match else "Unknown",
            "confidence": float(conf_match.group(1)) if conf_match else 0.0,
            "summary": summary_match.group(1).strip() if summary_match else raw_output.strip()
        }
    return data





def extract(State :state) -> state:
    file_count = 0
    all_fileName = []
    files = [f for f in os.listdir(r"D:\RAG_document_queries\root\uploads")]
    files_uploaded = []
    results = []
    paths = []

    upload_dir = os.path.abspath(r"D:\RAG_document_queries\root\uploads")
    allowed_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".txt"]

    total_file = []

    for file in files:
        file_path = os.path.join(upload_dir, file)
        ext = os.path.splitext(file)[1].lower()
        if ext not in allowed_extensions:
            print(f"Skipping unsupported file type: {file}")
            continue
        if os.path.exists(file_path):
            uploaded_file = genai.upload_file(file_path)
            files_uploaded.append(uploaded_file)
            total_file.append(file)
            print("uploaded file is :- ", uploaded_file.display_name)
            all_fileName.append(uploaded_file.name)
            file_count += 1
        else:
            print(f"File not found: {file_path}")
    
    model = genai.GenerativeModel("gemini-2.5-flash")

    for file_u,origianl_file_name in zip(files_uploaded,total_file):
        try :
            pprint(f"getting response from :- {file_u}")
            response  = model.generate_content(["""Analyze the uploaded document carefully.

                                                    You must return your output strictly in the following JSON format (no other text outside the JSON):

                                                    {
                                                    "category": "<Technical_Docs or Business_Reports>",
                                                    "confidence": <a value between 0 and 1 showing how confident you are in the category>,
                                                    "summary": "<complete detailed plain-text explanation of the entire document>"
                                                    }

                                                    Category meanings:
                                                    - Technical_Docs: research papers, scientific/technical reports, datasets, implementation guides, or software/system design documents.
                                                    - Business_Reports: whitepapers, company reports, business analyses, financial or strategy documents, or management summaries.

                                                    Rules for the summary:
                                                    - Include every important detail (title, authors, purpose, methods, data, results, analysis, applications, conclusions, etc.).
                                                    - Use plain text (no markdown, no lists).
                                                    - Do not skip or shorten any section.
                                                    - Describe figures or tables in words.
                                                    - Be clear and continuous.
                                                    """
                                                    ,file_u])

            raw_output = response.text
            data = safe_json_extract(raw_output)          

            # Extract values
            category = data.get("category")
            confidence = data.get("confidence")
            summary = data.get("summary")
            file_name = file_u.display_name
            print("DISPLAY NAME IS :- ",file_name)

            print("CATEGORY IS :- ",category)
            print("CONFIDENCE IS :- ",confidence)
            print("SUMMARY IS :- ",summary)
            
            try:
                sourch_path = f"{upload_dir}//{origianl_file_name}"
                destination_path = os.path.join(f"D:\\RAG_document_queries\\root\\data_store\\{category}", file_name)
                shutil.copy(sourch_path, destination_path)
                print(f"file is copyed in :- {destination_path}")
            except Exception as e:
                print("Error is :- ",e)

            result = {'category' : category, 'confidence':confidence, 'file_name':file_name,'file_path':destination_path ,'summary':summary}
            results.append(result)
            paths.append(destination_path)
            print("####################################################################################################################################   SAMEER KHAN \n\n\n\n\n\n\n\n")
        except Exception as e:
            print(f"Error analyzing {file_u.name}: {e}")
        finally:
            # Cleanup to prevent stuck state / quota exhaustion
            try:
                genai.delete_file(file_u.name)
                print(f"Deleted remote file: {file_u.name}")
            except Exception as e:
                print(f"Cleanup failed for {file_u.name}: {e}")
    return {'File_count':file_count,'Extracted':True,"File_names":all_fileName,"Paths":paths,'Results':results}


def file_count_varification(State : state) -> state:
    if State["File_count"] > 0:
        return True
    else:
        return False


def vector_store(State : state) -> state:

    print("VECTORIGING THE DOCUMENT")
    embedding = HuggingFaceBgeEmbeddings(
                model_name="BAAI/bge-m3",
                model_kwargs={'device': 'cpu'},  
                encode_kwargs={'normalize_embeddings': True})
                
    chroma_db_path = r"D:\RAG_document_queries\root\vectore_db"  

    vectorstore = Chroma(
        collection_name="my_documents_vectoreDB",
        embedding_function=embedding,
        persist_directory=chroma_db_path
    )

    Texts = []
    metadatas = []

    for result in State['Results']:
        Texts.append(result['summary'])
        metadatas.append({
            'category': result['category'],
            'confidence': result['confidence'],
            'file_name': result['file_name'],
            'file_path': result['file_path'],
        })

    vectorstore.add_texts(texts=Texts, metadatas=metadatas)
    vectorstore.persist()
    print("FILE STORED IN VECOTRE DATABASE")
    return {'Embedding':True,'VDB_upload':True}