import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import generativeai as genai
from google.generativeai import types

app = FastAPI()

# 🔐 Читаем скрытый ключ напрямую из защищенной памяти сервера Vercel
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

MINPROM_CACHE = None

class QueryModel(BaseModel):
    text: str

@app.on_event("startup")
def startup_event():
    global MINPROM_CACHE
    try:
        print("Загрузка базы НПА 'Башкирского Шэньчжэня' из папки minprom_docs...")
        documents_text = ""
        folder_path = "./minprom_docs"
        
        # Автоматически собираем все переведенные скриптом .md файлы в один массив
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith(".md"):
                    with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                        documents_text += f"\n\n=== {filename} ===\n" + f.read()
        
        if not documents_text:
            print("ВНИМАНИЕ: Папка minprom_docs пуста или не найдена!")
            documents_text = "Тестовая заглушка: База данных НПА Минпрома РБ пуста."

        # Создаем официальный Context Cache на серверах Google на 3 часа
        MINPROM_CACHE = genai.caching.CachedContent.create(
            model='models/gemini-3.7-flash', # Новейшая Gemini 3.7 Flash!
            display_name='bashkir_shenzhen_cached_base',
            contents=[documents_text],
            config=types.CreateCachedContentOptions(ttl=time.Duration(seconds=10800))
        )
        print("🚀 Контекстный кэш 'Башкирского Шэньчжэня' успешно активирован в Google!")
    except Exception as e:
        print(f"❌ Ошибка инициализации кэша: {e}")

# Красивый интерфейс чата с фиолетовым неоновым вайбом
@app.get("/", response_class=HTMLResponse)
def get_interface():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Башкирский Шэньчжэнь</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #121212; color: #e0e0e0; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
            .chat-container { width: 100%; max-width: 800px; background: #1e1e1e; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); padding: 20px; box-sizing: border-box; margin-top: 40px; }
            h2 { color: #bb86fc; text-align: center; margin-top: 0; font-weight: 600; }
            #chat-box { height: 450px; overflow-y: auto; border: 1px solid #333; background: #181818; padding: 15px; border-radius: 8px; margin-bottom: 15px; white-space: pre-wrap; font-size: 15px; line-height: 1.6; }
            .input-area { display: flex; gap: 10px; }
            textarea { flex: 1; background: #2d2d2d; color: #fff; border: 1px solid #444; border-radius: 6px; padding: 10px; resize: none; height: 50px; font-family: inherit; font-size: 14px; }
            button { background: #bb86fc; color: #121212; border: none; border-radius: 6px; padding: 0 25px; font-weight: bold; cursor: pointer; transition: 0.2s; font-size: 14px; }
            button:hover { background: #9965db; }
            .user-msg { color: #03dac6; margin-bottom: 10px; font-weight: bold; }
            .ai-msg { color: #e0e0e0; margin-bottom: 20px; background: #252525; padding: 15px; border-radius: 6px; border-left: 4px solid #bb86fc; }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <h2>🇨🇳 Башкирский Шэньчжэнь v1.0 🤖</h2>
            <div id="chat-box"></div>
            <div class="input-area">
                <textarea id="user-input" placeholder="Спроси Промышленника про НПА, отборы или Постановление 1780..."></textarea>
                <button onclick="sendQuery()">Спросить</button>
            </div>
        </div>
        <script>
            async function sendQuery() {
                const inputEl = document.getElementById('user-input');
                const chatBox = document.getElementById('chat-box');
                const text = inputEl.value.trim();
                if (!text) return;
                
                chatBox.innerHTML += `<div class='user-msg'>👤 Я: ${text}</div>`;
                inputEl.value = '';
                chatBox.scrollTop = chatBox.scrollHeight;
                
                try {
                    const response = await fetch('/ask', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: text })
                    });
                    const data = await response.json();
                    chatBox.innerHTML += `<div class='ai-msg'>🤖 <b>Добрый Башкирский Шэньчжэнь:</b><br>${data.answer}</div>`;
                } catch (err) {
                    chatBox.innerHTML += `<div class='ai-msg' style='color:#cf6679'>Ошибка вызова модели. Проверьте лимиты или логи Vercel.</div>`;
                }
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        </script>
    </body>
    </html>
    """

@app.post("/ask")
def ask_ai(query: QueryModel):
    global MINPROM_CACHE
    if not MINPROM_CACHE:
        raise HTTPException(status_code=500, detail="Контекстный кэш нормативной базы не активен на сервере.")
        
    try:
        model = genai.GenerativeModel(model_name='models/gemini-3.7-flash')
        
        # 🎯 Твой финальный обновленный промпт со скриншота один в один!
        system_instruction = (
            "You are \"Добрый Башкирский Шэньчжэнь\", a highly advanced AI assistant for the Ministry of Industry of the Republic of Bashkortostan.\n"
            "Your mission: Help businesses easily understand complex state support measures for establishing industrial and technoparks in Bashkortostan. Always speak in Russian.\n\n"
            "STRICT OPERATIONAL RULES:\n"
            "1. COMMUNICATION STYLE & MINIMALISM:\n"
            "Respond in a friendly, human, and understandable language on Russian. Avoid heavy bureaucracy, but maintain absolute legal precision. Format text with short paragraphs and clear Markdown lists.\n\n"
            "2. DATABASE RELIANCE & CITATION:\n"
            "- Your answers must be built EXCLUSIVELY on the provided context (cached content) of Russian Federation (RF) and Republic of Bashkortostan (RB) laws.\n"
            "- For ANY requirement, figure, or restriction, you MUST explicitly state the primary source in parentheses. Example: (ПП РФ № 794, пункт 3) or (Закон РБ №...).\n"
            "- Cross-reference federal and regional laws. Warn the user about overlapping restrictions (e.g., if one measure excludes another).\n\n"
            "3. ZERO HALLUCINATIONS:\n"
            "Strictly forbidden to invent facts, laws, dates, or numbers. If the data is missing, respond with the exact template:\n"
            "\"К сожалению, в моей базе данных эта информация отсутствует. Я передам этот вопрос разработчику, чтобы он добавил её.\"\n\n"
            "4. SUPER-LEARNING MODE (TRIGGER \"банановый кексик\"):\n"
            "- When the user types the secret phrase \"банановый кексик\", switch to real-time information recording. Treat all text following this phrase as a critical system instruction or newly approved fact.\n"
            "- Confirm recording by replying: \"Октябрьский Промышленник всё запомнил!\". Use this new knowledge for all subsequent answers in the current session.\n"
            "- DEVELOPER TECHNICAL LOG: At the very end of your response to the trigger phrase, print a hidden line: СЕЙВ_ДАТА: [text after keksik]."
        )

        response = model.generate_content(
            [query.text],
            cached_content=MINPROM_CACHE,
            generation_config=genai.GenerationConfig(
                system_instruction=system_instruction, 
                temperature=0.1,
                max_output_tokens=8192
            )
        )
        return {"answer": response.candidates[0].content.parts[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
