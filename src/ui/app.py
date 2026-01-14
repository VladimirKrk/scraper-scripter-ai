import sys

PROJECT_ROOT = r"F:\code\projects\tiktok_analysis2"

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils.config import MERGED_DATA_FILE
from src.ai_engine.generator import ai_audit_script

#Run this command to start the app:
#streamlit run .\src\ui\app.py

# Настройка страницы
st.set_page_config(page_title="TikTok AI Studio", layout="wide", page_icon="🎬")

# --- ЗАГРУЗКА ДАННЫХ ---
@st.cache_data
def load_data():
    if MERGED_DATA_FILE.exists():
        df = pd.read_csv(MERGED_DATA_FILE)
        return df
    return None

df = load_data()

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.header("⚙️ Настройки Генератора")
target_wpm = st.sidebar.slider("Целевая скорость (WPM)", 120, 200, 155, help="Сколько слов в минуту должен читать диктор?")
power_words = st.sidebar.text_area("Power Words (Триггеры)", "secret, mistake, shocking, ufc, ko, prediction, wrong")

st.sidebar.divider()
st.sidebar.info("💡 Совет: Если база данных пустая, запустите main.py")

# --- ОСНОВНОЙ ЭКРАН ---
st.title("🎬 TikTok AI Studio")

tab1, tab2 = st.tabs(["📝 AI Сценарист", "📊 Аналитика Канала"])

# === ВКЛАДКА 1: ГЕНЕРАТОР ===
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Вводные данные")
        topic = st.text_input("Тема видео",placeholder="Например: Islam Makhachev vs Arman Tsarukyan prediction")
        
        draft = st.text_area("Ваш черновик (или оставьте пустым для генерации с нуля)", height=300, 
                             placeholder="Вставьте сюда свой текст, и ИИ его отредактирует...")
        
        generate_btn = st.button("🚀 Запустить AI", type="primary", use_container_width=True)

    with col2:
        st.subheader("Результат")
        if generate_btn:
            if not topic:
                st.error("Пожалуйста, укажите тему видео!")
            else:
                with st.spinner("ИИ анализирует прошлые хиты и пишет текст..."):
                    # Вызов нашей функции из src
                    try:
                        result_text, refs = ai_audit_script(draft, topic, target_wpm, power_words)
                        
                        st.success("Готово!")
                        st.markdown(f"### 🤖 Сценарий:\n{result_text}")
                        st.divider()
                        with st.expander("📚 Использованные референсы (RAG Context)"):
                            st.text(refs)
                    except Exception as e:
                        st.error(f"Ошибка ИИ: {e}. Убедитесь, что AI запущена!")

# === ВКЛАДКА 2: АНАЛИТИКА ===
with tab2:
    if df is not None:
        # Метрики сверху
        top_videos = df.nlargest(10, 'Views')
        avg_wpm = top_videos['Words_per_Minute'].mean()
        avg_views = df['Views'].mean()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Всего видео", len(df))
        m2.metric("Средний WPM (Топ-10)", f"{avg_wpm:.1f}")
        m3.metric("Средние просмотры", f"{int(avg_views):,}")
        
        st.divider()
        
        # График 1: Scatter Plot (WPM vs Views)
        st.subheader("Влияет ли скорость речи на просмотры?")
        fig = px.scatter(
            df, 
            x="Words_per_Minute", 
            y="Views", 
            size="Likes", 
            color="Brightness", 
            hover_data=["Filename"],
            title="Каждая точка - это видео. Размер = Лайки.",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Таблица Топ видео
        st.subheader("🏆 Топ-10 Лучших видео")
        st.dataframe(top_videos[['Filename', 'Views', 'Likes', 'Words_per_Minute', 'Upload_Date']], use_container_width=True)
        
    else:
        st.warning("Файл данных не найден. Запустите main.py!")