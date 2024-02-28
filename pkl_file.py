import pickle
from typing import List, Tuple, Sequence
from langchain.storage import InMemoryStore


#Load data from .pkl file 
def key_document_pairs(keys,documents) -> Sequence[Tuple[str, str]]:
    # Create a list of tuples
    keys_documents: List[Tuple[str, str]] = list(zip(keys, documents))
    return keys_documents

#Store data into .pkl file 
def save_to_file(data: Sequence[Tuple[str, str]], file_path: str):
    with open(file_path, 'wb') as file:
        pickle.dump(data, file)


#Load data from .pkl file 
def load_from_file(file_path: str) -> Sequence[Tuple[str, str]]:
    with open(file_path, 'rb') as file:
        data = pickle.load(file)    
    return data

def append_data(data: Sequence[Tuple[str, str]], file_path: str):
    old_data = load_from_file(file_path)
    store = InMemoryStore()
    store.mset(old_data)
    store.mset(data)
    keys = list(store.yield_keys())
    documents = list(store.mget(keys))
    # Create a list of tuples
    keys_documents = key_document_pairs(keys,documents)
    save_to_file(keys_documents, file_path)



