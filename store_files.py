# Load documents from directory
from langchain.document_loaders import DirectoryLoader,AmazonTextractPDFLoader
def dir_loader(path):
    loader = DirectoryLoader(
    path,
    "**/[!.]*",
    {
        ".pdf": lambda path: AmazonTextractPDFLoader(path),
        "recursive": True
    }
    )
    documents = loader.load()
    return documents
print("Loader.............start")
documents = dir_loader("documents")
print("Loader.............end")

# Chroma instance 
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
key = "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"
embeddings = OpenAIEmbeddings(api_key=key)
chroma = Chroma( collection_name="user_stories",persist_directory="chroma/", embedding_function=embeddings)




# Use Parent Retriever to split and store documents in chroma vector store
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.storage import InMemoryStore
from langchain.retrievers import ParentDocumentRetriever

child_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
store = InMemoryStore()
parent_retriever = ParentDocumentRetriever(
    vectorstore=chroma,
    docstore=store,
    child_splitter=child_splitter,
    search_kwargs = {"k": 5}
)


total_documents = len(documents)
# batch_size = total_documents // 4
# print(f"total_documents={total_documents}")
# # Add documents in four batches
# for i in range(4):
#     start_index = i * batch_size
#     end_index = (i + 1) * batch_size if i < 3 else total_documents
#     batch_documents = documents[start_index:end_index]
#     print(f"start_index={start_index} => end_index={end_index}")
#     print(f"Batch {i + 1} Documents:")
#     for doc in batch_documents:
#         print(doc.metadata)
#     # Add the current batch of documents to parent_retriever
#     print("embedding.............start")
#     parent_retriever.add_documents(batch_documents)
#     print("embedding.............end")


# Define the batch size
batch_size = 500

# Iterate over batches
for start_index in range(0, len(documents), batch_size):
    end_index = min(start_index + batch_size, len(documents))
    batch_documents = documents[start_index:end_index]
    print(f"start_index={start_index} => end_index={end_index}")

    # Print the documents in the current batch
    print(f"Batch {start_index // batch_size + 1} Documents:")
    for doc in batch_documents:
         print(doc.metadata)
    # Add the current batch of documents to parent_retriever
    print("embedding.............start")
    parent_retriever.add_documents(batch_documents)
    print("embedding.............end")






# print("embedding.............start")
# parent_retriever.add_documents(documents)
# print("embedding.............end")




from pkl_file import key_document_pairs, save_to_file

# get keys and documents from memeory store
keys = list(store.yield_keys())
documents = list(store.mget(keys))

# Create a list of tuples
keys_documents = key_document_pairs(keys,documents)

# Specify the file path where you want to save the data in memory
file_path = 'ids_docs.pkl'

# Call the function to save the data to the file
save_to_file(keys_documents, file_path)


from langchain.storage import InMemoryStore
from pkl_file import load_from_file
file_path = 'ids_docs.pkl'
print(f"total_documents={total_documents}")

docs = load_from_file(file_path)
print(len(docs))
