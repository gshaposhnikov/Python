import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import threading
import time
import platform
import os

class NetworkMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Сетевой монитор v2.3.0")
        self.devices = {}
        self.unreachable_devices = {}
        self.notification_windows = {}
        self.notification_intervals = {
            "Не отправлять уведомления": None,
            "Через 1 минуту": 1 * 60,
            "Через 3 минуты": 3 * 60,
            "Через 5 минут": 5 * 60,
            "Через 15 минут": 15 * 60,
            "Через 30 минут": 30 * 60,
            "Через 1 час": 60 * 60,
            "Через 2 часа": 2 * 60 * 60,
            "Через 3 часа": 3 * 60 * 60,
            "Через 5 часов": 5 * 60 * 60,
            "Через 10 часов": 10 * 60 * 60,
            "Через 20 часов": 20 * 60 * 60,
            "Через 24 часов": 24 * 60 * 60,
            "Через 48 часов": 48 * 60 * 60
        }

        self.lock = threading.Lock()

        self.frame = tk.Frame(root)
        self.frame.pack(pady=10)

        self.device_list_frame = tk.Frame(self.frame)
        self.device_list_frame.pack(pady=10)

        # Заголовки для списка устройств
        self.header_frame = tk.Frame(self.device_list_frame)
        self.header_frame.grid(row=0, column=0, sticky="w")

        tk.Label(self.header_frame, text="Информация об устройстве", borderwidth=1, relief="solid", width=30).grid(row=0, column=0, padx=5, sticky="w")
        tk.Label(self.header_frame, text="Статус", borderwidth=1, relief="solid", width=15).grid(row=0, column=1, padx=5, sticky="w")
        tk.Label(self.header_frame, text="Интервал уведомлений", borderwidth=1, relief="solid", width=23).grid(row=0, column=2, padx=5, sticky="w")
        tk.Label(self.header_frame, text="Действие", borderwidth=1, relief="solid", width=10).grid(row=0, column=3, padx=5, sticky="w")

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
                        font=("Helvetica", 10, "bold"))
        style.map("Glass.TButton",
                 background=[("active", "blue")],
                 relief=[("pressed", "sunken")])

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

            device_label = tk.Label(device_frame, text=f"{info} ({ip})", borderwidth=1, relief="solid", width=30)
            device_label.grid(row=0, column=0, padx=5, sticky="w")

            status_label = tk.Label(device_frame, text="Проверка...", bg="yellow", borderwidth=1, relief="solid", width=15)
            status_label.grid(row=0, column=1, padx=5, sticky="w")

            interval_combobox = ttk.Combobox(device_frame, values=list(self.notification_intervals.keys()), state="readonly", width=23)
            interval_combobox.current(0)
            interval_combobox.grid(row=0, column=2, padx=5, sticky="w")

            remove_button = ttk.Button(device_frame, text="Удалить", command=lambda: self.confirm_remove_device(info, ip, device_frame), style="Glass.TButton")
            remove_button.grid(row=0, column=3, padx=5, sticky="w")

            with self.lock:
                self.devices[ip] = (device_frame, status_label, info, interval_combobox)
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
            if ip in self.unreachable_devices:
                self.unreachable_devices[ip].cancel()
                del self.unreachable_devices[ip]
            if ip in self.notification_windows:
                self.notification_windows[ip].destroy()
                del self.notification_windows[ip]
        self.rearrange_devices()

    def rearrange_devices(self):
        with self.lock:
            for i, (ip, (frame, status_label, info, interval_combobox)) in enumerate(self.devices.items()):
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
            for ip, (frame, status_label, info, interval_combobox) in devices_copy.items():
                if self.ping_device(ip):
                    self.root.after(0, self.update_label, status_label, "Online", "green")
                    if ip in self.unreachable_devices:
                        self.unreachable_devices[ip].cancel()
                        with self.lock:
                            del self.unreachable_devices[ip]
                    if ip in self.notification_windows:
                        self.notification_windows[ip].destroy()
                        with self.lock:
                            del self.notification_windows[ip]
                else:
                    self.root.after(0, self.update_label, status_label, "Offline", "red")
                    if ip not in self.unreachable_devices:
                        if interval_combobox.winfo_exists():
                            interval = self.notification_intervals[interval_combobox.get()]
                            if interval:
                                self.unreachable_devices[ip] = threading.Timer(interval, self.send_notification, args=(ip, info))
                                self.unreachable_devices[ip].start()
                    else:
                        self.root.after(0, self.update_notification, ip, info)
            time.sleep(3)

    def update_label(self, label, text, bg):
        if label.winfo_exists():
            label.config(text=text, bg=bg)

    def send_notification(self, ip, info):
        with self.lock:
            if ip in self.devices and self.devices[ip][1].cget("text") == "Offline":
                if ip not in self.notification_windows:
                    self.notification_windows[ip] = tk.Toplevel(self.root)
                    self.notification_windows[ip].title("Уведомление")
                    self.notification_windows[ip].attributes("-topmost", True)
                    self.notification_windows[ip].protocol("WM_DELETE_WINDOW", lambda: self.close_notification(ip))
                    self.notification_windows[ip].label = tk.Label(self.notification_windows[ip], text=f"Устройство {info} ({ip}) недоступно\nв течение: 0 секунд.")
                    self.notification_windows[ip].label.pack(pady=10, padx=10)
                    self.notification_windows[ip].start_time = time.time()
                else:
                    self.update_notification(ip, info)

                # Запускаем таймер для повторного уведомления, если устройство остается недоступным
                interval = self.notification_intervals[self.devices[ip][3].get()]
                if interval:
                    self.unreachable_devices[ip] = threading.Timer(interval, self.send_notification, args=(ip, info))
                    self.unreachable_devices[ip].start()

    def update_notification(self, ip, info):
        if ip in self.notification_windows:
            elapsed_time = int(time.time() - self.notification_windows[ip].start_time)
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.notification_windows[ip].label.config(text=f"Устройство {info} ({ip}) недоступно\nв течение: {hours} час. {minutes} мин. {seconds} сек.")

    def close_notification(self, ip):
        if ip in self.notification_windows:
            self.notification_windows[ip].destroy()
            with self.lock:
                del self.notification_windows[ip]

    def save_devices(self):
        with open("devices.txt", "w") as f:
            with self.lock:
                for ip, (_, _, info, interval_combobox) in self.devices.items():
                    f.write(f"{info},{ip},{interval_combobox.get()}\n")

    def load_devices(self):
        if os.path.exists("devices.txt"):
            with open("devices.txt", "r") as f:
                for line in f:
                    parts = line.strip().split(",", 2)
                    if len(parts) == 3:
                        info, ip, interval = parts
                        row = len(self.devices) + 1
                        device_frame = tk.Frame(self.device_list_frame)
                        device_frame.grid(row=row, column=0, sticky="w", pady=5)

                        device_label = tk.Label(device_frame, text=f"{info} ({ip})", borderwidth=1, relief="solid", width=30)
                        device_label.grid(row=0, column=0, padx=5, sticky="w")

                        status_label = tk.Label(device_frame, text="Проверка...", bg="yellow", borderwidth=1, relief="solid", width=15)
                        status_label.grid(row=0, column=1, padx=5, sticky="w")

                        interval_combobox = ttk.Combobox(device_frame, values=list(self.notification_intervals.keys()), state="readonly", width=23)
                        interval_combobox.set(interval)
                        interval_combobox.grid(row=0, column=2, padx=5, sticky="w")

                        remove_button = ttk.Button(device_frame, text="Удалить",
                                                 command=lambda ip=ip, frame=device_frame, info=info: self.confirm_remove_device(info, ip, frame), style="Glass.TButton")
                        remove_button.grid(row=0, column=3, padx=5, sticky="w")

                        with self.lock:
                            self.devices[ip] = (device_frame, status_label, info, interval_combobox)
                    else:
                        print(f"Некорректная строка: {line.strip()}")

    def on_closing(self):
        self.save_devices()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkMonitor(root)
    root.mainloop()