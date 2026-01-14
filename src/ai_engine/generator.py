import os
import chromadb
from chromadb.utils import embedding_functions
from google import genai
from google.genai import types
from src.utils.config import CHROMA_DB_DIR, API_KEY_CONFIG

API_KEY = API_KEY_CONFIG 

# RAG
def get_rag_context(topic, n_results=3):
    """
    Ищет 3 похожих успешных сценария в вашей локальной базе ChromaDB.
    """
    try:
        # connecting to the BD
        client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        # collection
        try:
            collection = client.get_collection(name="viral_scripts", embedding_function=ef)
        except ValueError:
            return "База знаний пока пуста. Запустите main.py для обучения."

        # search
        results = collection.query(query_texts=[topic], n_results=n_results)
        
        if not results['documents'] or not results['documents'][0]:
            return "Нет похожих референсов."

        docs = results['documents'][0]
        metas = results['metadatas'][0]
        
        # forming a clean text for the AI
        context_text = ""
        for i, doc in enumerate(docs):
            title = metas[i]['title']
            views = metas[i]['views']
            context_text += f"--- ПРИМЕР {i+1} (Просмотры: {views}) ---\nЗаголовок: {title}\nТекст: {doc}\n\n"
            
        return context_text
        
    except Exception as e:
        print(f"⚠️ Ошибка RAG: {e}")
        return ""

# gemini
def ai_audit_script(draft, topic, target_wpm, power_words):
    """
    Основная функция, которую вызывает интерфейс.
    1. Ищет контекст через get_rag_context.
    2. Отправляет всё в Google Gemini.
    """
    
    # searching for references
    references = get_rag_context(topic)
    
    # connecting to gemini
    try:
        client = genai.Client(api_key=API_KEY)
    except Exception as e:
        return f"Ошибка настройки клиента Google: {e}. Проверьте API Key.", ""
    
    # prompting
    system_instruction = f"""
    You are an elite UFC content creator. You write viral, high-retention TikTok scripts.
    
    YOUR GOAL: 
    Take the user's idea/draft and rewrite it into a finished script that people will watch till the end.
    Or create a new script while incorporating THE STATS given to you. Use them when they fit

    STYLE:
    - Energetic, slightly controversial.
    - NO robotic intros like "Welcome to the video". Start with an agressive, maybe negative bang.
    
    CONSTRAINTS:
    1.Make the hook more agressive
    2.Add a few power words from the list, ONLY if they are fitting
    3.Make sure, that the length of the text is suitable for the tempo {target_wpm} WPM 
    4.The lenght of the video should be 30-50 SECONDS !!! it is around 130 to 190 words
    5.Make the words sentences flow
    6.There is no Host or Guest. Only 1 person is going to speak

    I don't need no bullshit, give me ONLY the script
    Structure of the answer:
    Full rewritten script, while following the structute of the input while 

    YOUR PREVIOUS HITS (Mimic this vibe/structure):
    {references}
    """
    
    user_prompt = f"""
    TOPIC: {topic}
    
    MY DRAFT / NOTES:
    "{draft}"
    
    ACTION: Rewrite this into a viral script. Make the Hook (first 3s) impossible to ignore.
    """

    # sending the request
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", # Очень быстрая и умная
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.8, # Чуть выше креативность
            ),
            contents=[user_prompt]
        )
        
        if response.text:
            return response.text, references
        else:
            return "Google вернул пустой ответ (возможно, сработал фильтр безопасности).", references
            
    except Exception as e:
        return f"Ошибка при запросе к Google Gemini: {e}", references