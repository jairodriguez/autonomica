import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os

class VectorStore:
    def __init__(self, model_name='all-MiniLM-L6-v2', index_file='faiss.index'):
        self.model = SentenceTransformer(model_name)
        self.index_file = index_file
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            
        self.texts = []

    def add_texts(self, texts):
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        self.index.add(np.array(embeddings, dtype=np.float32))
        self.texts.extend(texts)
        self.save_index()

    def search(self, query_text, k=5):
        query_embedding = self.model.encode([query_text])
        distances, indices = self.index.search(np.array(query_embedding, dtype=np.float32), k)
        
        results = []
        for i in range(len(indices[0])):
            if indices[0][i] != -1:
                results.append({
                    'text': self.texts[indices[0][i]],
                    'distance': distances[0][i]
                })
        return results

    def save_index(self):
        faiss.write_index(self.index, self.index_file)

    def load_index(self):
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
        else:
            print("Index file not found. A new index will be created on add_texts.")

    def check_consistency(self):
        return len(self.texts) == self.index.ntotal

# Example Usage:
if __name__ == '__main__':
    vector_store = VectorStore()
    
    # Add some texts
    sample_texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Artificial intelligence is a branch of computer science.",
        "The sky is blue and the sun is bright.",
        "Natural language processing is a subfield of AI.",
        "FAISS is a library for efficient similarity search."
    ]
    vector_store.add_texts(sample_texts)
    
    # Search for similar texts
    query = "What is AI?"
    search_results = vector_store.search(query)
    
    print(f"Search results for: '{query}'")
    for result in search_results:
        print(f" - Text: {result['text']}, Distance: {result['distance']:.4f}")

    # Another search
    query_2 = "A fast animal."
    search_results_2 = vector_store.search(query_2)

    print(f"\nSearch results for: '{query_2}'")
    for result in search_results_2:
        print(f" - Text: {result['text']}, Distance: {result['distance']:.4f}") 