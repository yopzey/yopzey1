import streamlit as st
import pandas as pd
import tempfile
from langchain import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import CTransformers
import os

# Simple Document-like structure
class SimpleDocument:
    def __init__(self, content, metadata=None):
        self.page_content = content
        if metadata is None:
            metadata = {}  # default to an empty dictionary if no metadata is provided
        self.metadata = metadata

# Streamlit interface setup
st.title('Llama Investment Banker')
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    # Load the CSV file into a DataFrame
    df = pd.read_csv(uploaded_file)
    
    # Convert the entire DataFrame to a list of texts (each row is one text)
    texts = df.apply(lambda row: ' '.join(row.astype(str)), axis=1).tolist()

    # Wrap texts in simple Document-like structures
    documents = [SimpleDocument(text) for text in texts]

    # Split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    text_chunks = text_splitter.split_documents(documents)
    
    # Load embeddings and create a vector store
    embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device':'cpu'})
    vector_store = FAISS.from_documents(text_chunks, embeddings)
    
    # Setup the LLM
    llm = CTransformers(model="/home/yopz/documents/LargeLanguageModelsProjects/Run_llama2_local_cpu_upload/models/llama-2-7b-chat.ggmlv3.q8_0.bin",
                        model_type="llama",
                        config={'max_new_tokens': 128, 'temperature': 0.01})
    
    # Setup the prompt template and chain
    template = """Use the following pieces of information to answer the user's question.
    If you don't know the answer, just say you don't know; don't try to make up an answer.
    
    Context:{context}
    Question:{question}
    
    Only return the helpful answer below and nothing else:
    Helpful answer
    """
    qa_prompt = PromptTemplate(template=template, input_variables=['context', 'question'])
    chain = RetrievalQA.from_chain_type(llm=llm,
                                        chain_type='stuff',
                                        retriever=vector_store.as_retriever(search_kwargs={'k': 2}),
                                        return_source_documents=True,
                                        chain_type_kwargs={'prompt': qa_prompt})
    
    # Get user's query and display the result
    user_input = st.text_input('Input your prompt here')
    if user_input:
        result = chain({'query': user_input})
        st.write(f"Answer: {result['result']}")

else:
    st.write("Please upload a CSV to proceed.")
