import os
import re
import mammoth

INPUT_DIR = "./input_docx"       
DATABASE_DIR = "./minprom_docs"  

def setup_folders():
    for folder in [INPUT_DIR, DATABASE_DIR]:
        if not os.path.exists(folder):
            os.makedirs(folder)

def clean_and_format_markdown(raw_html_markdown):
    # 1. Сразу убираем мусорные косые черты и экранирование от Консультанта
    text = re.sub(r'\\\s*', ' ', raw_html_markdown)
    text = re.sub(r'\\', '', text)
    
    # 2. Ищем маркер разрыва первой страницы, который ставит mammoth
    # Обычно это горизонтальная линия <hr ... /> или специальный тег разрыва
    page_break_match = re.search(r'<hr\s+[^>]*id="docx-pb"[^>]*>', text)
    
    if page_break_match:
        # Разрезаем текст ровно по границе первой страницы
        split_index = page_break_match.start()
        first_page_text = text[:split_index]
        remaining_text = text[split_index:]
    else:
        # Если разрыв не найден (редкий случай), по дефолту берем первые 10 строк
        lines = text.split('\n')
        first_page_text = "\n".join(lines[:10])
        remaining_text = "\n".join(lines[10:])
        
    # 3. Очищаем текст первой страницы, убираем переносы строк и лишние пробелы
    clean_title = first_page_text.replace('\n', ' ').strip()
    clean_title = re.sub(r'\s+', ' ', clean_title) # убираем двойные пробелы
    
    # Убираем возможные остаточные HTML теги из заголовка, если они проскочили
    clean_title = re.sub(r'<[^>]+>', '', clean_title)
    
    # Собираем финальный документ: Шапка # + оставшийся текст НПА
    final_markdown = f"# {clean_title}\n\n{remaining_text}"
    
    # Очищаем документ от самого тега разрыва, чтобы он не мозолил глаза в .md
    final_markdown = re.sub(r'<hr\s+[^>]*id="docx-pb"[^>]*>', '\n---\n', final_markdown)
    
    return final_markdown

def process_npa_pipeline():
    setup_folders()
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.docx') and not f.startswith('~$')]
    
    if not files:
        print("В папке 'input_docx' нет новых файлов для конвертации.")
        return
    
    for filename in files:
        docx_path = os.path.join(INPUT_DIR, filename)
        md_filename = filename.replace('.docx', '.md')
        md_path = os.path.join(DATABASE_DIR, md_filename)
        
        print(f"🔄 Конвертация первой страницы в супер-заголовок: {filename}...")
        
        try:
            with open(docx_path, "rb") as docx_file:
                # Конвертируем Word
                result = mammoth.convert_to_markdown(docx_file)
                raw_markdown = result.value
                
                # Запускаем нашу тотальную склейку первой страницы
                perfect_markdown = clean_and_format_markdown(raw_markdown)
                
                with open(md_path, "w", encoding="utf-8") as md_file:
                    md_file.write(perfect_markdown)
            
            os.remove(docx_path)
            print(f"✅ Документ {md_filename} успешно упакован! Первая страница стала заголовком.")
            
        except Exception as e:
            print(f"❌ Ошибка при конвертации файла {filename}: {e}")

if __name__ == "__main__":
    process_npa_pipeline()
