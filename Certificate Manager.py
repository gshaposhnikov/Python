import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime, timedelta
import threading
import time
from plyer import notification

DB_NAME = 'certificates.db'

# --- Работа с базой данных ---
class Database:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_table()

    def create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_name TEXT NOT NULL,
            clinic TEXT NOT NULL,
            certificate_name TEXT NOT NULL,
            issue_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL
        )
        '''
        self.conn.execute(query)
        self.conn.commit()

    def add_certificate(self, doctor_name, clinic, certificate_name, issue_date, expiry_date):
        query = '''
        INSERT INTO certificates (doctor_name, clinic, certificate_name, issue_date, expiry_date)
        VALUES (?, ?, ?, ?, ?)
        '''
        self.conn.execute(query, (doctor_name, clinic, certificate_name, issue_date, expiry_date))
        self.conn.commit()

    def update_certificate(self, cert_id, doctor_name, clinic, certificate_name, issue_date, expiry_date):
        query = '''
        UPDATE certificates SET doctor_name=?, clinic=?, certificate_name=?, issue_date=?, expiry_date=?
        WHERE id=?
        '''
        self.conn.execute(query, (doctor_name, clinic, certificate_name, issue_date, expiry_date, cert_id))
        self.conn.commit()

    def delete_certificate(self, cert_id):
        query = 'DELETE FROM certificates WHERE id=?'
        self.conn.execute(query, (cert_id,))
        self.conn.commit()

    def get_all_certificates(self):
        query = 'SELECT * FROM certificates ORDER BY expiry_date ASC'
        cursor = self.conn.execute(query)
        return cursor.fetchall()

    def get_expiring_certificates(self, days_threshold):
        # Возвращает сертификаты, срок действия которых истекает в течение days_threshold дней
        now = datetime.now()
        limit_date = now + timedelta(days=days_threshold)
        query = '''
        SELECT * FROM certificates WHERE date(expiry_date) <= date(?) ORDER BY expiry_date ASC
        '''
        cursor = self.conn.execute(query, (limit_date.strftime('%Y-%m-%d'),))
        return cursor.fetchall()

# --- Основное приложение ---
class CertificateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет сертификатов врачей")
        self.db = Database()

        self.notification_interval = 60  # секунд, по умолчанию 1 минута
        self.days_before_expiry = 30  # по умолчанию уведомлять за 30 дней

        self.create_widgets()
        self.load_data()

        # Запускаем фоновый поток уведомлений
        self.running = True
        self.notification_thread = threading.Thread(target=self.notification_worker, daemon=True)
        self.notification_thread.start()

    def create_widgets(self):
        # Верхняя панель с кнопками
        frame_buttons = ttk.Frame(self.root)
        frame_buttons.pack(fill=tk.X, padx=5, pady=5)

        btn_add = ttk.Button(frame_buttons, text="Добавить", command=self.add_certificate)
        btn_add.pack(side=tk.LEFT, padx=5)

        btn_edit = ttk.Button(frame_buttons, text="Редактировать", command=self.edit_certificate)
        btn_edit.pack(side=tk.LEFT, padx=5)

        btn_delete = ttk.Button(frame_buttons, text="Удалить", command=self.delete_certificate)
        btn_delete.pack(side=tk.LEFT, padx=5)

        btn_settings = ttk.Button(frame_buttons, text="Настройки уведомлений", command=self.settings)
        btn_settings.pack(side=tk.RIGHT, padx=5)

        # Таблица
        columns = ("id", "doctor_name", "clinic", "certificate_name", "issue_date", "expiry_date")
        self.tree = ttk.Treeview(self.root, columns=columns, show='headings')
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=30, anchor=tk.CENTER)
        self.tree.heading("doctor_name", text="Врач")
        self.tree.column("doctor_name", width=150)
        self.tree.heading("clinic", text="Клиника")
        self.tree.column("clinic", width=150)
        self.tree.heading("certificate_name", text="Сертификат")
        self.tree.column("certificate_name", width=150)
        self.tree.heading("issue_date", text="Дата выдачи")
        self.tree.column("issue_date", width=100, anchor=tk.CENTER)
        self.tree.heading("expiry_date", text="Дата окончания")
        self.tree.column("expiry_date", width=100, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for cert in self.db.get_all_certificates():
            self.tree.insert("", tk.END, values=cert)

    def add_certificate(self):
        dialog = CertificateDialog(self.root, "Добавить сертификат")
        if dialog.result:
            doctor_name, clinic, certificate_name, issue_date, expiry_date = dialog.result
            try:
                # Проверка дат
                datetime.strptime(issue_date, '%Y-%m-%d')
                datetime.strptime(expiry_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД")
                return
            self.db.add_certificate(doctor_name, clinic, certificate_name, issue_date, expiry_date)
            self.load_data()

    def edit_certificate(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выберите запись", "Пожалуйста, выберите сертификат для редактирования")
            return
        item = self.tree.item(selected[0])
        cert_id, doctor_name, clinic, certificate_name, issue_date, expiry_date = item['values']
        dialog = CertificateDialog(self.root, "Редактировать сертификат", 
                                   doctor_name, clinic, certificate_name, issue_date, expiry_date)
        if dialog.result:
            doctor_name, clinic, certificate_name, issue_date, expiry_date = dialog.result
            try:
                datetime.strptime(issue_date, '%Y-%m-%d')
                datetime.strptime(expiry_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД")
                return
            self.db.update_certificate(cert_id, doctor_name, clinic, certificate_name, issue_date, expiry_date)
            self.load_data()

    def delete_certificate(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выберите запись", "Пожалуйста, выберите сертификат для удаления")
            return
        if messagebox.askyesno("Подтвердите удаление", "Вы уверены, что хотите удалить выбранный сертификат?"):
            item = self.tree.item(selected[0])
            cert_id = item['values'][0]
            self.db.delete_certificate(cert_id)
            self.load_data()

    def settings(self):
        dialog = SettingsDialog(self.root, self.notification_interval, self.days_before_expiry)
        if dialog.result:
            interval_sec, days_before = dialog.result
            self.notification_interval = interval_sec
            self.days_before_expiry = days_before

    def notification_worker(self):
        while self.running:
            expiring_certs = self.db.get_expiring_certificates(self.days_before_expiry)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            for cert in expiring_certs:
                cert_id, doctor_name, clinic, certificate_name, issue_date, expiry_date = cert
                expiry_dt = datetime.strptime(expiry_date, '%Y-%m-%d')
                days_left = (expiry_dt - datetime.now()).days
                if days_left < 0:
                    status = "Срок истек!"
                else:
                    status = f"Осталось {days_left} дней"
                title = f"Сертификат врача {doctor_name} скоро истекает"
                message = (f"Клиника: {clinic}\n"
                           f"Сертификат: {certificate_name}\n"
                           f"Дата окончания: {expiry_date}\n"
                           f"{status}")
                # Отправляем уведомление с красным текстом (если платформа поддерживает)
                try:
                    notification.notify(
                        title=title,
                        message=message,
                        app_name="Учет сертификатов",
                        timeout=10,
                        # plyer не поддерживает цвет текста, но мы можем указать иконку или т.п.
                    )
                except Exception as e:
                    print(f"Ошибка уведомления: {e}")
            time.sleep(self.notification_interval)

    def on_close(self):
        self.running = False
        self.root.destroy()

# --- Диалог добавления/редактирования сертификата ---
class CertificateDialog(simpledialog.Dialog):
    def __init__(self, parent, title, doctor_name='', clinic='', certificate_name='', issue_date='', expiry_date=''):
        self.doctor_name = doctor_name
        self.clinic = clinic
        self.certificate_name = certificate_name
        self.issue_date = issue_date
        self.expiry_date = expiry_date
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Врач:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_doctor = ttk.Entry(master)
        self.entry_doctor.grid(row=0, column=1, pady=2)
        self.entry_doctor.insert(0, self.doctor_name)

        ttk.Label(master, text="Клиника:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entry_clinic = ttk.Entry(master)
        self.entry_clinic.grid(row=1, column=1, pady=2)
        self.entry_clinic.insert(0, self.clinic)

        ttk.Label(master, text="Сертификат:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.entry_certificate = ttk.Entry(master)
        self.entry_certificate.grid(row=2, column=1, pady=2)
        self.entry_certificate.insert(0, self.certificate_name)

        ttk.Label(master, text="Дата выдачи (ГГГГ-ММ-ДД):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.entry_issue = ttk.Entry(master)
        self.entry_issue.grid(row=3, column=1, pady=2)
        self.entry_issue.insert(0, self.issue_date)

        ttk.Label(master, text="Дата окончания (ГГГГ-ММ-ДД):").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.entry_expiry = ttk.Entry(master)
        self.entry_expiry.grid(row=4, column=1, pady=2)
        self.entry_expiry.insert(0, self.expiry_date)

        return self.entry_doctor  # фокус

    def apply(self):
        doctor_name = self.entry_doctor.get().strip()
        clinic = self.entry_clinic.get().strip()
        certificate_name = self.entry_certificate.get().strip()
        issue_date = self.entry_issue.get().strip()
        expiry_date = self.entry_expiry.get().strip()
        if not all([doctor_name, clinic, certificate_name, issue_date, expiry_date]):
            messagebox.showerror("Ошибка", "Все поля должны быть заполнены")
            self.result = None
            return
        self.result = (doctor_name, clinic, certificate_name, issue_date, expiry_date)

# --- Диалог настроек уведомлений ---
class SettingsDialog(simpledialog.Dialog):
    def __init__(self, parent, current_interval, current_days_before):
        self.current_interval = current_interval
        self.current_days_before = current_days_before
        super().__init__(parent, "Настройки уведомлений")

    def body(self, master):
        ttk.Label(master, text="Интервал проверки (секунды):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entry_interval = ttk.Entry(master)
        self.entry_interval.grid(row=0, column=1, pady=5)
        self.entry_interval.insert(0, str(self.current_interval))

        ttk.Label(master, text="Уведомлять за (дней до истечения):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_days = ttk.Entry(master)
        self.entry_days.grid(row=1, column=1, pady=5)
        self.entry_days.insert(0, str(self.current_days_before))

        return self.entry_interval

    def apply(self):
        try:
            interval = int(self.entry_interval.get())
            days_before = int(self.entry_days.get())
            if interval <= 0 or days_before <= 0:
                raise ValueError
            self.result = (interval, days_before)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите положительные целые числа")
            self.result = None

# --- Запуск приложения ---
def main():
    root = tk.Tk()
    app = CertificateApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
