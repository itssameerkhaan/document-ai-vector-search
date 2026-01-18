import os
import time

from langgraph.graph import StateGraph, START, END
from typing import TypedDict

from core.input.nodeInput import extract,file_count_varification,vector_store
from core.input.nodeInput import state

# class state(TypedDict):
#     content : str
#     query : str
#     query_varification : bool

graph = StateGraph(state)

#-----NODE
graph.add_node('extract',extract)
graph.add_node('vectore_store',vector_store)
# graph.add_node('create_query',create_query)
# graph.add_node('varify_query', varify_query)
# graph.add_node('login_to_email',log_emil)
# graph.add_node('fetching',fetching)
# graph.add_node('deleteBackups',deleteBackups)


#-----EDGES
graph.add_edge(START,'extract')
graph.add_conditional_edges('extract',file_count_varification,{True:'vectore_store',False:END})
graph.add_edge('vectore_store',END)
# graph.add_conditional_edges('content',line_varify,{True:'create_query',False:'content'})
# graph.add_edge('create_query', 'varify_query')
# graph.add_conditional_edges('varify_query', route_varify_query, {
#     'yes': 'login_to_email',
#     'no': 'create_query'
# })
# graph.add_conditional_edges('login_to_email',line_varify,{True:'fetching',False:'content'})
# graph.add_conditional_edges('fetching',line_varify,{True:'deleteBackups',False:'content'})
# graph.add_edge('deleteBackups',END)
graph.add_edge('extract',END)



initial_state = {
    "File_count" :0,
    "Extracted":False,
    "Embedding":False,
    "VDB_upload":False,
    "File_names":[],
    "Result":[],
    "Path" : ""
}

def run():
    workflow = graph.compile()
    upload_dir = os.path.abspath(r"D:\RAG_document_queries\root\uploads")
    files = [f for f in os.listdir(upload_dir)]
    if files:
        print(f"extracting total files are  file :- {files}")
        final_state = workflow.invoke(initial_state)
        print("FINAL STATE IS :-",final_state)
        print("FOLDER PATH IS :- ",final_state['Paths'])
        for f in files:
            file_path = os.path.join(upload_dir, f)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {f}")
            except Exception as e:
                print(f"Could not delete {f}: {e}")

    time.sleep(2)
 