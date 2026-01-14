import os
import cv2
import pandas as pd
import whisper
import datetime
from moviepy import VideoFileClip
from pathlib import Path
from src.utils.config import RAW_VIDEOS_DIR, LOCAL_DATA_FILE, WHISPER_MODEL_SIZE

def get_file_date(filepath):
    """
    Получает дату ПОСЛЕДНЕГО ИЗМЕНЕНИЯ файла.
    Для видео это обычно дата рендера.
    """
    try:
        # Используем pathlib stat (надежнее для Windows)
        timestamp = filepath.stat().st_mtime
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    except Exception as e:
        print(f"⚠️ Не удалось получить дату для {filepath.name}: {e}")
        return None

def extract_visual_brightness(video_path):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return 0
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return 0
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return round(hsv[..., 2].mean(), 2)

def run_local_analysis():
    print(f"📂 Сканирование папки: {RAW_VIDEOS_DIR}")
    
    # Загружаем модель
    print(f"⏳ Загрузка Whisper ({WHISPER_MODEL_SIZE})...")
    model = whisper.load_model(WHISPER_MODEL_SIZE)
    
    data = []
    
    # Ищем файлы через pathlib (это важно для корректной работы путей Windows)
    # Если RAW_VIDEOS_DIR это строка, превращаем в Path
    folder_path = Path(RAW_VIDEOS_DIR)
    files = list(folder_path.glob("*.mp4"))
    
    total = len(files)
    print(f"Найдено видео: {total}. Начинаем анализ...")

    for i, filepath in enumerate(files):
        filename = filepath.name
        
        try:
            # 1. Дата (Теперь с выводом в консоль для проверки)
            file_date = get_file_date(filepath)
            
            # 2. Длительность
            clip = VideoFileClip(str(filepath))
            duration = clip.duration
            clip.close()

            # 3. Яркость
            brightness = extract_visual_brightness(filepath)

            # 4. Транскрипция
            # Если не хотите ждать снова 30 мин, и у вас есть старый CSV с текстом,
            # можно написать логику подгрузки текста оттуда. Но для чистоты лучше прогнать.
            result = model.transcribe(str(filepath), fp16=False, task="translate")
            text = result["text"].strip()

            word_count = len(text.split())
            wpm = round(word_count / (duration / 60), 2) if duration > 0 else 0

            # Вывод лога, чтобы вы видели, что дата есть
            print(f"[{i+1}/{total}] {filename[:15]}... | 📅 {file_date} | ⏱ {wpm} WPM")

            data.append({
                "Filename": filename,
                "File_Creation_Date": file_date,
                "Duration_Sec": round(duration, 2),
                "Brightness": brightness,
                "Word_Count": word_count,
                "Words_per_Minute": wpm,
                "Transcription": text
            })

        except Exception as e:
            print(f"❌ Ошибка с {filename}: {e}")

    # Сохраняем
    df = pd.DataFrame(data)
    df.to_csv(LOCAL_DATA_FILE, index=False)
    print(f"✅ Локальный анализ завершен. Сохранено в: {LOCAL_DATA_FILE}")

if __name__ == "__main__":
    run_local_analysis()