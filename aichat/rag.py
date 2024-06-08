from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
import dotenv

class rag():

    dotenv.load_dotenv()

    # Define a function to create a DirectoryLoader for a specific file type
   
    def get_pinecone_vectorstore(self):
        embeddings = OpenAIEmbeddings(model='text-embedding-3-large')# aryan recommened
        vectorstore = PineconeVectorStore(  embedding=embeddings,
                                            index_name="hukukai",
                                            )

        return vectorstore

    def get_FAISS_vectorstore(self, chunks):
        embeddings = OpenAIEmbeddings(model='text-embedding-3-large')
        faiss_vectorstore = FAISS.from_documents(chunks, embeddings)

        return faiss_vectorstore


    def get_bm25_vectorstore(self, chunks):
        bm25_retriever = BM25Retriever()
        
        bm25_retriever.k = 2

        return bm25_retriever

    def get_retriver(self, retrivers):
        ensemble_retriever = EnsembleRetriever(retrievers=retrivers)
        return ensemble_retriever


    def self_querying_retriever(self, vectorstore):
        llm = ChatOpenAI(temperature=0)
        metadata_field_info = [AttributeInfo(name= 'source', description= 'kaynak belge', type='string',), AttributeInfo(name='source_type', description= 'metin dili', type='string',),
                        AttributeInfo(name='text', description= 'metnin kendisi', type='string',), AttributeInfo(name='esas', description= 'esas numarasi', type='string',),
                        AttributeInfo(name='karar', description= 'karar numarasi', type='string',)]
        document_content_description = "ictihat metinleri"
        retriever = SelfQueryRetriever.from_llm(
        llm= llm,
        vectorstore= vectorstore,
        metadata_field_info=metadata_field_info,
        document_contents= document_content_description
            )   
        return retriever


    def add_documents_pinecone(self,chunks):
        self.pinecone_vs.add_documents(chunks)


    def add_documents_faiss(self, chunks):
        self.faiss_vs.add_documents(chunks)

    def rag_context(self, query):
        pinecone_vs = self.get_pinecone_vectorstore()
        self_querying = self.self_querying_retriever(pinecone_vs)
        retriever = self.get_retriver(retrivers=[pinecone_vs.as_retriever(), self_querying])

        documents = retriever.invoke(input=query)
        return documents