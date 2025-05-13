import tkinter as tk
from tkinter import scrolledtext, Menu, filedialog
import re

class CodeEditor(tk.Tk):
    def __init__(self):
        super().__init__()  # Инициализация родительского класса Tk
        self.title("NotePy v1.0.0-beta")  # Установка заголовка окна
        self.geometry("800x600")  # Установка размера окна

        # Создание области текста с прокруткой и включением функции отмены
        self.text_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, undo=True, bg="#2F4F4F")
        self.text_area.pack(expand=True, fill='both')  # Заполнение доступного пространства

        # Привязка события нажатия клавиши для подсветки синтаксиса
        self.text_area.bind("<KeyRelease>", self.highlight_syntax)

        # Создание меню
        self.menu = Menu(self)
        self.config(menu=self.menu)

        # Создание подменю "Файл"
        self.file_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Файл", menu=self.file_menu)
        self.file_menu.add_command(label="Открыть", command=self.open_file)  # Команда открытия файла
        self.file_menu.add_command(label="Сохранить", command=self.save_file)  # Команда сохранения файла
        self.file_menu.add_separator()  # Разделитель в меню
        self.file_menu.add_command(label="Выйти", command=self.quit)  # Команда выхода

        # Создание подменю "Прочее"
        self.file_menu = Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Прочее", menu=self.file_menu)
        self.file_menu.add_command(label="О программе", command=self.open_oProgram)

        # Создание контекстного меню
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Копировать", command=self.copy_text)
        self.context_menu.add_command(label="Вставить", command=self.paste_text)

        # Привязка контекстного меню к текстовому полю
        self.text_area.bind("<Button-2>", self.show_context_menu)  # Для правой кнопки мыши
        self.text_area.bind("<Control-Button-1>", self.show_context_menu)  # Для Ctrl + ЛКМ (если нужно)


        # Инициализация тегов для подсветки синтаксиса
        self.init_tags()

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def copy_text(self):
        self.text_area.event_generate("<<Copy>>")

    def paste_text(self):
        self.text_area.event_generate("<<Paste>>")

    def open_oProgram(self):
        # Создание окна "О программе"
        non_modal_window = tk.Toplevel(self)
        non_modal_window.title("О программе...")
        non_modal_window.geometry("500x200")

        # Добавление метки в немодальное окно
        BigText = ''' 
Добро пожаловать в наш редактор кода для Python!
Этот простой и удобный инструмент предлагает 
подсветку синтаксиса, что делает ваш код более 
читаемым, а также встроенный справочник по Python 
для быстрого доступа к необходимой информации.

Надеемся, что наш редактор поможет вам в программировании!'''
        label = tk.Label(non_modal_window, text=BigText, justify='left')
        label.pack(pady=10)

        # Кнопка для закрытия немодального окна
        close_button = tk.Button(non_modal_window, text="Закрыть", command=non_modal_window.destroy)
        close_button.pack(pady=10)

    def init_tags(self):
        # Настройка тегов для подсветки синтаксиса
        self.text_area.tag_configure("keyword", foreground="#00FFFF")  # Ключевые слова - синим
        self.text_area.tag_configure("string", foreground="#00FF00")  # Строки - зеленым
        self.text_area.tag_configure("comment", foreground="#C0C0C0")  # Комментарии - серым

    def highlight_syntax(self, event=None):
        # Удаление существующих тегов
        for tag in self.text_area.tag_names():
            self.text_area.tag_remove(tag, "1.0", tk.END)

        # Получение содержимого текстовой области
        content = self.text_area.get("1.0", tk.END)

        # Применение подсветки синтаксиса
        self.apply_highlighting(content)

    def apply_highlighting(self, content):
        # Определение регулярных выражений для ключевых слов, строк и комментариев
        keywords = r'\b(def|class|if|else|elif|for|while|return|import|from|as|with|try|except|finally|print|in|is|and|or|not)\b'
        strings = r'(\".*?\"|\'.*?\')'
        comments = r'(#.*?$)'

        # Применение тегов для ключевых слов
        for match in re.finditer(keywords, content, re.MULTILINE):
            self.text_area.tag_add("keyword", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

        # Применение тегов для строк
        for match in re.finditer(strings, content):
            self.text_area.tag_add("string", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

        # Применение тегов для комментариев
        for match in re.finditer(comments, content, re.MULTILINE):
            self.text_area.tag_add("comment", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

    def open_file(self):
        # Открытие диалогового окна для выбора файла
        file_path = filedialog.askopenfilename()
        if file_path:
            with open(file_path, 'r') as file:
                self.text_area.delete("1.0", tk.END)  # Очистка текстовой области
                self.text_area.insert("1.0", file.read())  # Вставка содержимого файла
                self.highlight_syntax()  # Подсветка синтаксиса после загрузки файла

    def save_file(self):
        # Открытие диалогового окна для сохранения файла
        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files", "*.py")])
        if file_path:
            with open(file_path, 'w') as file:
                file.write(self.text_area.get("1.0", tk.END)) 

if __name__ == "__main__":
    # Создание экземпляра редактора кода и запуск главного цикла приложения
    editor = CodeEditor()
    editor.mainloop()  # Запуск основного цикла обработки событий

# Стабильная версия
