import os
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
import fnmatch
import json
import logging
from queue import Queue, Empty
import pystray
from PIL import Image, ImageDraw
import shutil  # для проверки свободного места

SETTINGS_FILE = "backup_app_settings.json"
SETTINGS_BACKUP_FILE = "backup_app_settings_backup.json"
LOG_FILE = "backup_app.log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File backup v 1.4.7")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close_window)
        self.root.overrideredirect(True)

        self.source_dirs = []
        self.source_files = []
        self.exclude_patterns = []
        self.target_dir = ""
        self.interval_hours = 24
        self.interval_weeks = 0
        self.compression_level = 6
        self.backup_thread = None
        self.stop_event = threading.Event()
        self.log_queue = Queue()
        self.running = False

        self._last_notifications = []
        self._notification_lock = threading.Lock()

        self.next_backup_time = None
        self.status_text = tk.StringVar(value="Статус: Ожидание запуска")

        self._build_custom_titlebar()
        self._build_ui()
        self._load_settings()
        self._process_log_queue()

        self._offset_x = 0
        self._offset_y = 0

        self._icon = None
        self._icon_thread = threading.Thread(target=self._setup_tray_icon, daemon=True)
        self._icon_thread.start()

        # Запускаем обновление статуса и следующего запуска
        self._update_status_loop()

    # --- Кастомный заголовок с кнопками ---
    def _build_custom_titlebar(self):
        self.titlebar = tk.Frame(self.root, bg="#2e2e2e", relief='raised', bd=0)
        self.titlebar.pack(fill=tk.X)

        self.title_label = tk.Label(self.titlebar, text=self.root.title(), bg="#2e2e2e", fg="white", padx=10)
        self.title_label.pack(side=tk.LEFT, pady=2)

        self.btn_close = tk.Button(self.titlebar, text="✕", bg="#2e2e2e", fg="white",
                                   command=self._close_window, relief=tk.FLAT, padx=8, pady=2,
                                   activebackground="#ff5555", activeforeground="white")
        self.btn_close.pack(side=tk.RIGHT, padx=2, pady=2)

        self.btn_minimize = tk.Button(self.titlebar, text="—", bg="#2e2e2e", fg="white",
                                      command=self._minimize_window, relief=tk.FLAT, padx=8, pady=2,
                                      activebackground="#555555", activeforeground="white")
        self.btn_minimize.pack(side=tk.RIGHT, padx=2, pady=2)

        for widget in (self.titlebar, self.title_label):
            widget.bind("<ButtonPress-1>", self._start_move)
            widget.bind("<ButtonRelease-1>", self._stop_move)
            widget.bind("<B1-Motion>", self._on_move)

    def _start_move(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def _stop_move(self, event):
        self._offset_x = 0
        self._offset_y = 0

    def _on_move(self, event):
        x = event.x_root - self._offset_x
        y = event.y_root - self._offset_y
        self.root.geometry(f"+{x}+{y}")

    def _minimize_window(self):
        self.root.update_idletasks()
        self.root.overrideredirect(False)
        self.root.iconify()

    def _close_window(self):
        self._on_close_window()

    def _on_close_window(self):
        if self.running:
            if messagebox.askyesno("Подтверждение", "Резервное копирование запущено. Вы действительно хотите выйти?"):
                self.stop_backup()
                self._remove_tray_icon()
                self.root.destroy()
        else:
            self._remove_tray_icon()
            self.root.destroy()

    # --- Трей и уведомления ---
    def _create_image(self):
        image = Image.new('RGB', (64, 64), color='lime')
        d = ImageDraw.Draw(image)
        d.text((20, 20), 'B', fill='orange')
        return image

    def _setup_tray_icon(self):
        image = self._create_image()
        menu = pystray.Menu(
            pystray.MenuItem('Показать окно', self._show_window),
            pystray.MenuItem('Выход', self._exit_app)
        )
        self._icon = pystray.Icon("BackupApp", image, "BackupApp", menu)
        self._icon.run()

    def _show_window(self, icon, item):
        self.root.after(0, self._restore_window)

    def _exit_app(self, icon, item):
        self.stop_event.set()
        if self.backup_thread and self.backup_thread.is_alive():
            self.backup_thread.join(timeout=5)
        self._remove_tray_icon()
        self.root.after(0, self.root.destroy)

    def _remove_tray_icon(self):
        if self._icon:
            self._icon.stop()
            self._icon = None

    def _restore_window(self):
        self.root.overrideredirect(True)
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _show_notification(self, message):
        with self._notification_lock:
            self._last_notifications.append(message)
            if len(self._last_notifications) > 15:
                self._last_notifications.pop(0)
            combined_message = "\n".join(self._last_notifications)

        # Ограничиваем длину уведомления (макс 250 символов с запасом)
        max_len = 250
        if len(combined_message) > max_len:
            combined_message = "..." + combined_message[-max_len:]

        def notify():
            try:
                if self._icon:
                    self._icon.notify(combined_message)
            except Exception as e:
                self._log(f"Ошибка уведомления в трее: {e}")

        threading.Thread(target=notify, daemon=True).start()

    # --- Основной интерфейс ---
    def _build_ui(self):
        self.main_frame = tk.Frame(self.root, bd=2, relief=tk.GROOVE)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(self.main_frame, text="Исходные каталоги и файлы:").grid(row=0, column=0, sticky="nw")
        self.sources_text = tk.Listbox(self.main_frame, width=60, height=8, selectmode=tk.SINGLE)
        self.sources_text.grid(row=0, column=1, columnspan=4, pady=5, sticky="w")

        tk.Button(self.main_frame, text="Добавить каталог", command=self.add_source).grid(row=1, column=1, sticky="w", padx=2)
        tk.Button(self.main_frame, text="Добавить файл", command=self.add_file).grid(row=1, column=2, sticky="w", padx=2)
        tk.Button(self.main_frame, text="Удалить из списка", command=self.remove_source).grid(row=1, column=3, sticky="w", padx=2)
        tk.Button(self.main_frame, text="Очистить список", command=self.clear_sources).grid(row=1, column=4, sticky="w", padx=2)

        tk.Label(self.main_frame, text="Каталог для резервных копий:").grid(row=2, column=0, sticky="w")
        self.target_entry = tk.Entry(self.main_frame, width=50)
        self.target_entry.grid(row=2, column=1, columnspan=3, sticky="w")
        tk.Button(self.main_frame, text="Выбрать...", command=self.select_target).grid(row=2, column=4, sticky="w", padx=2)

        tk.Label(self.main_frame, text="Интервал копирования:").grid(row=3, column=0, sticky="w")
        interval_frame = tk.Frame(self.main_frame)
        interval_frame.grid(row=3, column=1, columnspan=4, sticky="w")

        tk.Label(interval_frame, text="Часы:").grid(row=0, column=0)
        self.hours_entry = tk.Entry(interval_frame, width=5)
        self.hours_entry.insert(0, "24")
        self.hours_entry.grid(row=0, column=1, padx=5)

        tk.Label(interval_frame, text="Недели (опционально):").grid(row=0, column=2)
        self.weeks_entry = tk.Entry(interval_frame, width=5)
        self.weeks_entry.insert(0, "0")
        self.weeks_entry.grid(row=0, column=3, padx=5)

        tk.Label(interval_frame, text="Уровень сжатия (0-9):").grid(row=0, column=4)
        self.compression_entry = tk.Entry(interval_frame, width=3)
        self.compression_entry.insert(0, str(self.compression_level))
        self.compression_entry.grid(row=0, column=5, padx=5)

        tk.Label(self.main_frame, text="Исключить файлы по маске (через запятую *.tmp, *.log):").grid(row=4, column=0, sticky="w")
        self.exclude_entry = tk.Entry(self.main_frame, width=50)
        self.exclude_entry.grid(row=4, column=1, columnspan=4, sticky="w", pady=2)

        tk.Label(self.main_frame, textvariable=self.status_text, fg="green").grid(row=5, column=0, columnspan=5, sticky="w", pady=(5,0))

        tk.Label(self.main_frame, text="Следующее резервное копирование:").grid(row=6, column=0, sticky="w")
        self.next_backup_label = tk.Label(self.main_frame, text="не запланировано", fg="blue")
        self.next_backup_label.grid(row=6, column=1, columnspan=4, sticky="w", pady=(0,10))

        tk.Label(self.main_frame, text="Лог резервного копирования:").grid(row=7, column=0, sticky="nw")
        self.log_text = scrolledtext.ScrolledText(self.main_frame, width=60, height=10, state=tk.DISABLED)
        self.log_text.grid(row=7, column=1, columnspan=4, pady=5, sticky="w")

        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.main_frame, variable=self.progress, maximum=100)
        self.progress_bar.grid(row=8, column=1, columnspan=4, sticky="ew", pady=5)

        self.start_button = ttk.Button(self.main_frame, text="Запустить резервное копирование", command=self.start_backup)
        self.start_button.grid(row=9, column=1, pady=10)

        self.stop_button = ttk.Button(self.main_frame, text="Остановить", command=self.stop_backup, state=tk.DISABLED)
        self.stop_button.grid(row=9, column=2, pady=10)

        self.save_log_button = ttk.Button(self.main_frame, text="Сохранить лог", command=self.save_log)
        self.save_log_button.grid(row=9, column=3, pady=10)

    # --- Методы управления списками ---
    def add_source(self):
        directory = filedialog.askdirectory()
        if directory and directory not in self.source_dirs:
            self.source_dirs.append(directory)
            self._log(f"Добавлен каталог: {directory}")
            self.update_sources_listbox()

    def add_file(self):
        files = filedialog.askopenfilenames()
        if files:
            added = 0
            for f in files:
                if f not in self.source_files:
                    if os.path.exists(f):
                        self.source_files.append(f)
                        added += 1
                    else:
                        self._log(f"Файл не найден: {f}")
            if added > 0:
                self._log(f"Добавлено файлов: {added}")
                self.update_sources_listbox()

    def remove_source(self):
        selection = self.sources_text.curselection()
        if not selection:
            messagebox.showinfo("Удаление", "Выберите элемент для удаления.")
            return
        index = selection[0]
        total_dirs = len(self.source_dirs)
        if index < total_dirs:
            removed = self.source_dirs.pop(index)
            self._log(f"Удалён каталог: {removed}")
        else:
            removed = self.source_files.pop(index - total_dirs)
            self._log(f"Удалён файл: {removed}")
        self.update_sources_listbox()

    def clear_sources(self):
        if self.source_dirs or self.source_files:
            if not messagebox.askyesno("Подтверждение", "Очистить списки исходных каталогов и файлов?"):
                return
        self.source_dirs.clear()
        self.source_files.clear()
        self._log("Списки исходных каталогов и файлов очищены")
        self.update_sources_listbox()

    def update_sources_listbox(self):
        self.sources_text.delete(0, tk.END)
        for d in self.source_dirs:
            self.sources_text.insert(tk.END, f"[DIR]  {d}")
        for f in self.source_files:
            self.sources_text.insert(tk.END, f"[FILE] {f}")

    def select_target(self):
        directory = filedialog.askdirectory()
        if directory:
            self.target_dir = directory
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, directory)
            self._log(f"Выбран каталог для резервных копий: {directory}")

    # --- Запуск резервного копирования ---
    def start_backup(self):
        try:
            hours = int(self.hours_entry.get())
            weeks = int(self.weeks_entry.get())
            compression = int(self.compression_entry.get())
            if hours < 0 or weeks < 0 or not (0 <= compression <= 9):
                raise ValueError
            if hours == 0 and weeks == 0:
                messagebox.showerror("Ошибка", "Интервал копирования не может быть равен нулю")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Интервал и уровень сжатия должны быть целыми числами в корректном диапазоне")
            return

        self.interval_hours = hours
        self.interval_weeks = weeks
        self.compression_level = compression

        exclude_text = self.exclude_entry.get().strip()
        self.exclude_patterns = [p.strip() for p in exclude_text.split(",") if p.strip()]

        if not self.source_dirs and not self.source_files:
            messagebox.showerror("Ошибка", "Не выбран ни один исходный каталог или файл")
            return
        for d in self.source_dirs:
            if not os.path.isdir(d):
                messagebox.showerror("Ошибка", f"Исходный каталог не существует:\n{d}")
                return
        for f in self.source_files:
            if not os.path.isfile(f):
                messagebox.showerror("Ошибка", f"Исходный файл не существует:\n{f}")
                return

        self.target_dir = self.target_entry.get()
        if not os.path.isdir(self.target_dir):
            messagebox.showerror("Ошибка", "Каталог для резервных копий не выбран или не существует")
            return

        # Проверка свободного места на диске
        try:
            total, used, free = shutil.disk_usage(self.target_dir)
            if free < 100 * 1024 * 1024:  # менее 100 МБ свободно
                if not messagebox.askyesno("Внимание", "Свободного места на диске мало. Продолжить?"):
                    return
        except Exception as e:
            self._log(f"Ошибка при проверке свободного места: {e}")

        self.stop_event.clear()
        self.backup_thread = threading.Thread(target=self.run_backup_schedule, daemon=True)
        self.backup_thread.start()

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.running = True
        self._log("Автоматическое резервное копирование запущено")
        self._show_notification("Резервное копирование запущено")
        self.status_text.set("Статус: Резервное копирование запущено")
        messagebox.showinfo("Запуск", "Автоматическое резервное копирование запущено")

        self._save_settings()
        self._update_next_backup_time()

    def stop_backup(self):
        self.stop_event.set()
        if self.backup_thread and self.backup_thread.is_alive():
            self.backup_thread.join()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.running = False
        self._log("Резервное копирование остановлено")
        self._show_notification("Резервное копирование остановлено")
        self.status_text.set("Статус: Резервное копирование остановлено")
        messagebox.showinfo("Остановка", "Резервное копирование остановлено")
        self.next_backup_time = None
        self._update_next_backup_label()

    # --- Основной цикл резервного копирования ---
    def run_backup_schedule(self):
        interval_seconds = (self.interval_weeks * 7 * 24 + self.interval_hours) * 3600
        if interval_seconds <= 0:
            interval_seconds = 3600

        while not self.stop_event.is_set():
            try:
                self.create_backup()
            except Exception as e:
                self._log(f"Ошибка в процессе создания резервной копии: {e}")
            # Обновляем время следующего запуска
            self.next_backup_time = time.time() + interval_seconds
            self._update_next_backup_label()
            if self.stop_event.wait(interval_seconds):
                break

    # --- Обновление отображения следующего запуска ---
    def _update_next_backup_label(self):
        if self.next_backup_time:
            next_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.next_backup_time))
            self.next_backup_label.config(text=next_time_str)
        else:
            self.next_backup_label.config(text="не запланировано")

    def _update_next_backup_time(self):
        interval_seconds = (self.interval_weeks * 7 * 24 + self.interval_hours) * 3600
        self.next_backup_time = time.time() + interval_seconds
        self._update_next_backup_label()

    def _update_status_loop(self):
        # Обновление статуса и следующего запуска каждую секунду
        if self.running and self.next_backup_time:
            remaining = int(self.next_backup_time - time.time())
            if remaining > 0:
                self.status_text.set(f"Статус: Резервное копирование запущено. Следующий запуск через {remaining} сек.")
            else:
                self.status_text.set("Статус: Резервное копирование выполняется...")
        elif not self.running:
            self.status_text.set("Статус: Ожидание запуска")
        self.root.after(1000, self._update_status_loop)

    # --- Создание резервной копии ---
    def create_backup(self):
        date_folder = time.strftime("%Y%m%d")
        backup_dir = os.path.join(self.target_dir, date_folder)
        if not os.path.exists(backup_dir):
            try:
                os.makedirs(backup_dir)
                self._log(f"Создан каталог для резервных копий: {backup_dir}")
            except Exception as e:
                self._log(f"Ошибка при создании каталога резервных копий: {e}")
                self._show_notification(f"Ошибка при создании каталога: {e}")
                return

        archive_name = time.strftime("%H%M%S") + ".zip"
        archive_path = os.path.join(backup_dir, archive_name)

        try:
            compression = ZIP_DEFLATED if self.compression_level > 0 else ZIP_STORED
            with ZipFile(archive_path, 'w', compression,
                         compresslevel=self.compression_level if compression == ZIP_DEFLATED else None) as zipf:
                total_files = 0
                processed_files = 0
                all_files = 0

                for source_dir in self.source_dirs:
                    for foldername, subfolders, filenames in os.walk(source_dir):
                        subfolders[:] = [d for d in subfolders if not self._is_excluded(d)]
                        all_files += len(filenames)
                all_files += len(self.source_files)

                for source_dir in self.source_dirs:
                    for foldername, subfolders, filenames in os.walk(source_dir):
                        subfolders[:] = [d for d in subfolders if not self._is_excluded(d)]
                        for filename in filenames:
                            if self._is_excluded(filename):
                                continue
                            filepath = os.path.join(foldername, filename)
                            try:
                                relative_path = os.path.relpath(filepath, source_dir)
                                source_dir_name = os.path.basename(os.path.normpath(source_dir))
                                arcname = os.path.join(source_dir_name, relative_path)
                                zipf.write(filepath, arcname)
                                total_files += 1
                                self._log(f"Добавлен в архив: {filepath}")
                            except Exception as e:
                                self._log(f"Ошибка при добавлении файла {filepath}: {e}")

                            processed_files += 1
                            self._update_progress(processed_files, all_files)

                for filepath in self.source_files:
                    if not os.path.isfile(filepath):
                        self._log(f"Файл не найден и пропущен: {filepath}")
                        continue
                    filename = os.path.basename(filepath)
                    if self._is_excluded(filename):
                        self._log(f"Файл исключён по маске: {filepath}")
                        continue
                    try:
                        arcname = os.path.join("files", filename)
                        zipf.write(filepath, arcname)
                        total_files += 1
                        self._log(f"Добавлен в архив: {filepath}")
                    except Exception as e:
                        self._log(f"Ошибка при добавлении файла {filepath}: {e}")

                    processed_files += 1
                    self._update_progress(processed_files, all_files)

            self._log(f"Резервная копия создана: {archive_path} (файлов: {total_files})")
            self._show_notification(f"Резервная копия создана: {archive_path} (файлов: {total_files})")
        except Exception as e:
            self._log(f"Ошибка при создании резервной копии: {e}")
            self._show_notification(f"Ошибка при создании резервной копии: {e}")
        finally:
            self.progress.set(0)
            self.root.update_idletasks()

    def _update_progress(self, processed, total):
        if total > 0:
            progress = (processed / total) * 100
            self.progress.set(progress)
            self.root.update_idletasks()

    def _is_excluded(self, name):
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    def _log(self, message):
        self.log_queue.put(message)

    def _process_log_queue(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                full_message = f"[{timestamp}] {message}\n"

                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, full_message)
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)

                logging.info(message)
                print(full_message.strip())
        except Empty:
            pass
        self.root.after(100, self._process_log_queue)

    def save_log(self):
        log_content = self.log_text.get('1.0', tk.END)
        if not log_content.strip():
            messagebox.showinfo("Лог пуст", "В логе нет данных для сохранения.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
                                                 title="Сохранить лог")
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(log_content)
                messagebox.showinfo("Успех", f"Лог успешно сохранён в:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить лог:\n{e}")

    def _save_settings(self):
        settings = {
            "source_dirs": self.source_dirs,
            "source_files": self.source_files,
            "target_dir": self.target_dir,
            "interval_hours": self.interval_hours,
            "interval_weeks": self.interval_weeks,
            "compression_level": self.compression_level,
            "exclude_patterns": self.exclude_patterns,
        }
        # Резервное копирование файла настроек
        try:
            if os.path.isfile(SETTINGS_FILE):
                shutil.copy2(SETTINGS_FILE, SETTINGS_BACKUP_FILE)
        except Exception as e:
            self._log(f"Ошибка при создании резервной копии настроек: {e}")

        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self._log("Настройки сохранены")
        except Exception as e:
            self._log(f"Ошибка при сохранении настроек: {e}")

    def _load_settings(self):
        if os.path.isfile(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                self.source_dirs = settings.get("source_dirs", [])
                self.source_files = settings.get("source_files", [])
                self.target_dir = settings.get("target_dir", "")
                self.interval_hours = settings.get("interval_hours", 1)
                self.interval_weeks = settings.get("interval_weeks", 0)
                self.compression_level = settings.get("compression_level", 6)
                self.exclude_patterns = settings.get("exclude_patterns", [])

                self.update_sources_listbox()
                self.target_entry.delete(0, tk.END)
                self.target_entry.insert(0, self.target_dir)
                self.hours_entry.delete(0, tk.END)
                self.hours_entry.insert(0, str(self.interval_hours))
                self.weeks_entry.delete(0, tk.END)
                self.weeks_entry.insert(0, str(self.interval_weeks))
                self.compression_entry.delete(0, tk.END)
                self.compression_entry.insert(0, str(self.compression_level))
                self.exclude_entry.delete(0, tk.END)
                self.exclude_entry.insert(0, ", ".join(self.exclude_patterns))

                self._log("Настройки загружены")
            except Exception as e:
                self._log(f"Ошибка при загрузке настроек: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use('clam')
    root.minsize(700, 500)

    app = BackupApp(root)

    def on_deiconify(event):
        root.overrideredirect(True)

    root.bind("<Map>", on_deiconify)

    root.mainloop()
