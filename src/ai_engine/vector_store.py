import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from src.utils.config import MERGED_DATA_FILE, CHROMA_DB_DIR

def rebuild_knowledge_base():
    print("Updating AI's data base")
    if not MERGED_DATA_FILE.exists():
        print("No merged data file. Start the merging first")
        return 
    
    df = pd.read_csv(MERGED_DATA_FILE)

    #cleaning up the data first 
    df['Views'] = pd.to_numeric(df['Views'], errors='coerce').fillna(0)

    #taking only top 30% 
    threshold = df['Views'].quantile(0.70)
    viral_df = df[df['Views'] >= threshold]

    print(f"All videos: {len(df)}")
    print(f"Best videos for learning: {len(viral_df)}")

    #initializing db
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

    #embeddings, transforming text into
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    try:
        client.delete_collection("viral_scripts")
    except:
        pass

    collection = client.create_collection(name="viral_scripts", embedding_function=ef)

    #preparing the documents
    documents = []
    metadatas = []
    ids = []

    for idx, row in viral_df.iterrows():
        text = str(row.get('Transcription',''))
        if len(text) < 10:
            continue

        meta = {
            "title": str(row.get('Title', 'Unknown')),
            "views": str(row.get('Views', '')),
            "wpm": str(row.get('Words_per_Minute', '')),
            "brightness": str(row.get('Brightness', ''))
        }

        documents.append(text)
        metadatas.append(meta)
        ids.append(f"vid_{idx}")

    if documents:
        collection.add(documents=documents, metadatas=metadatas, ids = ids)
        print("Data base is sucessfully transformed")
    else:
        print("There is nothing to add to the data base")

if __name__ == "__main__":
    rebuild_knowledge_base()