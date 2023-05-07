"""Init File"""
import os
from pathlib import Path

from langchain.llms import AzureOpenAI
from langchain.embeddings import OpenAIEmbeddings

from llama_index import LangchainEmbedding
from llama_index import (
    GPTVectorStoreIndex,
    SimpleDirectoryReader,
    LLMPredictor,
    PromptHelper,
    StorageContext,
    ServiceContext, 
    download_loader,
    GPTListIndex,
    ComposableGraph,
    load_index_from_storage,
    load_graph_from_storage
)
def LLMServiceSetup():
    # increase the size of prompt completions (responses)
    max_tokens = 2048 

    llm_deployment_name = "AIHackathonLLM2"
    embedding_deployment_name = "AIHackathonModel"


    # Create LLM, Predictor, and Embedding Model
    llm = AzureOpenAI(deployment_name=llm_deployment_name, max_tokens=max_tokens)

    llm_predictor = LLMPredictor(llm=llm)

    embedding_llm = LangchainEmbedding(OpenAIEmbeddings(deployment=embedding_deployment_name),embed_batch_size=1)

    # Define prompt helper
    max_input_size = 3000 # Maximum input size for the LLM
    num_output = 256 # Number of outputs for the LLM
    chunk_size_limit = 512 # token window size per document
    max_chunk_overlap = 20 # overlap for each token fragment
    prompt_helper = PromptHelper(max_input_size=max_input_size, num_output=num_output, max_chunk_overlap=max_chunk_overlap, chunk_size_limit=chunk_size_limit)

    # Build a service context so we can use it later -- this is the link back to our private OpenAI instance
    return ServiceContext.from_defaults(llm_predictor=llm_predictor, embed_model=embedding_llm, prompt_helper=prompt_helper)

def BuildIndexes(years, doc_path, index_path, doc_set, all_docs, service_context):
    ## Perform indexing and pesisting here

    index_set = {}

    # Build the list of documents to be indexed
    #
    UnstructuredReader = download_loader("UnstructuredReader", refresh_cache=True)
    loader = UnstructuredReader()

    ## annual reports
    #
    if os.path.exists(index_path + '/uber'):
        print(f"Skipping indexing for uber.")
    else:
        print(f"Performing indexing of uber documents.")
        ## Build the list of documents
        for year in years:
            year_docs = loader.load_data(file=Path(doc_path + f'/uber/UBER_{year}.html'), split_documents=False)
            # insert year metadata into each year
            for d in year_docs:
                d.extra_info = {"year": year}
            doc_set[year] = year_docs   # add to doc_set for individal indexing by year
            all_docs.extend(year_docs)  # add to the all_docs list for global indexing

        ## Build and persist the indices
        for year in years:
            cur_index = GPTVectorStoreIndex.from_documents(doc_set[year], service_context=service_context)
            index_set[str(year)] = cur_index
            cur_index.storage_context.persist(persist_dir=index_path + f'/uber/{year}')

    
    ## mixed documents
    #
    if os.path.exists(index_path + '/mixed'):
        print(f"Skipping indexing for mixed.")
    else:
        print(f"Performing indexing of mixed documents.")

        ## Build the list of documents
        loader = SimpleDirectoryReader(doc_path + '/mixed', recursive=True, exclude_hidden=True)
        mixed_docs = loader.load_data()
        doc_set['mixed'] = mixed_docs   # add to doc_set for individal indexing by year
        all_docs.extend(mixed_docs)     # add to the all_docs list for global indexing

        ## Build and persist the mixed index
        mixed_index = GPTVectorStoreIndex.from_documents(doc_set['mixed'], service_context=service_context)
        index_set['mixed'] = mixed_index
        mixed_index.storage_context.persist(persist_dir=index_path + '/mixed')

    ## all documents
    #
    if os.path.exists(index_path + '/all_docs'):
        print(f"Skipping indexing for all_docs.")
    else:
        print(f"Performing indexing of all documents.")

        ## This all_docs index is a single vector store containing all documents
        all_docs_index = GPTVectorStoreIndex.from_documents(all_docs, service_context=service_context)
        index_set['all_docs'] = all_docs_index
        all_docs_index.storage_context.persist(persist_dir=index_path + '/all_docs')

    return index_set

def LoadIndexes(years, index_path, service_context,index_set ):
    #############################################################################################
    ##  Load the indices from persistent storage
    ##

    ## Load annual report indices from disk
    for year in years:
        ## build a storage context from the persisted year index
        if not(str(year) in index_set):
            print('index {year} not present in memory, loading now ...')
            storage_context = StorageContext.from_defaults(persist_dir=index_path + f'/uber/{year}')

            ## load the index from the storage context using our Azure service context
            cur_index = load_index_from_storage(storage_context,service_context=service_context)
            index_set[str(year)] = cur_index

    ## Load mixed index
    if not('mixed' in index_set):
        print('index mixed not present in memory, loading now ...')
        storage_context = StorageContext.from_defaults(persist_dir=index_path + '/mixed')
        index_set["mixed"] = load_index_from_storage(storage_context,service_context=service_context)

    ## Load all_docs index
    if not('all_docs' in index_set):
        print('index all_docs not present in memory, loading now ...')
        storage_context = StorageContext.from_defaults(persist_dir=index_path + '/all_docs')
        index_set["all_docs"] = load_index_from_storage(storage_context,service_context=service_context)

    return index_set

def CreateComposableGraph(years,index_set, service_context):
    #############################################################################################
    ##  Create a composable graph of annual report indexes
    ##
    storage_context = StorageContext.from_defaults()

    # set summary text for each index
    summaries = {}
    for year in years:
        summaries[year] = f"UBER 10-k Filing for {year} fiscal year"

    summaries['mixed'] = "Mixed collection of documents on different topics"
    summaries['blake'] = "Video workshop collection of documents"
    summaries['all_docs']= "Collection of mixed documents on different topics and UBER 10K Filings"

    graph = ComposableGraph.from_indices(
        GPTListIndex,
        [index_set[str(y)] for y in years],
        [summaries[y] for y in years],
    #    [index_set[key] for key in index_set],
    #    [summaries[key] for key in summaries],
        storage_context=storage_context,
        service_context=service_context,
    )

    return graph
