import tkinter as tk
from tkinter import scrolledtext, Menu, filedialog, messagebox, simpledialog
import re
import os
import subprocess

class CodeEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NotePy v1.1 — редактор с номерами строк")
        self.geometry("1000x700")
        self.current_file = None

        # Основной фрейм
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)

        # Номера строк (Canvas)
        self.linenumbers = tk.Canvas(self.main_frame, width=50, bg="#2d2d2d", highlightthickness=0)
        self.linenumbers.pack(side="left", fill="y")

        # Текстовое поле
        self.text_area = scrolledtext.ScrolledText(
            self.main_frame,
            wrap=tk.NONE,
            undo=True,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            font=("Consolas", 12),
            # tabs убрали из конструктора
        )
        self.text_area.pack(side="left", fill="both", expand=True)

        # Настраиваем табуляцию = ширина 4 пробелов
        self.set_tab_width()

        # Синхронизация прокрутки
        self.text_area.bind("<MouseWheel>", self.sync_scroll)
        self.text_area.bind("<Button-4>", self.sync_scroll)   # Linux up
        self.text_area.bind("<Button-5>", self.sync_scroll)   # Linux down
        self.text_area.bind("<Configure>", lambda e: self.update_linenumbers())
        self.text_area.bind("<KeyRelease>", self.on_key_release)

        # Статус-бар
        self.status = tk.Label(self, text="Строка: 1   Столбец: 1   |   UTF-8",
                               anchor="w", bg="#007acc", fg="white", font=("Segoe UI", 9))
        self.status.pack(side="bottom", fill="x")

        # Привязки
        self.text_area.bind("<KeyRelease>", self.update_status)
        self.text_area.bind("<ButtonRelease-1>", self.update_status)
        self.text_area.bind("<Return>", self.auto_indent)
        self.bind("<Control-f>", lambda e: self.find_text())
        self.bind("<Control-h>", lambda e: self.replace_text())
        self.bind("<F5>", lambda e: self.run_code())

        self.init_syntax_tags()
        self.create_menu()

        # Начальное обновление
        self.update_linenumbers()
        self.update_status()

    def set_tab_width(self):
        """Устанавливаем табуляцию равной ширине 4 пробелов в текущем шрифте"""
        try:
            # Измеряем ширину строки из 4 пробелов в пикселях
            width_4spaces = self.text_area.tk.call(
                "font", "measure", self.text_area.cget("font"), "    "
            )
            self.text_area.configure(tabs=(width_4spaces,))
        except:
            # Если по какой-то причине не получилось — оставляем стандартные 8
            pass

    def create_menu(self):
        menubar = Menu(self)
        self.config(menu=menubar)

        filemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=filemenu)
        filemenu.add_command(label="Открыть...", command=self.open_file, accelerator="Ctrl+O")
        filemenu.add_command(label="Сохранить", command=self.save_file, accelerator="Ctrl+S")
        filemenu.add_command(label="Сохранить как...", command=self.save_as_file)
        filemenu.add_separator()
        filemenu.add_command(label="Выход", command=self.quit)

        editmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=editmenu)
        editmenu.add_command(label="Найти...", command=self.find_text, accelerator="Ctrl+F")
        editmenu.add_command(label="Заменить...", command=self.replace_text, accelerator="Ctrl+H")

        runmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Запуск", menu=runmenu)
        runmenu.add_command(label="Запустить (F5)", command=self.run_code)

        helpmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="?", menu=helpmenu)
        helpmenu.add_command(label="О программе", command=self.show_about)

    def init_syntax_tags(self):
        self.text_area.tag_configure("keyword", foreground="#ff79c6")
        self.text_area.tag_configure("builtin",  foreground="#8be9fd")
        self.text_area.tag_configure("string",   foreground="#50fa7b")
        self.text_area.tag_configure("comment",  foreground="#6272a4")
        self.text_area.tag_configure("number",   foreground="#bd93f9")
        self.text_area.tag_configure("self",     foreground="#ffb86c")

    def highlight_syntax(self):
        for tag in ("keyword", "builtin", "string", "comment", "number", "self"):
            self.text_area.tag_remove(tag, "1.0", tk.END)

        content = self.text_area.get("1.0", "end-1c")

        patterns = [
            (r'\b(def|class|if|else|elif|for|while|return|import|from|as|with|try|except|finally|break|continue|pass|lambda|async|await|yield|global|nonlocal|assert|del|raise|True|False|None|and|or|not|in|is)\b', "keyword"),
            (r'\bself\b', "self"),
            (r'\b\d+(\.\d+)?\b', "number"),
            (r'\b(print|len|str|int|float|list|dict|tuple|set|range|open|input|type|isinstance|super)\b', "builtin"),
            (r'(\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'|".*?"|\'.*?\')', "string", re.DOTALL),
            (r'#.*?$', "comment", re.MULTILINE),
        ]

        for pattern, tag, *flags in patterns:
            flags = flags[0] if flags else 0
            for m in re.finditer(pattern, content, flags):
                start = f"1.0 + {m.start()} chars"
                end   = f"1.0 + {m.end()} chars"
                self.text_area.tag_add(tag, start, end)

    def update_linenumbers(self):
        self.linenumbers.delete("all")
        first = self.text_area.index("@0,0")
        last  = self.text_area.index("@0," + str(self.text_area.winfo_height()))

        line_start = int(first.split('.')[0])
        while True:
            dlineinfo = self.text_area.dlineinfo(f"{line_start}.0")
            if not dlineinfo:
                break
            y = dlineinfo[1]
            self.linenumbers.create_text(
                48, y, anchor="ne",
                text=str(line_start),
                font=("Consolas", 11), fill="#858585"
            )
            line_start += 1

    def sync_scroll(self, event=None):
        self.update_linenumbers()

    def on_key_release(self, event=None):
        self.highlight_syntax()
        self.update_linenumbers()
        self.update_status()

    def update_status(self, event=None):
        try:
            idx = self.text_area.index("insert")
            line, col = map(int, idx.split("."))
            filename = os.path.basename(self.current_file) if self.current_file else "Без имени"
            self.status.config(text=f"Строка: {line}   Столбец: {col+1}   |   {filename}")
        except:
            pass

    def auto_indent(self, event):
        line_start = self.text_area.index("insert linestart")
        line_text = self.text_area.get(line_start, "insert")

        indent = len(line_text) - len(line_text.lstrip())
        if line_text.strip().endswith(":"):
            indent += 4

        self.text_area.insert("insert", "\n" + " " * indent)
        return "break"

    def find_text(self):
        search = simpledialog.askstring("Найти", "Что ищем?")
        if not search:
            return
        self.text_area.tag_remove("search", "1.0", tk.END)
        start = "1.0"
        while True:
            pos = self.text_area.search(search, start, stopindex=tk.END, nocase=True)
            if not pos: break
            end = f"{pos}+{len(search)}c"
            self.text_area.tag_add("search", pos, end)
            start = end
        self.text_area.tag_config("search", background="#ffff99", foreground="black")

    def replace_text(self):
        find_str = simpledialog.askstring("Заменить", "Найти:")
        if not find_str: return
        replace_str = simpledialog.askstring("Заменить", "Заменить на:")
        if replace_str is None: return

        content = self.text_area.get("1.0", tk.END)
        new_content = content.replace(find_str, replace_str)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", new_content)
        self.highlight_syntax()
        self.update_linenumbers()

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Python", "*.py *.pyw"), ("Все файлы", "*.*")])
        if not path: return
        try:
            with open(path, encoding="utf-8") as f:
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", f.read())
            self.current_file = path
            self.title(f"NotePy — {os.path.basename(path)}")
            self.highlight_syntax()
            self.update_linenumbers()
            self.update_status()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл\n{e}")

    def save_file(self):
        if not self.current_file:
            return self.save_as_file()
        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.text_area.get("1.0", "end-1c"))
            messagebox.showinfo("Сохранено", "Файл успешно сохранён")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить\n{e}")

    def save_as_file(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python", "*.py"), ("Все файлы", "*.*")]
        )
        if not path: return
        self.current_file = path
        self.title(f"NotePy — {os.path.basename(path)}")
        self.save_file()

    def run_code(self):
        if not self.current_file:
            messagebox.showwarning("Запуск", "Сначала сохраните файл!")
            return
        try:
            subprocess.Popen(["python", self.current_file])
        except Exception as e:
            messagebox.showerror("Ошибка запуска", str(e))

    def show_about(self):
        messagebox.showinfo("О программе", "NotePy v1.1\nПростой редактор кода на Tkinter\n\n• номера строк\n• подсветка\n• автоотступы\n• поиск / замена\n• запуск F5")

if __name__ == "__main__":
    app = CodeEditor()
    app.mainloop()
