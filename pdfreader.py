import streamlit as st
import tempfile
from langchain import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import CTransformers
import os
import psutil

def display_system_resources():
    st.sidebar.title("System Resource Utilization")
    
    # CPU utilization
    cpu_percentage = psutil.cpu_percent(interval=1) / 100.0
    st.sidebar.progress(cpu_percentage)
    st.sidebar.text(f"CPU: {cpu_percentage * 100}%")
    
    # RAM utilization
    ram = psutil.virtual_memory()
    st.sidebar.progress(ram.percent / 100.0)  # Divide by 100 to normalize
    st.sidebar.text(f"RAM: {ram.percent}%")

# Streamlit interface setup
st.title('Llama Investment Banker')
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

# Call the function to display system resources
display_system_resources()

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        tmpfile.write(uploaded_file.getvalue())
        temp_path = tmpfile.name
    
    loader = PyPDFLoader(temp_path)
    documents = loader.load()
    
    if not isinstance(documents, list):
        documents = [documents]

    if not all(hasattr(doc, 'page_content') for doc in documents):
        st.write("There was an error processing the document. The format might not be supported.")
    else:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        text_chunks = text_splitter.split_documents(documents)
        
        embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device':'cpu'})
        vector_store = FAISS.from_documents(text_chunks, embeddings)
        
        llm = CTransformers(model="/home/yopz/documents/LargeLanguageModelsProjects/Run_llama2_local_cpu_upload/models/llama-2-7b-chat.ggmlv3.q8_0.bin",
                            model_type="llama",
                            config={'max_new_tokens': 128, 'temperature': 0.01})
        
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
        
        user_input = st.text_input('Input your prompt here')
        if user_input:
            result = chain({'query': user_input})
            st.write(f"Answer: {result['result']}")

    os.remove(temp_path)
else:
    st.write("Please upload a PDF to proceed.")
