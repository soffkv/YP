import tkinter as tk
from tkinter import messagebox

def create_start_screen(root, start_callback):
    """
    Создаёт начальный экран с правилами и кнопкой старта.
    root - главное окно tk.Tk()
    start_callback - функция, которая вызовется при нажатии "Начать игру"
    """
    # Очистка окна
    for widget in root.winfo_children():
        widget.destroy()
    
    # Фон окна - нежный розово-персиковый
    root.configure(bg="#F9D0D0")
    
    # Основной контейнер
    main_frame = tk.Frame(root, bg="#F9D0D0")
    main_frame.pack(expand=True, fill="both")
    
    # Заголовок
    title_label = tk.Label(
        main_frame,
        text="5 БУКВ",
        font=("Arial", 40, "bold"),
        bg="#F9D0D0",
        fg="#2c3e50"
    )
    title_label.pack(pady=(60, 10))
    
    # Подзаголовок
    subtitle = tk.Label(
        main_frame,
        text="Угадай слово за 6 попыток",
        font=("Arial", 14),
        bg="#F9D0D0",
        fg="#7f8c8d"
    )
    subtitle.pack(pady=(0, 30))
    
    # Карточка с правилами (фон #FFCCE9)
    rules_frame = tk.Frame(main_frame, bg="#FFCCE9", relief="flat", bd=0)
    rules_frame.pack(pady=20, padx=30, fill="x")
    # Тёмно-розовая обводка для аккуратности
    rules_frame.config(highlightbackground="#e8b0d0", highlightthickness=1)
    
    rules_text = """
    📖 Правила игры:
    
    • Цель: угадать загаданное слово из 5 букв.
    • У вас есть 6 попыток.
    • После каждой попытки буквы подсвечиваются:
       🟢 Зелёный — буква на своём месте
       🟡 Жёлтый — буква есть в слове, но не здесь
       ⚪ Серый — такой буквы нет в слове
    • Если ввели слово с двумя одинаковыми буквами, 
      а в загаданном только одна — подсветится только одна.
    """
    
    rules_label = tk.Label(
        rules_frame,
        text=rules_text,
        font=("Arial", 11),
        bg="#FFCCE9",
        fg="#2c3e50",
        justify="left",
        anchor="w"
    )
    rules_label.pack(padx=20, pady=20, fill="x")
    
    # Кнопка "Начать игру" (фон #FFCCE9)
    start_btn = tk.Button(
        main_frame,
        text="Начать игру",
        font=("Arial", 14, "bold"),
        bg="#FFCCE9",
        fg="#2c3e50",
        activebackground="#f0b8d8",
        activeforeground="#2c3e50",
        relief="flat",
        cursor="hand2",
        padx=40,
        pady=12,
        command=start_callback
    )
    start_btn.pack(pady=40)
    
    # Эффект при наведении
    def on_enter(e):
        start_btn.config(bg="#f0b8d8")  # чуть темнее при наведении
    
    def on_leave(e):
        start_btn.config(bg="#FFCCE9")
    
    start_btn.bind("<Enter>", on_enter)
    start_btn.bind("<Leave>", on_leave)


# ------------------- ПРИМЕР ИСПОЛЬЗОВАНИЯ -------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.title("5 букв — начальный экран")
    root.geometry("600x700")
    
    # Функция, которая будет вызвана при нажатии "Начать игру"
    def on_start():
        messagebox.showinfo("Старт", "Переход к игровому экрану")
        # Здесь будет create_game_screen(root)
    
    # Создаём начальный экран
    create_start_screen(root, on_start)
    
    root.mainloop()