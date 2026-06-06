import tkinter as tk
from game import WordleGame

if __name__ == "__main__":
    root = tk.Tk()
    game = WordleGame(root)
    root.mainloop()