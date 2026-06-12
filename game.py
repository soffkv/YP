import tkinter as tk
from tkinter import messagebox
import random
import os
import sys

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ

def get_resource_path(filename):
    """
    Возвращает правильный путь к файлу, даже когда программа собрана в exe.
    При запуске из исходного кода - ищет файл в папке со скриптом.
    При запуске из exe - ищет во временной папке MEIPASS.
    """
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS  # Путь к временной папке при запуске exe
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))  # Путь к папке со скриптом
    return os.path.join(base_path, filename)


def load_words(filename="words.txt"):
    """
    Загружает слова из текстового файла.
    Каждое слово должно быть на отдельной строке и состоять из 5 букв.
    Возвращает список слов в верхнем регистре.
    """
    filepath = get_resource_path(filename)
    words = []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip().upper()  # Удаляем пробелы и переводим в верхний регистр
                if len(word) == 5 and word.isalpha():  # Проверяем длину и что это буквы
                    words.append(word)
    except FileNotFoundError:
        pass  # Если файл не найден, возвращаем пустой список
    
    return words


def save_word_to_file(word):
    """
    Сохраняет новое слово в файл словаря.
    Проверяет длину слова и уникальность.
    Возвращает (успех, сообщение).
    """
    filepath = get_resource_path("words.txt")
    
    # Проверка длины слова
    if len(word) != 5 or not word.isalpha():
        return False, "Слово должно состоять из 5 букв!"
    
    # Проверка на существование слова в словаре
    existing_words = load_words("words.txt")
    if word.upper() in existing_words:
        return False, "Это слово уже есть в словаре!"
    
    # Сохранение в файл
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(f"{word.upper()}\n")
        return True, "Слово успешно добавлено в словарь!"
    except Exception as e:
        return False, f"Ошибка при сохранении: {e}"


# ФУНКЦИЯ ДЛЯ СОЗДАНИЯ СКРУГЛЁННЫХ ПРЯМОУГОЛЬНИКОВ

def _create_rounded_rect(self, x1, y1, x2, y2, radius=30, **kwargs):
    """
    Создаёт прямоугольник со скруглёнными углами на Canvas.
    x1,y1 - координаты левого верхнего угла
    x2,y2 - координаты правого нижнего угла
    radius - радиус скругления
    """
    width = x2 - x1
    height = y2 - y1
    max_radius = min(width, height) // 2  # Максимально возможный радиус
    radius = min(radius, max_radius)  # Ограничиваем радиус, чтобы не выйти за пределы
    
    # Создаём список точек для полигона (12 точек для скруглённого прямоугольника)
    points = []
    for x, y in [
        (x1+radius, y1), (x2-radius, y1),  # Верхняя сторона
        (x2, y1), (x2, y1+radius),         # Правый верхний угол
        (x2, y2-radius), (x2, y2),         # Правая сторона
        (x2-radius, y2), (x1+radius, y2),  # Нижняя сторона
        (x1, y2), (x1, y2-radius),         # Левый нижний угол
        (x1, y1+radius), (x1, y1)          # Левая сторона
    ]:
        points.append(x)
        points.append(y)
    
    return self.create_polygon(points, smooth=True, **kwargs)


# Добавляем метод в класс Canvas для удобства использования
tk.Canvas.create_rounded_rect = _create_rounded_rect


# КОНСТАНТЫ

MAX_ATTEMPTS = 6  # Максимальное количество попыток
WORD_LEN = 5      # Длина слова

# Цветовая схема
FIRST_BG = "#F9D0D0"      # Фон первого окна (нежно-персиковый)
SECOND_BG = "#FFCCE9"     # Фон второго окна (нежно-розовый)
CELL_KEY_BG = "#F9D0D0"   # Фон ячеек и кнопок клавиатуры (нежно-персиковый)
CARD_BG = "#FFD1E8"       # Фон карточки правил и кнопки (максимально нежно-розовый)
BUTTON_HOVER = "#FFC0D8"  # Цвет кнопки при наведении


# ОСНОВНОЙ КЛАСС ИГРЫ

class WordleGame:
    """Основной класс игры Wordle (5 букв)"""
    
    def __init__(self, root):
        """
        Инициализация игры.
        root - главное окно tkinter
        """
        self.root = root
        self.root.title("5 букв")
        self.root.geometry("750x700")
        self.root.configure(bg=FIRST_BG)
        self.root.minsize(500, 500)
        
        # Привязка клавиши ESC для закрытия игры
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Загрузка словаря
        self.WORDS = load_words("words.txt")
        
        # Если словарь пуст - показываем ошибку и выходим
        if not self.WORDS:
            self.show_error_and_exit()
            return
        
        # Переменные состояния игры
        self.current_attempt = 0          # Текущая попытка (0-5)
        self.game_over = False             # Флаг окончания игры
        self.target_word = random.choice(self.WORDS)  # Загаданное слово
        self.guesses = [""] * MAX_ATTEMPTS  # Список введённых слов
        self.valid_words = set(self.WORDS) # Множество допустимых слов для быстрой проверки
        self.key_buttons = {}              # Словарь кнопок клавиатуры
        self.cell_frames = []              # Список ячеек игрового поля
        self.key_frames = {}               # Словарь фреймов клавиш
        self.current_screen = "start"      # Текущий экран (start/game/win/lose)
        self.waiting_for_word_add = False  # Флаг ожидания добавления слова
        
        # Сохраняем цвета для каждой строки (чтобы они не сбрасывались при изменении размера окна)
        self.row_colors = [[] for _ in range(MAX_ATTEMPTS)]
        
        # Создаём стартовый экран
        self.create_start_screen()
        
        # Привязка события изменения размера окна
        self.root.bind("<Configure>", self.on_window_resize)
    
    
    # МЕТОДЫ ЗАГРУЗКИ И ПЕРЕЗАГРУЗКИ СЛОВАРЯ
    
    def reload_words(self):
        """Перезагружает словарь из файла и обновляет множество допустимых слов"""
        self.WORDS = load_words("words.txt")
        if self.WORDS:
            self.valid_words = set(self.WORDS)
            return True
        return False
    
    
    # ОБРАБОТЧИКИ СОБЫТИЙ
    
    def on_window_resize(self, event):
        """
        Обработчик изменения размера окна.
        Пересоздаёт текущий экран с новыми размерами.
        """
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
        """Показывает экран ошибки, если файл words.txt не найден или пуст"""
        # Очищаем все виджеты
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Создаём фрейм с сообщением об ошибке
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
        
        # Кнопка выхода
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
    
    
    # ЭКРАН СТАРТА
    
    def create_start_screen(self):
        """Создаёт стартовый экран с правилами игры и кнопкой начала"""
        self.current_screen = "start"
        
        # Очищаем окно
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg=FIRST_BG)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Получаем текущие размеры окна для адаптивного дизайна
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
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg=FIRST_BG)
        main_frame.pack(expand=True, fill="both")
        
        # Центральный контейнер для вертикального центрирования
        center_container = tk.Frame(main_frame, bg=FIRST_BG)
        center_container.pack(expand=True)
        
        # Карточка с правилами
        rules_container = tk.Frame(center_container, bg=FIRST_BG, width=card_width, height=card_height)
        rules_container.pack(pady=(max(10, int(window_height * 0.03)), max(10, int(window_height * 0.02))))
        rules_container.pack_propagate(False)
        
        rules_canvas = tk.Canvas(rules_container, bg=FIRST_BG, highlightthickness=0)
        rules_canvas.pack(fill="both", expand=True)
        
        # Скруглённый фон карточки
        rules_canvas.create_rounded_rect(5, 5, card_width-5, card_height-5, radius=radius, 
                                         fill=CARD_BG, outline="black", width=2)
        
        # Текст правил
        rules_text = """Правила игры:

Цель: угадать загаданное слово из 5 букв

У вас есть 6 попыток

После каждой попытки буквы подсвечиваются:

- Зелёный - буква на своём месте
- Жёлтый - буква есть в слове, но не здесь
- Серый - такой буквы нет в слове

Если ввести слово с двумя одинаковыми буквами, а в загаданном слове только одна такая буква, 
зеленым или желтым подсветится только одна из повторяющихся букв, стоящая ближе к правильному месту."""
        
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
        
        start_rect = start_canvas.create_rounded_rect(5, 5, button_width-5, button_height-5, 
                                                       radius=max(15, int(radius * 0.8)), 
                                                       fill=CARD_BG, outline="black", width=2)
        start_text = start_canvas.create_text(button_width//2, button_height//2, text="Начать игру", 
                                               font=("Arial", button_font_size, "normal"), fill="black")
        
        # Обработчики для кнопки
        def start_handler(e=None):
            self.start_game()
        
        def on_enter(e=None):
            start_canvas.itemconfig(start_rect, fill=BUTTON_HOVER)
        
        def on_leave(e=None):
            start_canvas.itemconfig(start_rect, fill=CARD_BG)
        
        # Привязываем события
        start_canvas.tag_bind(start_rect, "<Button-1>", start_handler)
        start_canvas.tag_bind(start_text, "<Button-1>", start_handler)
        start_canvas.tag_bind(start_rect, "<Enter>", on_enter)
        start_canvas.tag_bind(start_rect, "<Leave>", on_leave)
        start_canvas.tag_bind(start_text, "<Enter>", on_enter)
        start_canvas.tag_bind(start_text, "<Leave>", on_leave)
        start_canvas.config(cursor="hand2")
    
    
    def start_game(self):
        """Начинает новую игру: сбрасывает все переменные и создаёт игровой экран"""
        self.current_attempt = 0
        self.game_over = False
        self.waiting_for_word_add = False
        self.target_word = random.choice(self.WORDS)  # Выбираем новое загаданное слово
        self.guesses = [""] * MAX_ATTEMPTS
        self.row_colors = [[] for _ in range(MAX_ATTEMPTS)]
        self.create_game_screen()
    
    
    # ИГРОВОЙ ЭКРАН
    
    def create_game_screen(self):
        """Создаёт основной игровой экран: поле из ячеек и клавиатуру"""
        self.current_screen = "game"
        
        # Очищаем окно
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg=SECOND_BG)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Адаптивные размеры
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        # Вычисляем размер ячейки в зависимости от размера окна
        max_cell_size = min(window_width // (WORD_LEN + 3), window_height // (MAX_ATTEMPTS + 5))
        cell_size = max(40, min(75, max_cell_size))
        cell_padding = max(3, int(cell_size * 0.07))
        font_size = max(16, int(cell_size * 0.4))
        key_size = max(32, int(cell_size * 0.7))
        key_font_size = max(9, int(key_size * 0.28))
        key_padding = max(2, int(key_size * 0.04))
        radius = max(8, int(cell_size * 0.35))
        
        # Игровое поле (сетка 6x5)
        self.cell_frames = []
        game_frame = tk.Frame(self.root, bg=SECOND_BG)
        game_frame.pack(expand=True, pady=max(10, int(window_height * 0.02)))
        
        for row in range(MAX_ATTEMPTS):
            row_frames = []
            for col in range(WORD_LEN):
                # Каждая ячейка - отдельный фрейм с Canvas
                cell_frame = tk.Frame(game_frame, bg=SECOND_BG)
                cell_frame.grid(row=row, column=col, padx=cell_padding, pady=cell_padding)
                
                canvas = tk.Canvas(cell_frame, width=cell_size, height=cell_size, 
                                   bg=SECOND_BG, highlightthickness=0)
                canvas.pack()
                
                # Скруглённый прямоугольник - фон ячейки
                rect = canvas.create_rounded_rect(3, 3, cell_size-3, cell_size-3, 
                                                   radius=radius, fill=CELL_KEY_BG, 
                                                   outline="black", width=2)
                # Текст в ячейке (буква)
                text_id = canvas.create_text(cell_size//2, cell_size//2, text="", 
                                              font=("Arial", font_size, "bold"), fill="#2C3E50")
                
                row_frames.append({"canvas": canvas, "rect": rect, "text": text_id})
            self.cell_frames.append(row_frames)
        
        # Восстанавливаем предыдущие попытки и их цвета (при изменении размера окна)
        for row in range(self.current_attempt):
            if self.guesses[row]:
                for col, letter in enumerate(self.guesses[row]):
                    self.update_cell_text(row, col, letter)
                if self.row_colors[row]:
                    for col, color in enumerate(self.row_colors[row]):
                        if color:
                            self.update_cell_color(row, col, color)
        
        # Создаём клавиатуру
        self.create_keyboard(key_size, key_font_size, key_padding, radius)
        
        # Привязываем нажатия клавиш
        self.root.bind("<Key>", self.on_key_press)
        self.root.focus_set()
    
    
    def create_keyboard(self, key_size, key_font_size, key_padding, radius):
        """
        Создаёт виртуальную клавиатуру с буквами и кнопками управления.
        key_size - размер кнопки
        key_font_size - размер шрифта
        key_padding - отступы
        radius - радиус скругления
        """
        # Основной контейнер для клавиатуры
        keyboard_container = tk.Frame(self.root, bg=SECOND_BG)
        keyboard_container.pack(pady=max(5, int(key_size * 0.15)))
        
        # Левая часть - буквенная клавиатура
        keyboard_frame = tk.Frame(keyboard_container, bg=SECOND_BG)
        keyboard_frame.pack(side="left")
        
        # Ряды клавиш (русская раскладка)
        rows = [
            ["Й", "Ц", "У", "К", "Е", "Н", "Г", "Ш", "Щ", "З", "Х", "Ъ"],
            ["Ф", "Ы", "В", "А", "П", "Р", "О", "Л", "Д", "Ж", "Э"],
            ["Я", "Ч", "С", "М", "И", "Т", "Ь", "Б", "Ю"]
        ]
        
        self.key_frames = {}
        key_radius = max(5, int(radius * 0.7))
        
        # Создаём каждую буквенную клавишу
        for r, row in enumerate(rows):
            row_frame = tk.Frame(keyboard_frame, bg=SECOND_BG)
            row_frame.pack(pady=key_padding)
            for letter in row:
                btn_frame = tk.Frame(row_frame, bg=SECOND_BG)
                btn_frame.pack(side="left", padx=key_padding, pady=key_padding)
                
                canvas = tk.Canvas(btn_frame, width=key_size, height=key_size, 
                                   bg=SECOND_BG, highlightthickness=0)
                canvas.pack()
                
                rect = canvas.create_rounded_rect(3, 3, key_size-3, key_size-3, 
                                                   radius=key_radius, fill=CELL_KEY_BG, 
                                                   outline="black", width=2)
                text_id = canvas.create_text(key_size//2, key_size//2, text=letter, 
                                              font=("Arial", key_font_size, "bold"), fill="#2C3E50")
                
                # Обработчики для клавиши
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
        
        # Правая часть - кнопки управления
        action_frame = tk.Frame(keyboard_container, bg=SECOND_BG)
        action_frame.pack(side="left", padx=(key_padding * 3, 0))
        
        btn_width = int(key_size * 2.0)
        btn_height = key_size
        btn_radius = key_radius
        
        # Кнопка "Удалить"
        delete_frame = tk.Frame(action_frame, bg=SECOND_BG)
        delete_frame.pack(pady=(0, key_padding * 4))
        
        delete_canvas = tk.Canvas(delete_frame, width=btn_width, height=btn_height, 
                                   bg=SECOND_BG, highlightthickness=0)
        delete_canvas.pack()
        delete_rect = delete_canvas.create_rounded_rect(3, 3, btn_width-3, btn_height-3, 
                                                         radius=btn_radius, fill=CELL_KEY_BG, 
                                                         outline="black", width=2)
        delete_text = delete_canvas.create_text(btn_width//2, btn_height//2, text="Удалить", 
                                                 font=("Arial", key_font_size, "bold"), fill="#2C3E50")
        
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
        
        # Кнопка "Ввод"
        enter_frame = tk.Frame(action_frame, bg=SECOND_BG)
        enter_frame.pack(pady=(key_padding * 4, 0))
        
        enter_canvas = tk.Canvas(enter_frame, width=btn_width, height=btn_height, 
                                  bg=SECOND_BG, highlightthickness=0)
        enter_canvas.pack()
        enter_rect = enter_canvas.create_rounded_rect(3, 3, btn_width-3, btn_height-3, 
                                                       radius=btn_radius, fill=CELL_KEY_BG, 
                                                       outline="black", width=2)
        enter_text = enter_canvas.create_text(btn_width//2, btn_height//2, text="Ввод", 
                                               font=("Arial", key_font_size, "bold"), fill="#2C3E50")
        
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
    
    
    # МЕТОДЫ ОБНОВЛЕНИЯ ИГРОВОГО ПОЛЯ
    
    def update_cell_text(self, row, col, text):
        """Обновляет текст в указанной ячейке"""
        if row < len(self.cell_frames) and col < len(self.cell_frames[row]):
            canvas_data = self.cell_frames[row][col]
            canvas_data["canvas"].itemconfig(canvas_data["text"], text=text)
    
    
    def update_cell_color(self, row, col, color):
        """
        Обновляет цвет ячейки.
        color может быть: "green", "yellow", "gray"
        """
        if row < len(self.cell_frames) and col < len(self.cell_frames[row]):
            # Соответствие цветов
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
        """
        Обновляет цвет клавиши на виртуальной клавиатуре.
        Приоритет: зелёный > жёлтый > серый
        """
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
        
        # Зелёный - всегда обновляем
        if color == "green":
            key_data["canvas"].itemconfig(key_data["rect"], fill=fill_color)
            key_data["canvas"].itemconfig(key_data["text"], fill="white")
        # Жёлтый - обновляем, если ещё не зелёный
        elif color == "yellow" and current_fill != "#27AE60":
            key_data["canvas"].itemconfig(key_data["rect"], fill=fill_color)
            key_data["canvas"].itemconfig(key_data["text"], fill="white")
        # Серый - обновляем, если ещё не зелёный и не жёлтый
        elif color == "gray" and current_fill not in ["#27AE60", "#F39C12"]:
            key_data["canvas"].itemconfig(key_data["rect"], fill=fill_color)
            key_data["canvas"].itemconfig(key_data["text"], fill="white")
    
    
    def add_letter(self, letter):
        """Добавляет букву в текущую попытку"""
        if self.game_over or self.waiting_for_word_add:
            return
        if len(self.guesses[self.current_attempt]) < WORD_LEN:
            self.guesses[self.current_attempt] += letter
            self.update_row_display()
    
    
    def backspace(self):
        """Удаляет последнюю букву в текущей попытке"""
        if self.game_over or self.waiting_for_word_add:
            return
        if len(self.guesses[self.current_attempt]) > 0:
            self.guesses[self.current_attempt] = self.guesses[self.current_attempt][:-1]
            self.update_row_display()
    
    
    def update_row_display(self):
        """Обновляет отображение текущей строки на игровом поле"""
        guess = self.guesses[self.current_attempt]
        for col in range(WORD_LEN):
            if col < len(guess):
                self.update_cell_text(self.current_attempt, col, guess[col])
            else:
                self.update_cell_text(self.current_attempt, col, "")
    
    
    # ОСНОВНАЯ ЛОГИКА ИГРЫ
    
    def submit_guess(self):
        """
        Обрабатывает введённое слово:
        - Проверяет длину
        - Проверяет на повторный ввод
        - Проверяет наличие в словаре (предлагает добавить, если нет)
        - Запускает проверку слова
        """
        if self.game_over or self.waiting_for_word_add:
            return
        
        guess = self.guesses[self.current_attempt]
        
        # Проверка длины слова
        if len(guess) != WORD_LEN:
            messagebox.showwarning("Неполное слово", f"Введите слово из {WORD_LEN} букв!")
            self.root.focus_set()
            return
        
        # ПРОВЕРКА НА ПОВТОРНЫЙ ВВОД ОДИНАКОВОГО СЛОВА
        # Если слово уже было введено в одной из предыдущих попыток
        if guess in self.guesses[:self.current_attempt]:
            messagebox.showwarning("Повторное слово", 
                                   f"Слово '{guess}' вы уже вводили!\n\nПопробуйте другое слово.")
            # Очищаем текущую строку, чтобы игрок мог ввести новое слово
            self.guesses[self.current_attempt] = ""
            self.update_row_display()
            self.root.focus_set()
            return
        
        # Проверка наличия слова в словаре
        if guess not in self.valid_words:
            new_word = guess
            
            # Спрашиваем, хочет ли игрок добавить слово в словарь
            answer = messagebox.askyesno(
                "Слова нет в словаре", 
                f"Слова '{new_word}' нет в словаре.\n\nХотите добавить его в словарь?\n\n(Слово должно состоять из 5 букв)"
            )
            
            if answer:
                # Пользователь хочет добавить слово
                success, message = save_word_to_file(new_word)
                
                if success:
                    messagebox.showinfo("Успех", f"Слово '{new_word}' добавлено в словарь!")
                    # Перезагружаем словарь и обновляем множество допустимых слов
                    self.reload_words()
                    self.valid_words = set(self.WORDS)
                    # Проверяем добавленное слово
                    self.check_guess(new_word)
                else:
                    messagebox.showerror("Ошибка", message)
                    self.root.focus_set()
            else:
                # Пользователь отказался добавлять слово - оставляем слово на поле для редактирования
                messagebox.showinfo("Слово не добавлено", 
                                   f"Слово '{new_word}' не было добавлено в словарь.\n\nСлово осталось на поле, вы можете его изменить.")
                self.root.focus_set()
            return
        
        # Если слово есть в словаре, проверяем его
        self.check_guess(guess)
    
    
    def check_guess(self, guess):
        """
        Проверяет введённое слово и обновляет цвета ячеек и клавиш.
        Алгоритм:
        1. Сначала отмечаем зелёные буквы (правильное место)
        2. Затем отмечаем жёлтые буквы (есть в слове, но не на этом месте)
        3. Остальные - серые
        """
        if self.game_over:
            return
        
        target = self.target_word
        guess_list = list(guess)
        target_list = list(target)
        
        # Массив цветов для каждой позиции (изначально все серые)
        colors = ["gray"] * WORD_LEN
        
        # ПЕРВЫЙ ПРОХОД: ищем зелёные буквы (точное совпадение)
        for i in range(WORD_LEN):
            if guess_list[i] == target_list[i]:
                colors[i] = "green"
                target_list[i] = None  # Удаляем из списка, чтобы не использовать повторно
        
        # ВТОРОЙ ПРОХОД: ищем жёлтые буквы (есть в слове, но не на этом месте)
        for i in range(WORD_LEN):
            if colors[i] == "green":
                continue  # Пропускаем уже отмеченные зелёные
            if guess_list[i] in target_list:
                colors[i] = "yellow"
                idx = target_list.index(guess_list[i])
                target_list[idx] = None  # Удаляем из списка, чтобы не использовать повторно
        
        # Сохраняем цвета для этой попытки (чтобы восстановить при изменении размера окна)
        self.row_colors[self.current_attempt] = colors.copy()
        
        # Обновляем цвета ячеек на игровом поле
        for i, color in enumerate(colors):
            self.update_cell_color(self.current_attempt, i, color)
        
        # Обновляем цвета клавиш на виртуальной клавиатуре
        for i, letter in enumerate(guess):
            self.update_key_color(letter, colors[i])
        
        # ПРОВЕРКА ПОБЕДЫ
        if guess == target:
            self.game_over = True
            self.show_win_screen()
            return
        
        # ПЕРЕХОД К СЛЕДУЮЩЕЙ ПОПЫТКЕ
        self.current_attempt += 1
        
        # ПРОВЕРКА ПОРАЖЕНИЯ (попытки закончились)
        if self.current_attempt >= MAX_ATTEMPTS:
            self.game_over = True
            self.show_lose_screen()
            return
    
    
    # ЭКРАНЫ ПОБЕДЫ И ПОРАЖЕНИЯ
    
    def show_win_screen(self):
        """Показывает экран победы"""
        self.current_screen = "win"
        
        # Очищаем окно
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg=FIRST_BG)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Адаптивные размеры
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
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
        
        # Кнопка "Дальше" для продолжения игры
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
        """Показывает экран поражения с загаданным словом"""
        self.current_screen = "lose"
        
        # Очищаем окно
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.configure(bg=FIRST_BG)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Адаптивные размеры
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
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
        
        # Показываем загаданное слово
        word_label = tk.Label(
            lose_frame,
            text=f"{self.target_word}",
            font=("Arial", word_font_size, "normal"),
            bg=SECOND_BG,
            fg="black"
        )
        word_label.pack()
        
        # Кнопка "Дальше" для продолжения игры
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
        """Начинает новую игру (вызывается после победы или поражения)"""
        self.current_attempt = 0
        self.game_over = False
        self.waiting_for_word_add = False
        self.target_word = random.choice(self.WORDS)  # Новое загаданное слово
        self.guesses = [""] * MAX_ATTEMPTS
        self.row_colors = [[] for _ in range(MAX_ATTEMPTS)]
        self.create_game_screen()
    
    
    # ОБРАБОТЧИК КЛАВИАТУРНЫХ НАЖАТИЙ
    
    def on_key_press(self, event):
        """
        Обрабатывает нажатия клавиш на физической клавиатуре.
        Поддерживает русскую раскладку и транслитерацию с английской.
        """
        if self.game_over or self.waiting_for_word_add:
            return
        
        # Клавиша Enter - отправка слова
        if event.keysym == "Return":
            self.submit_guess()
            return
        
        # Клавиша Backspace - удаление буквы
        if event.keysym == "BackSpace":
            self.backspace()
            return
        
        char = event.char.upper()
        
        # Прямой ввод русских букв
        if char in "ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЁ":
            self.add_letter(char)
            return
        
        # Транслитерация с английской клавиатуры на русскую
        eng_to_rus = {
            'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н', 'U': 'Г', 
            'I': 'Ш', 'O': 'Щ', 'P': 'З', 'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 
            'G': 'П', 'H': 'Р', 'J': 'О', 'K': 'Л', 'L': 'Д', 'Z': 'Я', 'X': 'Ч', 
            'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т', 'M': 'Ь'
        }
        
        if char in eng_to_rus:
            self.add_letter(eng_to_rus[char])


# ТОЧКА ВХОДА 

if __name__ == "__main__":
    root = tk.Tk()
    game = WordleGame(root)
    root.mainloop()