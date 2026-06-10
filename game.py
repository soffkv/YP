import tkinter as tk
from tkinter import messagebox
import random
import os
import sys

# ФУНКЦИЯ ДЛЯ ПОИСКА ФАЙЛА
def get_resource_path(filename):
    """Возвращает путь к файлу (работает и в собранном exe)"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

# ЗАГРУЗКА СЛОВАРЯ
def load_words(filename="words.txt"):
    """Загружает слова из текстового файла (по одному слову в строке)"""
    filepath = get_resource_path(filename)
    
    if not os.path.exists(filepath):
        messagebox.showerror(
            "Ошибка", 
            f"Файл {filename} не найден!\n\nИскали по пути:\n{filepath}\n\n"
            "Создайте файл words.txt в папке с программой\n"
            "и добавьте в него слова из 5 букв (по одному на строку)."
        )
        return []
    
    words = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip().upper()
                if len(word) == 5 and word.isalpha():
                    words.append(word)
        
        if not words:
            messagebox.showerror(
                "Ошибка", 
                f"Файл {filename} не содержит слов из 5 букв!\n\n"
                "Добавьте в него слова из 5 букв (по одному на строку)."
            )
            return []
        
        return words
        
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось прочитать файл {filepath}:\n{e}")
        return []

#  СОХРАНЕНИЕ СЛОВА В СЛОВАРЬ
def save_word_to_file(word):
    """Сохраняет новое слово в файл словаря"""
    filepath = get_resource_path("words.txt")
    
    # Проверяем длину слова
    if len(word) != 5 or not word.isalpha():
        return False, "Слово должно состоять из 5 букв!"
    
    # Проверяем, не существует ли уже слово
    existing_words = load_words("words.txt")
    if word.upper() in existing_words:
        return False, "Это слово уже есть в словаре!"
    
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(f"{word.upper()}\n")
        return True, "Слово успешно добавлено в словарь!"
    except Exception as e:
        return False, f"Ошибка при сохранении: {e}"

# ФУНКЦИЯ ДЛЯ СОЗДАНИЯ СКРУГЛЁННОЙ РАМКИ 
def _create_rounded_rect(self, x1, y1, x2, y2, radius=30, **kwargs):
    """Создаёт прямоугольник с сильно скруглёнными углами"""
    width = x2 - x1
    height = y2 - y1
    max_radius = min(width, height) // 2
    radius = min(radius, max_radius)
    
    points = []
    for x, y in [
        (x1+radius, y1), (x2-radius, y1),
        (x2, y1), (x2, y1+radius),
        (x2, y2-radius), (x2, y2),
        (x2-radius, y2), (x1+radius, y2),
        (x1, y2), (x1, y2-radius),
        (x1, y1+radius), (x1, y1)
    ]:
        points.append(x)
        points.append(y)
    return self.create_polygon(points, smooth=True, **kwargs)

tk.Canvas.create_rounded_rect = _create_rounded_rect

MAX_ATTEMPTS = 6
WORD_LEN = 5

# Цвета
FIRST_BG = "#F9D0D0"      # Фон первого окна (нежно-персиковый)
SECOND_BG = "#FFCCE9"     # Фон второго окна (нежно-розовый)
CELL_KEY_BG = "#F9D0D0"   # Фон ячеек и кнопок клавиатуры (нежно-персиковый)
CARD_BG = "#FFD1E8"       # Фон карточки правил и кнопки (максимально нежно-розовый)
BUTTON_HOVER = "#FFC0D8"  # Цвет кнопки при наведении

class WordleGame:
    def __init__(self, root):
        self.root = root
        self.root.title("5 букв")
        self.root.geometry("750x700")
        self.root.configure(bg=FIRST_BG)
        self.root.minsize(500, 500)
        
        # Привязка клавиши ESC для закрытия игры
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        self.WORDS = load_words("words.txt")
        
        if not self.WORDS:
            self.show_error_and_exit()
            return
        
        self.current_attempt = 0
        self.game_over = False
        self.target_word = random.choice(self.WORDS)
        self.guesses = [""] * MAX_ATTEMPTS
        self.valid_words = set(self.WORDS)
        self.key_buttons = {}
        self.cell_frames = []
        self.key_frames = {}
        self.current_screen = "start"
        self.waiting_for_word_add = False  # Флаг ожидания добавления слова
        
        self.create_start_screen()
        
        # Привязка события изменения размера окна
        self.root.bind("<Configure>", self.on_window_resize)
    
    def reload_words(self):
        """Перезагружает словарь из файла"""
        self.WORDS = load_words("words.txt")
        if self.WORDS:
            self.valid_words = set(self.WORDS)
            return True
        return False
    
    def on_window_resize(self, event):
        """Обработчик изменения размера окна"""
        if event.widget == self.root:
            if self.current_screen == "start":
                self.create_start_screen()
            elif self.current_screen == "game":
                self.create_game_screen()
            elif self.current_screen == "win":
                self.show_win_screen()
            elif self.current_screen == "lose":
                self.show_lose_screen()
    
    def show_error_and_exit(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        error_frame = tk.Frame(self.root, bg=FIRST_BG)
        error_frame.pack(expand=True, fill="both")
        
        error_label = tk.Label(
            error_frame,
            text="ОШИБКА!\n\nФайл words.txt не найден или пуст.\n\nСоздайте файл words.txt в папке с программой\nи добавьте в него слова из 5 букв\n(по одному на строку).",
            font=("Arial", 14, "normal"),
            bg=FIRST_BG,
            fg="#2C3E50",
            justify="center"
        )
        error_label.pack(expand=True)
        
        exit_btn = tk.Button(
            error_frame,
            text="Выход",
            font=("Arial", 14, "normal"),
            bg=CARD_BG,
            fg="#2C3E50",
            cursor="hand2",
            padx=40,
            pady=12,
            relief="flat",
            command=self.root.quit
        )
        exit_btn.pack(pady=20)
        
        self.root.bind("<Escape>", lambda e: self.root.quit())
    
    def create_start_screen(self):
        self.current_screen = "start"
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg=FIRST_BG)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Размеры окна
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Вычисляем размеры элементов пропорционально окну
        card_width = max(280, min(int(window_width * 0.45), window_width - 60))
        card_height = max(350, min(int(window_height * 0.65), window_height - 150))
        button_width = max(140, min(int(window_width * 0.22), window_width - 100))
        button_height = max(45, int(window_height * 0.07))
        font_size_text = max(10, min(13, int(window_width * 0.014)))
        button_font_size = max(11, min(14, int(window_width * 0.016)))
        radius = max(20, int(min(card_width, card_height) * 0.07))
        
        main_frame = tk.Frame(self.root, bg=FIRST_BG)
        main_frame.pack(expand=True, fill="both")
        
        # Центральный контейнер
        center_container = tk.Frame(main_frame, bg=FIRST_BG)
        center_container.pack(expand=True)
        
        # Контейнер для карточки правил
        rules_container = tk.Frame(center_container, bg=FIRST_BG, width=card_width, height=card_height)
        rules_container.pack(pady=(max(10, int(window_height * 0.03)), max(10, int(window_height * 0.02))))
        rules_container.pack_propagate(False)
        
        # Карточка с правилами
        rules_canvas = tk.Canvas(rules_container, bg=FIRST_BG, highlightthickness=0)
        rules_canvas.pack(fill="both", expand=True)
        
        # Скруглённый прямоугольник
        rules_canvas.create_rounded_rect(5, 5, card_width-5, card_height-5, radius=radius, fill=CARD_BG, outline="black", width=2)
        
        rules_text = """Правила игры:

Цель: угадать загаданное слово из 5 букв

У вас есть 6 попыток

После каждой попытки буквы подсвечиваются:

- Зелёный - буква на своём месте
- Жёлтый - буква есть в слове, но не здесь
- Серый - такой буквы нет в слове

Если ввести слово с двумя одинаковыми буквами, а в загаданном слове только одна такая буква, зеленым или желтым подсветится только одна из повторяющихся букв, стоящая ближе к правильному месту."""
        
        rules_label = tk.Label(
            rules_canvas,
            text=rules_text,
            font=("Arial", font_size_text, "normal"),
            bg=CARD_BG,
            fg="black",
            justify="left",
            anchor="nw",
            wraplength=card_width - 50
        )
        rules_label.place(x=max(15, int(card_width * 0.05)), y=max(15, int(card_height * 0.05)))
        
        # Кнопка "Начать игру"
        button_container = tk.Frame(center_container, bg=FIRST_BG, width=button_width, height=button_height)
        button_container.pack(pady=(max(5, int(window_height * 0.01)), max(20, int(window_height * 0.03))))
        button_container.pack_propagate(False)
        
        start_canvas = tk.Canvas(button_container, bg=FIRST_BG, highlightthickness=0)
        start_canvas.pack(fill="both", expand=True)
        
        start_rect = start_canvas.create_rounded_rect(5, 5, button_width-5, button_height-5, radius=max(15, int(radius * 0.8)), fill=CARD_BG, outline="black", width=2)
        start_text = start_canvas.create_text(button_width//2, button_height//2, text="Начать игру", font=("Arial", button_font_size, "normal"), fill="black")
        
        def start_handler(e=None):
            self.start_game()
        
        def on_enter(e=None):
            start_canvas.itemconfig(start_rect, fill=BUTTON_HOVER)
        
        def on_leave(e=None):
            start_canvas.itemconfig(start_rect, fill=CARD_BG)
        
        start_canvas.tag_bind(start_rect, "<Button-1>", start_handler)
        start_canvas.tag_bind(start_text, "<Button-1>", start_handler)
        start_canvas.tag_bind(start_rect, "<Enter>", on_enter)
        start_canvas.tag_bind(start_rect, "<Leave>", on_leave)
        start_canvas.tag_bind(start_text, "<Enter>", on_enter)
        start_canvas.tag_bind(start_text, "<Leave>", on_leave)
        start_canvas.config(cursor="hand2")
    
    def start_game(self):
        self.current_attempt = 0
        self.game_over = False
        self.waiting_for_word_add = False
        self.target_word = random.choice(self.WORDS)
        self.guesses = [""] * MAX_ATTEMPTS
        self.create_game_screen()
    
    def create_game_screen(self):
        self.current_screen = "game"
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg=SECOND_BG)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Получаем размеры окна
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Размер ячейки
        max_cell_size = min(window_width // (WORD_LEN + 3), window_height // (MAX_ATTEMPTS + 5))
        cell_size = max(40, min(75, max_cell_size))
        cell_padding = max(3, int(cell_size * 0.07))
        font_size = max(16, int(cell_size * 0.4))
        key_size = max(32, int(cell_size * 0.7))
        key_font_size = max(9, int(key_size * 0.28))
        key_padding = max(2, int(key_size * 0.04))
        radius = max(8, int(cell_size * 0.35))
        
        # Игровое поле
        self.cell_frames = []
        game_frame = tk.Frame(self.root, bg=SECOND_BG)
        game_frame.pack(expand=True, pady=max(10, int(window_height * 0.02)))
        
        for row in range(MAX_ATTEMPTS):
            row_frames = []
            for col in range(WORD_LEN):
                cell_frame = tk.Frame(game_frame, bg=SECOND_BG)
                cell_frame.grid(row=row, column=col, padx=cell_padding, pady=cell_padding)
                
                canvas = tk.Canvas(cell_frame, width=cell_size, height=cell_size, bg=SECOND_BG, highlightthickness=0)
                canvas.pack()
                
                rect = canvas.create_rounded_rect(3, 3, cell_size-3, cell_size-3, radius=radius, fill=CELL_KEY_BG, outline="black", width=2)
                text_id = canvas.create_text(cell_size//2, cell_size//2, text="", font=("Arial", font_size, "bold"), fill="#2C3E50")
                
                row_frames.append({"canvas": canvas, "rect": rect, "text": text_id})
            self.cell_frames.append(row_frames)
        
        self.create_keyboard(key_size, key_font_size, key_padding, radius)
        self.root.bind("<Key>", self.on_key_press)
        self.root.focus_set()
    
    def create_keyboard(self, key_size, key_font_size, key_padding, radius):
        # Основной контейнер для клавиатуры и кнопок
        keyboard_container = tk.Frame(self.root, bg=SECOND_BG)
        keyboard_container.pack(pady=max(5, int(key_size * 0.15)))
        
        # Левая часть - буквенная клавиатура
        keyboard_frame = tk.Frame(keyboard_container, bg=SECOND_BG)
        keyboard_frame.pack(side="left")
        
        rows = [
            ["Й", "Ц", "У", "К", "Е", "Н", "Г", "Ш", "Щ", "З", "Х", "Ъ"],
            ["Ф", "Ы", "В", "А", "П", "Р", "О", "Л", "Д", "Ж", "Э"],
            ["Я", "Ч", "С", "М", "И", "Т", "Ь", "Б", "Ю"]
        ]
        
        self.key_frames = {}
        key_radius = max(5, int(radius * 0.7))
        
        for r, row in enumerate(rows):
            row_frame = tk.Frame(keyboard_frame, bg=SECOND_BG)
            row_frame.pack(pady=key_padding)
            for letter in row:
                btn_frame = tk.Frame(row_frame, bg=SECOND_BG)
                btn_frame.pack(side="left", padx=key_padding, pady=key_padding)
                
                canvas = tk.Canvas(btn_frame, width=key_size, height=key_size, bg=SECOND_BG, highlightthickness=0)
                canvas.pack()
                
                rect = canvas.create_rounded_rect(3, 3, key_size-3, key_size-3, radius=key_radius, fill=CELL_KEY_BG, outline="black", width=2)
                text_id = canvas.create_text(key_size//2, key_size//2, text=letter, font=("Arial", key_font_size, "bold"), fill="#2C3E50")
                
                def make_handler(l=letter):
                    return lambda e=None: self.add_letter(l)
                
                def make_enter(c=canvas, r=rect):
                    return lambda e=None: c.itemconfig(r, fill="#f0b8d8")
                
                def make_leave(c=canvas, r=rect):
                    return lambda e=None: c.itemconfig(r, fill=CELL_KEY_BG)
                
                canvas.tag_bind(rect, "<Button-1>", make_handler())
                canvas.tag_bind(text_id, "<Button-1>", make_handler())
                canvas.tag_bind(rect, "<Enter>", make_enter())
                canvas.tag_bind(rect, "<Leave>", make_leave())
                canvas.tag_bind(text_id, "<Enter>", make_enter())
                canvas.tag_bind(text_id, "<Leave>", make_leave())
                canvas.config(cursor="hand2")
                
                self.key_frames[letter] = {"canvas": canvas, "rect": rect, "text": text_id}
        
        # Правая часть - кнопки Удалить и Ввод
        action_frame = tk.Frame(keyboard_container, bg=SECOND_BG)
        action_frame.pack(side="left", padx=(key_padding * 3, 0))
        
        btn_width = int(key_size * 2.0)
        btn_height = key_size
        btn_radius = key_radius
        
        # Кнопка Delete
        delete_frame = tk.Frame(action_frame, bg=SECOND_BG)
        delete_frame.pack(pady=(0, key_padding * 4))
        
        delete_canvas = tk.Canvas(delete_frame, width=btn_width, height=btn_height, bg=SECOND_BG, highlightthickness=0)
        delete_canvas.pack()
        delete_rect = delete_canvas.create_rounded_rect(3, 3, btn_width-3, btn_height-3, radius=btn_radius, fill=CELL_KEY_BG, outline="black", width=2)
        delete_text = delete_canvas.create_text(btn_width//2, btn_height//2, text="Удалить", font=("Arial", key_font_size, "bold"), fill="#2C3E50")
        
        def delete_handler(e=None):
            self.backspace()
        
        def delete_enter(e=None):
            delete_canvas.itemconfig(delete_rect, fill="#f0b8d8")
        
        def delete_leave(e=None):
            delete_canvas.itemconfig(delete_rect, fill=CELL_KEY_BG)
        
        delete_canvas.tag_bind(delete_rect, "<Button-1>", delete_handler)
        delete_canvas.tag_bind(delete_text, "<Button-1>", delete_handler)
        delete_canvas.tag_bind(delete_rect, "<Enter>", delete_enter)
        delete_canvas.tag_bind(delete_rect, "<Leave>", delete_leave)
        delete_canvas.tag_bind(delete_text, "<Enter>", delete_enter)
        delete_canvas.tag_bind(delete_text, "<Leave>", delete_leave)
        delete_canvas.config(cursor="hand2")
        
        # Кнопка Enter
        enter_frame = tk.Frame(action_frame, bg=SECOND_BG)
        enter_frame.pack(pady=(key_padding * 4, 0))
        
        enter_canvas = tk.Canvas(enter_frame, width=btn_width, height=btn_height, bg=SECOND_BG, highlightthickness=0)
        enter_canvas.pack()
        enter_rect = enter_canvas.create_rounded_rect(3, 3, btn_width-3, btn_height-3, radius=btn_radius, fill=CELL_KEY_BG, outline="black", width=2)
        enter_text = enter_canvas.create_text(btn_width//2, btn_height//2, text="Ввод", font=("Arial", key_font_size, "bold"), fill="#2C3E50")
        
        def enter_handler(e=None):
            self.submit_guess()
        
        def enter_enter(e=None):
            enter_canvas.itemconfig(enter_rect, fill="#f0b8d8")
        
        def enter_leave(e=None):
            enter_canvas.itemconfig(enter_rect, fill=CELL_KEY_BG)
        
        enter_canvas.tag_bind(enter_rect, "<Button-1>", enter_handler)
        enter_canvas.tag_bind(enter_text, "<Button-1>", enter_handler)
        enter_canvas.tag_bind(enter_rect, "<Enter>", enter_enter)
        enter_canvas.tag_bind(enter_rect, "<Leave>", enter_leave)
        enter_canvas.tag_bind(enter_text, "<Enter>", enter_enter)
        enter_canvas.tag_bind(enter_text, "<Leave>", enter_leave)
        enter_canvas.config(cursor="hand2")
    
    def update_cell_text(self, row, col, text):
        canvas_data = self.cell_frames[row][col]
        canvas_data["canvas"].itemconfig(canvas_data["text"], text=text)
    
    def update_cell_color(self, row, col, color):
        color_map = {
            "green": "#27AE60",
            "yellow": "#F39C12",
            "gray": "#95A5A6"
        }
        fill_color = color_map.get(color, CELL_KEY_BG)
        text_color = "white" if color != "gray" else "#2C3E50"
        
        canvas_data = self.cell_frames[row][col]
        canvas_data["canvas"].itemconfig(canvas_data["rect"], fill=fill_color)
        canvas_data["canvas"].itemconfig(canvas_data["text"], fill=text_color)
    
    def update_key_color(self, letter, color):
        if letter not in self.key_frames:
            return
        
        color_map = {
            "green": "#27AE60",
            "yellow": "#F39C12",
            "gray": "#95A5A6"
        }
        fill_color = color_map.get(color, CELL_KEY_BG)
        
        key_data = self.key_frames[letter]
        current_fill = key_data["canvas"].itemcget(key_data["rect"], "fill")
        
        if color == "green":
            key_data["canvas"].itemconfig(key_data["rect"], fill=fill_color)
            key_data["canvas"].itemconfig(key_data["text"], fill="white")
        elif color == "yellow" and current_fill != "#27AE60":
            key_data["canvas"].itemconfig(key_data["rect"], fill=fill_color)
            key_data["canvas"].itemconfig(key_data["text"], fill="white")
        elif color == "gray" and current_fill not in ["#27AE60", "#F39C12"]:
            key_data["canvas"].itemconfig(key_data["rect"], fill=fill_color)
            key_data["canvas"].itemconfig(key_data["text"], fill="white")
    
    def add_letter(self, letter):
        if self.game_over or self.waiting_for_word_add:
            return
        if len(self.guesses[self.current_attempt]) < WORD_LEN:
            self.guesses[self.current_attempt] += letter
            self.update_row_display()
    
    def backspace(self):
        if self.game_over or self.waiting_for_word_add:
            return
        if len(self.guesses[self.current_attempt]) > 0:
            self.guesses[self.current_attempt] = self.guesses[self.current_attempt][:-1]
            self.update_row_display()
    
    def update_row_display(self):
        guess = self.guesses[self.current_attempt]
        for col in range(WORD_LEN):
            if col < len(guess):
                self.update_cell_text(self.current_attempt, col, guess[col])
            else:
                self.update_cell_text(self.current_attempt, col, "")
    
    def submit_guess(self):
        if self.game_over or self.waiting_for_word_add:
            return
        
        guess = self.guesses[self.current_attempt]
        if len(guess) != WORD_LEN:
            messagebox.showwarning("Неполное слово", f"Введите слово из {WORD_LEN} букв!")
            # Очищаем текущую строку
            self.guesses[self.current_attempt] = ""
            self.update_row_display()
            self.root.focus_set()
            return
        
        if guess not in self.valid_words:
            # Запоминаем введённое слово
            new_word = guess
            
            # Спрашиваем, хочет ли игрок добавить слово
            answer = messagebox.askyesno(
                "Слова нет в словаре", 
                f"Слова '{new_word}' нет в словаре.\n\nХотите добавить его в словарь?\n\n(Слово должно состоять из 5 букв)"
            )
            
            if answer:
                # Проверяем длину слова
                if len(new_word) != 5 or not new_word.isalpha():
                    messagebox.showwarning("Ошибка", "Слово должно состоять из 5 букв!")
                    self.guesses[self.current_attempt] = ""
                    self.update_row_display()
                    self.root.focus_set()
                    return
                
                # Добавляем слово в словарь
                success, message = save_word_to_file(new_word)
                
                if success:
                    messagebox.showinfo("Успех", f"Слово '{new_word}' добавлено в словарь!")
                    # Перезагружаем словарь
                    self.reload_words()
                    # Обновляем guesses, чтобы слово осталось на поле
                    self.guesses[self.current_attempt] = new_word
                    self.update_row_display()
                    # Теперь проверяем это слово
                    self.check_guess(new_word)
                else:
                    messagebox.showerror("Ошибка", message)
                    self.guesses[self.current_attempt] = ""
                    self.update_row_display()
                    self.root.focus_set()
            else:
                # Игрок отказался добавлять слово
                self.guesses[self.current_attempt] = ""
                self.update_row_display()
                self.root.focus_set()
            return
        
        # Если слово есть в словаре, проверяем его
        self.check_guess(guess)
    
    def check_guess(self, guess):
        """Проверяет введённое слово и обновляет цвета"""
        if self.game_over:
            return
        
        target = self.target_word
        guess_list = list(guess)
        target_list = list(target)
        
        colors = ["gray"] * WORD_LEN
        
        # Сначала находим зелёные буквы
        for i in range(WORD_LEN):
            if guess_list[i] == target_list[i]:
                colors[i] = "green"
                target_list[i] = None
        
        # Затем жёлтые
        for i in range(WORD_LEN):
            if colors[i] == "green":
                continue
            if guess_list[i] in target_list:
                colors[i] = "yellow"
                idx = target_list.index(guess_list[i])
                target_list[idx] = None
        
        # Обновляем цвета ячеек
        for i, color in enumerate(colors):
            self.update_cell_color(self.current_attempt, i, color)
        
        # Обновляем цвета клавиш
        for i, letter in enumerate(guess):
            self.update_key_color(letter, colors[i])
        
        # Проверяем победу или поражение
        if guess == target:
            self.game_over = True
            self.show_win_screen()
            return
        
        self.current_attempt += 1
        if self.current_attempt >= MAX_ATTEMPTS:
            self.game_over = True
            self.show_lose_screen()
            return
    
    def show_win_screen(self):
        self.current_screen = "win"
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg=FIRST_BG)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Получаем размеры окна
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Вычисляем размеры пропорционально окну
        frame_width = max(300, min(int(window_width * 0.5), window_width - 100))
        frame_height = max(120, min(int(window_height * 0.25), window_height - 200))
        font_size = max(14, int(window_width * 0.02))
        button_font_size = max(12, int(window_width * 0.018))
        button_padx = max(30, int(window_width * 0.05))
        button_pady = max(8, int(window_height * 0.015))
        
        main_frame = tk.Frame(self.root, bg=FIRST_BG)
        main_frame.pack(expand=True, fill="both")
        
        center_container = tk.Frame(main_frame, bg=FIRST_BG)
        center_container.pack(expand=True)
        
        # Карточка победы
        win_frame = tk.Frame(center_container, bg=SECOND_BG, width=frame_width, height=frame_height)
        win_frame.pack(pady=max(20, int(window_height * 0.05)))
        win_frame.pack_propagate(False)
        win_frame.config(highlightbackground="black", highlightthickness=2)
        
        win_label = tk.Label(
            win_frame,
            text="Молодец! Ты отгадал\nзагаданное слово!",
            font=("Arial", font_size, "normal"),
            bg=SECOND_BG,
            fg="black",
            justify="center"
        )
        win_label.pack(expand=True)
        
        # Кнопка "Дальше"
        next_btn = tk.Button(
            center_container,
            text="Дальше",
            font=("Arial", button_font_size, "normal"),
            bg=SECOND_BG,
            fg="black",
            cursor="hand2",
            padx=button_padx,
            pady=button_pady,
            relief="solid",
            bd=2,
            command=self.play_again
        )
        next_btn.pack(pady=max(15, int(window_height * 0.03)))
        
        def on_enter(e):
            next_btn.config(bg=BUTTON_HOVER)
        def on_leave(e):
            next_btn.config(bg=SECOND_BG)
        
        next_btn.bind("<Enter>", on_enter)
        next_btn.bind("<Leave>", on_leave)
    
    def show_lose_screen(self):
        self.current_screen = "lose"
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg=FIRST_BG)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Получаем размеры окна
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Вычисляем размеры пропорционально окну
        frame_width = max(300, min(int(window_width * 0.5), window_width - 100))
        frame_height = max(150, min(int(window_height * 0.3), window_height - 200))
        font_size = max(14, int(window_width * 0.02))
        word_font_size = max(18, int(window_width * 0.03))
        button_font_size = max(12, int(window_width * 0.018))
        button_padx = max(30, int(window_width * 0.05))
        button_pady = max(8, int(window_height * 0.015))
        
        main_frame = tk.Frame(self.root, bg=FIRST_BG)
        main_frame.pack(expand=True, fill="both")
        
        center_container = tk.Frame(main_frame, bg=FIRST_BG)
        center_container.pack(expand=True)
        
        # Карточка поражения
        lose_frame = tk.Frame(center_container, bg=SECOND_BG, width=frame_width, height=frame_height)
        lose_frame.pack(pady=max(20, int(window_height * 0.05)))
        lose_frame.pack_propagate(False)
        lose_frame.config(highlightbackground="black", highlightthickness=2)
        
        lose_label = tk.Label(
            lose_frame,
            text="К сожалению, вы не отгадали\nзагаданное слово",
            font=("Arial", font_size, "normal"),
            bg=SECOND_BG,
            fg="black",
            justify="center"
        )
        lose_label.pack(pady=(max(15, int(frame_height * 0.1)), max(5, int(frame_height * 0.03))))
        
        word_label = tk.Label(
            lose_frame,
            text=f"{self.target_word}",
            font=("Arial", word_font_size, "normal"),
            bg=SECOND_BG,
            fg="black"
        )
        word_label.pack()
        
        # Кнопка "Дальше"
        next_btn = tk.Button(
            center_container,
            text="Дальше",
            font=("Arial", button_font_size, "normal"),
            bg=SECOND_BG,
            fg="black",
            cursor="hand2",
            padx=button_padx,
            pady=button_pady,
            relief="solid",
            bd=2,
            command=self.play_again
        )
        next_btn.pack(pady=max(15, int(window_height * 0.03)))
        
        def on_enter(e):
            next_btn.config(bg=BUTTON_HOVER)
        def on_leave(e):
            next_btn.config(bg=SECOND_BG)
        
        next_btn.bind("<Enter>", on_enter)
        next_btn.bind("<Leave>", on_leave)
    
    def play_again(self):
        self.current_attempt = 0
        self.game_over = False
        self.waiting_for_word_add = False
        self.target_word = random.choice(self.WORDS)
        self.guesses = [""] * MAX_ATTEMPTS
        self.create_game_screen()
    
    def on_key_press(self, event):
        if self.game_over or self.waiting_for_word_add:
            return
        
        if event.keysym == "Return":
            self.submit_guess()
            return
        
        if event.keysym == "BackSpace":
            self.backspace()
            return
        
        char = event.char.upper()
        
        if char in "ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЁ":
            self.add_letter(char)
            return
        
        eng_to_rus = {
            'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н', 'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З',
            'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р', 'J': 'О', 'K': 'Л', 'L': 'Д',
            'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т', 'M': 'Ь'
        }
        
        if char in eng_to_rus:
            self.add_letter(eng_to_rus[char])