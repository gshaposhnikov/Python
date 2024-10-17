import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import threading
import time
import platform
import os
from datetime import datetime
import sqlite3
import xlwt # Библиотека для создания XLS файлов
import matplotlib.pyplot as plt # Библиотека для создания графиков


class NetworkMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Сетевой монитор с возможностью логирования v2.5.5.5 Stable")
        self.devices = {}
        self.notification_windows = {}
        self.notification_intervals = {
            "Не отправлять": None,
            "3 секунды": 3,
            "5 секунд": 5,
            "15 секунд": 15,
            "30 секунд": 30,
            "1 минута": 1 * 60,
            "3 минуты": 3 * 60,
            "5 минут": 5 * 60,
            "15 минут": 15 * 60,
            "30 минут": 30 * 60,
            "1 час": 60 * 60,
            "2 часа": 2 * 60 * 60,
            "3 часа": 3 * 60 * 60,
            "5 часов": 5 * 60 * 60,
            "10 часов": 10 * 60 * 60,
            "20 часов": 20 * 60 * 60,
            "24 часов": 24 * 60 * 60,
            "48 часов": 48 * 60 * 60
        }

        self.lock = threading.Lock()

        self.frame = tk.Frame(root)
        self.frame.pack(pady=10)

        self.device_list_frame = tk.Frame(self.frame)
        self.device_list_frame.pack(pady=10)

        # Заголовки для списка устройств
        self.header_frame = tk.Frame(self.device_list_frame)
        self.header_frame.grid(row=0, column=0, sticky="w")

        tk.Label(self.header_frame, text="Устройство", borderwidth=1, relief="solid", width=25,
                 font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, sticky="w")
        tk.Label(self.header_frame, text="Время", borderwidth=1, relief="solid", width=10,
                 font=("Arial", 10, "bold")).grid(row=0, column=1, padx=14, sticky="w")
        tk.Label(self.header_frame, text="Online", borderwidth=1, relief="solid", width=10,
                 font=("Arial", 10, "bold")).grid(row=0, column=2, padx=7, sticky="w")
        tk.Label(self.header_frame, text="Offline", borderwidth=1, relief="solid", width=12,
                 font=("Arial", 10, "bold")).grid(row=0, column=3, padx=10, sticky="w")
        tk.Label(self.header_frame, text="Действие", borderwidth=1, relief="solid", width=10,
                 font=("Arial", 10, "bold")).grid(row=0, column=4, padx=25, sticky="w")

        # Комбобокс для включения логирования
        self.logging_frame = tk.Frame(self.frame)
        self.logging_frame.pack(pady=5)
        self.logging_label = tk.Label(self.logging_frame, text="Логирование:")
        self.logging_label.pack(side=tk.LEFT, padx=5)
        self.logging_combobox = ttk.Combobox(self.logging_frame, values=["Вкл", "Выкл"], state="readonly", width=10)
        self.logging_combobox.pack(side=tk.LEFT, padx=5)

        # Кнопка для формирования отчета
        self.report_frame = tk.Frame(self.frame)
        self.report_frame.pack(pady=10)

        self.report_button = tk.Button(self.report_frame, text="Сформировать отчет по логам", command=self.generate_report, state=tk.DISABLED)
        self.report_button.grid(row=0, column=0, padx=5)

        # Загрузка состояния логирования
        self.load_logging_state()

        # Инициализация базы данных
        self.init_db()

        self.load_devices()

        # Горизонтальная черта
        self.separator = ttk.Separator(self.frame, orient='horizontal')
        self.separator.pack(fill='x', pady=10)

        self.add_device_frame = tk.Frame(self.frame)
        self.add_device_frame.pack(pady=10)

        self.info_label = tk.Label(self.add_device_frame, text="Добавить устройство:")
        self.info_label.grid(row=0, column=0, padx=5)

        self.info_entry = tk.Entry(self.add_device_frame)
        self.info_entry.grid(row=0, column=1, padx=5)
        self.info_entry.bind("<KeyRelease>", self.check_entries)

        self.device_label = tk.Label(self.add_device_frame, text="IP:")
        self.device_label.grid(row=0, column=2, padx=5)

        self.ip_entries = [tk.Entry(self.add_device_frame, width=3, validate='key', validatecommand=(self.root.register(self.validate_ip_section), '%P')) for _ in range(4)]
        for i, ip_entry in enumerate(self.ip_entries):
            ip_entry.grid(row=0, column=3 + i, padx=2)
            ip_entry.bind("<KeyRelease>", self.check_entries)

        self.add_button = tk.Button(self.add_device_frame, text="Добавить устройство", command=self.add_device, state=tk.DISABLED)
        self.add_button.grid(row=0, column=7, padx=5)

        self.update_status_thread = threading.Thread(target=self.update_status)
        self.update_status_thread.daemon = True
        self.update_status_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Создание стиля для кнопок с эффектом стекла
        style = ttk.Style()
        style.configure("Glass.TButton",
                        background="lightblue",
                        foreground="black",
                        relief="flat",
                        padding=5,
                        font=("Arial", 10, "bold"))
        style.map("Glass.TButton",
                 background=[("active", "blue")],
                 relief=[("pressed", "sunken")])

        self.check_report_button_state()

    def validate_ip_section(self, value):
        return value.isdigit() and 0 <= int(value) <= 255 or value == ""

    def check_entries(self, event=None):
        if self.info_entry.get() and all(entry.get() for entry in self.ip_entries):
            self.add_button.config(state=tk.NORMAL)
        else:
            self.add_button.config(state=tk.DISABLED)

    def get_ip_address(self):
        return '.'.join(entry.get() for entry in self.ip_entries)

    def add_device(self):
        info = self.info_entry.get()
        ip = self.get_ip_address()
        if ip and ip not in self.devices:
            row = len(self.devices) + 1
            device_frame = tk.Frame(self.device_list_frame)
            device_frame.grid(row=row, column=0, sticky="w", pady=5)

            device_label = tk.Label(device_frame, text=f"{info} ({ip})", borderwidth=1, relief="solid", width=25)
            device_label.grid(row=0, column=0, padx=5, sticky="w")

            time_label = tk.Label(device_frame, text="0 д 0 ч 0 мин", borderwidth=1, relief="solid", width=12)
            time_label.grid(row=0, column=1, padx=5, sticky="w")

            expected_state_combobox = ttk.Combobox(device_frame, values=["Вкл", "Выкл"], state="readonly", width=7)
            expected_state_combobox.current(1)
            expected_state_combobox.grid(row=0, column=2, padx=3, sticky="w")

            interval_combobox = ttk.Combobox(device_frame, values=list(self.notification_intervals.keys()), state="readonly", width=23)
            interval_combobox.current(0)
            interval_combobox.grid(row=0, column=3, padx=5, sticky="w")

            remove_button = ttk.Button(device_frame, text="Удалить", command=lambda: self.confirm_remove_device(info, ip, device_frame), style="Glass.TButton")
            remove_button.grid(row=0, column=4, padx=5, sticky="w")

            initial_status = "Online" if self.ping_device(ip) else "Offline"
            with self.lock:
                self.devices[ip] = (device_frame, device_label, time_label, info, interval_combobox, expected_state_combobox, time.time(), initial_status, False)

            # Логирование начального состояния
            if self.logging_combobox.get() == "Вкл":
                self.log_device_status(info, ip, initial_status)

            for entry in self.ip_entries:
                entry.delete(0, tk.END)
            self.info_entry.delete(0, tk.END)
            self.add_button.config(state=tk.DISABLED)
        else:
            messagebox.showwarning("Предупреждение", "IP или информация об устройстве не введены или устройство уже добавлено.")

    def confirm_remove_device(self, info, ip, frame):
        if messagebox.askyesno("Подтверждение удаления", f"Вы уверены, что хотите удалить устройство {info} ({ip})?"):
            self.remove_device(ip, frame)

    def remove_device(self, ip, frame):
        frame.destroy()
        with self.lock:
            del self.devices[ip]
            if ip in self.notification_windows:
                for window in self.notification_windows[ip]:
                    window.destroy()
                del self.notification_windows[ip]
        self.rearrange_devices()

    def rearrange_devices(self):
        with self.lock:
            for i, (ip, (frame, _, _, _, _, _, _, _, _)) in enumerate(self.devices.items()):
                frame.grid(row=i + 1, column=0, sticky="w", pady=5)

    def ping_device(self, ip):
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, "1", ip]
        try:
            if platform.system().lower() == "windows":
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout
            if platform.system().lower() == "windows":
                return "TTL=" in output
            else:
                return "1 packets transmitted, 1 received" in output
        except subprocess.CalledProcessError:
            return False

    def update_status(self):
        while True:
            with self.lock:
                devices_copy = self.devices.copy()
            for ip, (frame, device_label, time_label, info, interval_combobox, expected_state_combobox, start_time, last_status, notified) in devices_copy.items():
                current_status = "Online" if self.ping_device(ip) else "Offline"
                if current_status != last_status:
                    start_time = time.time()
                    notified = False
                    with self.lock:
                        self.devices[ip] = (frame, device_label, time_label, info, interval_combobox, expected_state_combobox, start_time, current_status, notified)
                    # Логирование изменений статуса
                    if self.logging_combobox.get() == "Вкл":
                        self.log_device_status(info, ip, current_status)

                elapsed_time = int(time.time() - start_time)
                days, remainder = divmod(elapsed_time, 86400)
                hours, minutes = divmod(remainder // 60, 60)
                self.root.after(0, self.update_time_label, time_label, days, hours, minutes)

                if current_status == "Online":
                    self.root.after(0, self.update_device_label, device_label, info, ip, "Lime") # Цвет устройства Online
                    if last_status == "Offline" and expected_state_combobox.get() == "Вкл":
                        self.root.after(0, self.show_online_notification, info, ip)
                else:
                    self.root.after(0, self.update_device_label, device_label, info, ip, "Orange") # Цвет устройства Offline
                    interval = self.notification_intervals[interval_combobox.get()]
                    if interval is not None and not notified and elapsed_time >= interval:
                        self.root.after(0, self.send_notification, ip, info)
                        notified = True
                        with self.lock:
                            self.devices[ip] = (
                            frame, device_label, time_label, info, interval_combobox, expected_state_combobox, start_time, current_status, notified)
            time.sleep(3)

    def update_device_label(self, label, info, ip, bg):
        if label.winfo_exists():
            status = "Online" if bg == "Lime" else "Offline"
            label.config(text=f"{info} ({ip}) - {status}", bg=bg)

    def update_time_label(self, label, days, hours, minutes):
        if label.winfo_exists():
            label.config(text=f"{days} д {hours} ч {minutes} мин")

    def send_notification(self, ip, info):
        with self.lock:
            if ip in self.devices and self.devices[ip][7] == "Offline":
                notification_window = tk.Toplevel(self.root)
                notification_window.title("Уведомление Offline")
                notification_window.attributes("-topmost", True)
                notification_window.protocol("WM_DELETE_WINDOW", lambda: self.close_notification(ip, notification_window))
                # Форматирование уведомления о недоступности
                message = f"{info}\n{ip}\n❌\nOffline\n{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
                tk.Label(notification_window, text=message, fg="red", font=("Arial", 20, "bold")).pack(pady=20, padx=20) # Шрифт и размер формы "Уведомление Offline"

                if ip not in self.notification_windows:
                    self.notification_windows[ip] = []
                self.notification_windows[ip].append(notification_window)

    def show_online_notification(self, info, ip):
        # Форматирование уведомления о появлении в сети
        online_window = tk.Toplevel(self.root)
        online_window.title("Уведомление Online")
        online_window.attributes("-topmost", True)
        message = f"{info}\n{ip}\n✔️\nOnline\n{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
        tk.Label(online_window, text=message, fg="green", font=("Arial", 20, "bold")).pack(pady=20, padx=20) # Шрифт и размер формы "Уведомление Online"
        online_window.protocol("WM_DELETE_WINDOW", lambda: self.close_notification(ip, online_window))

        if ip not in self.notification_windows:
            self.notification_windows[ip] = []
        self.notification_windows[ip].append(online_window)

    def close_notification(self, ip, window):
        if ip in self.notification_windows:
            window.destroy()
            with self.lock:
                self.notification_windows[ip].remove(window)
                if not self.notification_windows[ip]:
                    del self.notification_windows[ip]

    def save_devices(self):
        with open("devices.txt", "w") as f:
            with self.lock:
                for ip, (_, _, _, info, interval_combobox, expected_state_combobox, _, _, _) in self.devices.items():
                    f.write(f"{info},{ip},{interval_combobox.get()},{expected_state_combobox.get()}\n")

    def load_devices(self):
        if os.path.exists("devices.txt"):
            with open("devices.txt", "r") as f:
                for line in f:
                    parts = line.strip().split(",", 3)
                    if len(parts) == 4:
                        info, ip, interval, expected_state = parts
                        row = len(self.devices) + 1
                        device_frame = tk.Frame(self.device_list_frame)
                        device_frame.grid(row=row, column=0, sticky="w", pady=5)

                        device_label = tk.Label(device_frame, text=f"{info} ({ip})", borderwidth=1, relief="solid", width=30)
                        device_label.grid(row=0, column=0, padx=5, sticky="w")

                        time_label = tk.Label(device_frame, text="0 д 0 ч 0 мин", borderwidth=1, relief="solid", width=12)
                        time_label.grid(row=0, column=1, padx=5, sticky="w")

                        expected_state_combobox = ttk.Combobox(device_frame, values=["Вкл", "Выкл"], state="readonly", width=12)
                        expected_state_combobox.set(expected_state)
                        expected_state_combobox.grid(row=0, column=2, padx=5, sticky="w")

                        interval_combobox = ttk.Combobox(device_frame, values=list(self.notification_intervals.keys()), state="readonly", width=14)
                        interval_combobox.set(interval)
                        interval_combobox.grid(row=0, column=3, padx=5, sticky="w")

                        remove_button = ttk.Button(device_frame, text="Удалить", command=lambda ip=ip, frame=device_frame, info=info: self.confirm_remove_device(info, ip, frame), style="Glass.TButton")
                        remove_button.grid(row=0, column=4, padx=25, sticky="w")

                        initial_status = "Online" if self.ping_device(ip) else "Offline"
                        with self.lock:
                            self.devices[ip] = (device_frame, device_label, time_label, info, interval_combobox, expected_state_combobox, time.time(), initial_status, False)

                        # Логирование начального состояния
                        if self.logging_combobox.get() == "Вкл":
                            self.log_device_status(info, ip, initial_status)
                    else:
                        print(f"Некорректная строка: {line.strip()}")

    def save_logging_state(self):
        # Сохранение состояния логирования в файл
        with open("logging_state.txt", "w") as f:
            f.write(self.logging_combobox.get())

    def load_logging_state(self):
        # Загрузка состояния логирования из файла
        if os.path.exists("logging_state.txt"):
            with open("logging_state.txt", "r") as f:
                state = f.read().strip()
                if state in ["Вкл", "Выкл"]:
                    self.logging_combobox.set(state)
                else:
                    self.logging_combobox.set("Выкл")
        else:
            self.logging_combobox.set("Выкл")

    def init_db(self):
        # Инициализация базы данных SQLite
        self.conn = sqlite3.connect('device_logs.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT,
                ip_address TEXT,
                timestamp TEXT,
                status TEXT
            )
        ''')
        self.conn.commit()

    def log_device_status(self, device_name, ip_address, status):
        # Логирование статуса устройства в базу данных
        conn = sqlite3.connect('device_logs.db')
        cursor = conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO logs (device_name, ip_address, timestamp, status)
            VALUES (?, ?, ?, ?)
        ''', (device_name, ip_address, timestamp, status))
        conn.commit()
        conn.close()
        self.root.after(0, self.check_report_button_state)

    def check_report_button_state(self):
        # Проверка состояния кнопки "Сформировать отчет по логам"
        conn = sqlite3.connect('device_logs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM logs')
        count = cursor.fetchone()[0]
        conn.close()
        if count > 0:
            self.report_button.config(state=tk.NORMAL)
        else:
            self.report_button.config(state=tk.DISABLED)

    def generate_report(self):
        # Генерация отчета в формате XLS
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Device Logs')

        # Заголовки с обрамлением
        headers = ['ID', 'Device Name', 'IP Address', 'Timestamp', 'Status']
        header_style = xlwt.easyxf('border: left thin, right thin, top thin, bottom thin; font: bold on;')
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_style)

        # Закрепление первой строки
        sheet.set_panes_frozen(True)
        sheet.set_horz_split_pos(1)

        # Данные из базы
        conn = sqlite3.connect('device_logs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM logs')
        rows = cursor.fetchall()
        conn.close()

        # Создание стиля для ячеек
        online_style = xlwt.easyxf('border: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour lime;')
        offline_style = xlwt.easyxf('border: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour orange;')
        default_style = xlwt.easyxf('border: left thin, right thin, top thin, bottom thin;')

        for row_idx, row in enumerate(rows, start=1):
            for col_idx, value in enumerate(row):
                if col_idx == 4: # Столбец "Status"
                    style = online_style if value == 'Online' else offline_style
                elif col_idx == 1: # Столбец "Device Name"
                    status = row[4] # Получаем статус из столбца "Status"
                    style = online_style if status == 'Online' else offline_style
                else:
                    style = default_style
                sheet.write(row_idx, col_idx, value, style)

        # Установка ширины колонок
        sheet.col(0).width = 1500 # Уменьшение ширины колонки ID
        sheet.col(1).width = 8000 # Увеличение ширины колонки Device Name
        sheet.col(2).width = 5000 # Увеличение ширины колонки IP Address
        sheet.col(3).width = 6000 # Увеличение ширины колонки Timestamp
        sheet.col(4).width = 3000 # Увеличение ширины колонки Status

        # Сохранение файла
        report_filename = f"device_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xls"
        workbook.save(report_filename)
        messagebox.showinfo("Отчет сформирован", f"Отчет успешно сформирован и сохранен как {report_filename}")

        # Генерация графика
        self.generate_chart()

    def generate_chart(self):
        # Подключение к базе данных
        conn = sqlite3.connect('device_logs.db')
        cursor = conn.cursor()

        # Получение данных для графика
        cursor.execute('''
            SELECT device_name, SUM(CASE WHEN status = 'Online' THEN 1 ELSE 0 END) as online_count,
                 SUM(CASE WHEN status = 'Offline' THEN 1 ELSE 0 END) as offline_count
            FROM logs
            GROUP BY device_name
        ''')
        data = cursor.fetchall()

        # Получение первой и последней даты из базы данных
        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM logs')
        date_range = cursor.fetchone()
        conn.close()

        # Проверка наличия данных
        if not data:
            messagebox.showwarning("Недостаточно данных", "Недостаточно данных для построения графика.")
            return

        # Подготовка данных для графика
        device_names = [row[0] for row in data]
        online_counts = [row[1] for row in data]
        offline_counts = [row[2] for row in data]

        # Построение графика
        plt.figure(figsize=(12, 6))
        bar_width = 0.35
        index = range(len(device_names))

        plt.bar(index, online_counts, bar_width, label='Online', color='lime') # Цвет графика Online
        plt.bar([i + bar_width for i in index], offline_counts, bar_width, label='Offline', color='orange') # Цвет графика Offline

        plt.xlabel('Устройства')
        plt.ylabel('Количество событий онлайн или оффлайн')
        # Изменение названия графика с указанием периода без времени
        plt.title(f"Аналитика работы устройств за период с {date_range[0][:10]} по {date_range[1][:10]}")
        plt.xticks([i + bar_width / 2 for i in index], device_names, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()

        # Сохранение графика
        chart_filename = f"device_activity_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(chart_filename)
        plt.show()

        messagebox.showinfo("График сформирован", f"График успешно сформирован и сохранен как {chart_filename}")

    def on_closing(self):
        # Сохранение устройств и состояния логирования перед закрытием
        self.save_devices()
        self.save_logging_state()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkMonitor(root)
    root.mainloop()