import os
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from zipfile import ZipFile, ZIP_DEFLATED

class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File backup v 0.9.3")
        self.source_dir = ""
        self.target_dir = ""
        self.interval = 60  # интервал в минутах по умолчанию
        self.backup_thread = None
        self.stop_event = threading.Event()

        # Интерфейс
        tk.Label(root, text="Исходный каталог:").grid(row=0, column=0, sticky="w")
        self.source_entry = tk.Entry(root, width=50)
        self.source_entry.grid(row=0, column=1)
        tk.Button(root, text="Выбрать...", command=self.select_source).grid(row=0, column=2)

        tk.Label(root, text="Каталог для резервных копий:").grid(row=1, column=0, sticky="w")
        self.target_entry = tk.Entry(root, width=50)
        self.target_entry.grid(row=1, column=1)
        tk.Button(root, text="Выбрать...", command=self.select_target).grid(row=1, column=2)

        tk.Label(root, text="Интервал копирования (минуты):").grid(row=2, column=0, sticky="w")
        self.interval_entry = tk.Entry(root, width=10)
        self.interval_entry.insert(0, "60")
        self.interval_entry.grid(row=2, column=1, sticky="w")

        self.start_button = tk.Button(root, text="Запустить резервное копирование", command=self.start_backup)
        self.start_button.grid(row=3, column=0, columnspan=3, pady=10)

        self.stop_button = tk.Button(root, text="Остановить", command=self.stop_backup, state=tk.DISABLED)
        self.stop_button.grid(row=4, column=0, columnspan=3)

    def select_source(self):
        directory = filedialog.askdirectory()
        if directory:
            self.source_dir = directory
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, directory)

    def select_target(self):
        directory = filedialog.askdirectory()
        if directory:
            self.target_dir = directory
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, directory)

    def start_backup(self):
        try:
            interval = int(self.interval_entry.get())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Интервал должен быть положительным целым числом")
            return

        self.source_dir = self.source_entry.get()
        self.target_dir = self.target_entry.get()

        if not os.path.isdir(self.source_dir):
            messagebox.showerror("Ошибка", "Исходный каталог не выбран или не существует")
            return
        if not os.path.isdir(self.target_dir):
            messagebox.showerror("Ошибка", "Каталог для резервных копий не выбран или не существует")
            return

        self.interval = interval
        self.stop_event.clear()
        self.backup_thread = threading.Thread(target=self.run_backup_schedule, daemon=True)
        self.backup_thread.start()

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        messagebox.showinfo("Запуск", "Автоматическое резервное копирование запущено")

    def stop_backup(self):
        self.stop_event.set()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        messagebox.showinfo("Остановка", "Резервное копирование остановлено")

    def run_backup_schedule(self):
        while not self.stop_event.is_set():
            self.create_backup()
            for _ in range(self.interval * 60):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

    def create_backup(self):
        # Создаём подкаталог с датой
        date_folder = time.strftime("%Y%m%d")
        backup_dir = os.path.join(self.target_dir, date_folder)
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Имя архива с текущим временем
        archive_name = time.strftime("%H%M%S") + ".zip"
        archive_path = os.path.join(backup_dir, archive_name)

        try:
            with ZipFile(archive_path, 'w', ZIP_DEFLATED) as zipf:
                for foldername, subfolders, filenames in os.walk(self.source_dir):
                    for filename in filenames:
                        filepath = os.path.join(foldername, filename)
                        # Добавляем файл в архив с относительным путём
                        arcname = os.path.relpath(filepath, self.source_dir)
                        zipf.write(filepath, arcname)
            print(f"Резервная копия создана: {archive_path}")
        except Exception as e:
            print(f"Ошибка при создании резервной копии: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BackupApp(root)
    root.mainloop()
