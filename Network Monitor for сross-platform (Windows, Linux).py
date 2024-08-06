import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import time
import platform
import os


class NetworkMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Сетевой монитор")
        self.devices = {}

        self.frame = tk.Frame(root)
        self.frame.pack(pady=10)

        self.device_list_frame = tk.Frame(self.frame)
        self.device_list_frame.pack(pady=10)

        self.add_device_frame = tk.Frame(self.frame)
        self.add_device_frame.pack(pady=10)

        self.info_label = tk.Label(self.add_device_frame, text="Информация об устройстве:")
        self.info_label.grid(row=0, column=0, padx=5)

        self.info_entry = tk.Entry(self.add_device_frame)
        self.info_entry.grid(row=0, column=1, padx=5)
        self.info_entry.bind("<KeyRelease>", self.check_entries)

        self.device_label = tk.Label(self.add_device_frame, text="IP:")
        self.device_label.grid(row=0, column=2, padx=5)

        self.ip_entries = []
        for i in range(4):
            ip_entry = tk.Entry(self.add_device_frame, width=3, validate='key', validatecommand=(self.root.register(self.validate_ip_section), '%P'))
            ip_entry.grid(row=0, column=3 + i, padx=2)
            ip_entry.bind("<KeyRelease>", self.check_entries)
            self.ip_entries.append(ip_entry)

        self.add_button = tk.Button(self.add_device_frame, text="Добавить устройство", command=self.add_device, state=tk.DISABLED)
        self.add_button.grid(row=0, column=7, padx=5)

        # Заголовки для списка устройств
        self.header_frame = tk.Frame(self.device_list_frame)
        self.header_frame.grid(row=0, column=0, sticky="w")

        tk.Label(self.header_frame, text="Информация об устройстве", borderwidth=1, relief="solid", width=30).grid(row=0, column=0, padx=5, sticky="w")
        tk.Label(self.header_frame, text="Статус", borderwidth=1, relief="solid", width=15).grid(row=0, column=1, padx=5, sticky="w")
        tk.Label(self.header_frame, text="Действие", borderwidth=1, relief="solid", width=10).grid(row=0, column=2, padx=5, sticky="w")

        self.load_devices()

        self.update_status_thread = threading.Thread(target=self.update_status)
        self.update_status_thread.daemon = True
        self.update_status_thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def validate_ip_section(self, value):
        if value.isdigit() and 0 <= int(value) <= 255:
            return True
        elif value == "":
            return True
        return False

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

            remove_button = tk.Button(device_frame, text="Удалить", command=lambda: self.remove_device(ip, device_frame), borderwidth=1, relief="solid", width=10)
            remove_button.grid(row=0, column=2, padx=5, sticky="w")

            self.devices[ip] = (device_frame, status_label, info)
            for entry in self.ip_entries:
                entry.delete(0, tk.END)
            self.info_entry.delete(0, tk.END)
            self.add_button.config(state=tk.DISABLED)
        else:
            messagebox.showwarning("Предупреждение", "IP или Информация о устройстве не введены.")

    def remove_device(self, ip, frame):
        frame.destroy()
        del self.devices[ip]
        self.rearrange_devices()

    def rearrange_devices(self):
        for i, (ip, (frame, status_label, info)) in enumerate(self.devices.items()):
            frame.grid(row=i + 1, column=0, sticky="w", pady=5)

    def ping_device(self, ip):
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, "1", ip]
        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
            if platform.system().lower() == "windows":
                if "TTL=" in output:
                    return True
            else:
                if "1 packets transmitted, 1 received" in output:
                    return True
            return False
        except subprocess.CalledProcessError:
            return False

    def update_status(self):
        while True:
            for ip, (frame, status_label, info) in self.devices.items():
                if self.ping_device(ip):
                    status_label.config(text="Online", bg="green")
                else:
                    status_label.config(text="Offline", bg="red")
            time.sleep(3)

    def save_devices(self):
        with open("devices.txt", "w") as f:
            for ip, (_, _, info) in self.devices.items():
                f.write(f"{info},{ip}\n")

    def load_devices(self):
        if os.path.exists("devices.txt"):
            with open("devices.txt", "r") as f:
                for line in f:
                    parts = line.strip().split(",", 1)
                    if len(parts) == 2:
                        info, ip = parts
                        row = len(self.devices) + 1
                        device_frame = tk.Frame(self.device_list_frame)
                        device_frame.grid(row=row, column=0, sticky="w", pady=5)

                        device_label = tk.Label(device_frame, text=f"{info} ({ip})", borderwidth=1, relief="solid", width=30)
                        device_label.grid(row=0, column=0, padx=5, sticky="w")

                        status_label = tk.Label(device_frame, text="Проверка...", bg="yellow", borderwidth=1, relief="solid", width=15)
                        status_label.grid(row=0, column=1, padx=5, sticky="w")

                        remove_button = tk.Button(device_frame, text="Удалить",
                                                 command=lambda ip=ip, frame=device_frame: self.remove_device(ip, frame), borderwidth=1, relief="solid", width=10)
                        remove_button.grid(row=0, column=2, padx=5, sticky="w")

                        self.devices[ip] = (device_frame, status_label, info)
                    else:
                        print(f"Некорректная строка: {line.strip()}")

    def on_closing(self):
        self.save_devices()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkMonitor(root)
    root.mainloop()


