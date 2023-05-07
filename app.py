############################################################################################
##  querying a private OpenAI instance on Azure with private documents
##
##  the basic steps to indexing and querying a model are
##      
##  1. Load in documents (either manually, or through a data loader)
##  2. [Optional] Parse the Documents into Nodes
##  3. Construct Index (from Nodes or Documents)
##  4. [Optional, Advanced] Building indices on top of other indices
##  5. Query the index
##
#############################################################################################
import os
import gradio as gr
from llm_utils import LLMServiceSetup, BuildIndexes, LoadIndexes, CreateComposableGraph

using_docker=False

server_port=80      # this can remain 80 even if you deploy with a container app service, 443 not needed

username='queryuser'            ## dont use gradio method of authentication for production
password='$qP5*uB8!rN1^tE0&mX'

doc_path = 'data'
index_path = 'index'

## Index creation vars
doc_set = {}
all_docs = []
years = [2022, 2021, 2020, 2019]

# build the service context - this is the link to Azure OpenAI
service_context = LLMServiceSetup()

# Build individual indexes for the 10K statements plus an index for mixed documents and one for all documents
#  set names are 2019, 2020, 2021, 2022, mixed and all_docs
index_set = BuildIndexes(years, doc_path, index_path, doc_set, all_docs, service_context)

this_index_set = LoadIndexes(years, index_path, service_context, index_set)

graph = CreateComposableGraph(years, this_index_set, service_context)

# this global collection of query engines will be used by the chat function
qe_set = {}
for year in years:
    ## build a storage context from the persisted year index
    qe_set[str(year)] = index_set[str(year)].as_query_engine()

qe_set["mixed"] = index_set["mixed"].as_query_engine()
qe_set["all_docs"] = index_set["all_docs"].as_query_engine()
qe_set["graph"] = graph.as_query_engine()

def query_fn(input_text,index_name):
    global qe_set
    response = qe_set[index_name].query(input_text)
    return response.response

#  build the UI
description_text = """
<div style="text-align:center;">
  <h2>Index Description</h2>
  <ul style="list-style:none;">
    <li><strong>2019-2022:</strong> Uber annual 10K filings</li>
    <li><strong>graph:</strong> Combined index of Uber filings utilizing a Composable Graph</li>
    <li><strong>mixed:</strong> Mixed set of business documents in different formats</li>
    <li><strong>all_docs:</strong> Single index of all documents</li>
  </ul>
</div>
"""

iface = gr.Interface(fn=query_fn,
                     inputs= [
                        gr.components.Textbox(lines=7, label="Enter your query"),
                        gr.Dropdown(["2019", "2020", "2021", "2022","graph","mixed","all_docs"], value="mixed", label="Index")
                     ],
                     outputs=gr.Textbox(max_lines=500,label="Query Result"),
                     title="LLM Query with Custom Indexes",
                     description=description_text)

# launch the UI but do not share it publicly
if using_docker:
  iface.launch(share=False, server_port=server_port,server_name="0.0.0.0",auth=(username, password))
else:
  iface.launch(share=False, server_port=server_port,auth=(username, password))