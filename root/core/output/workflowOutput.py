import os
import time

from langgraph.graph import StateGraph, START, END
from typing import TypedDict

from core.output.nodeOutput import retrieve_from_chroma,summarize_results
from core.output.nodeOutput import state



graph = StateGraph(state)

#-----NODE
graph.add_node('retrieve_from_chroma',retrieve_from_chroma)
graph.add_node('summarize_results',summarize_results)



#-----EDGES
graph.add_edge(START,'retrieve_from_chroma')
graph.add_edge('retrieve_from_chroma','summarize_results')
graph.add_edge('summarize_results', END)
# graph.add_conditional_edges('varify_query', route_varify_query, {
#     'yes': 'login_to_email',
#     'no': 'create_query'
# })




def run_output(query,memory):
    initial_state = {
        "Query" :query,
        "Result" : "",
        "Embedding" : False,
        "File_count" : 0,
        "File_paths" : [],
        "Previouse_result" : [],
        "Output" : "",
        "Memory" : memory
    }
    workflow = graph.compile()
    final_state = workflow.invoke(initial_state)
    return str(final_state['Output']),str(final_state['Result'])