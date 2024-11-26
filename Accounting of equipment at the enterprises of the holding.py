import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment, Border, Side

# Создание базы данных и таблиц
conn = sqlite3.connect('equipment.db')
cursor = conn.cursor()

# Таблица для хранения информации о технике
cursor.execute('''CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY,
                    organization TEXT,
                    department TEXT,
                    building TEXT,
                    floor TEXT,
                    room TEXT,
                    user_name TEXT,
                    account TEXT,
                    phone TEXT,
                    pc_model TEXT,
                    pc_name TEXT,
                    pc_inventory INTEGER,
                    monitor_model TEXT,
                    monitor_inventory INTEGER,
                    printer_model TEXT,
                    printer_inventory INTEGER,
                    other_equipment_1 TEXT,
                    other_equipment_2 TEXT,
                    other_equipment_3 TEXT,
                    other_equipment_4 TEXT,
                    status TEXT)''')

# Таблица для хранения информации о пользователях
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT)''')

# Добавление администратора и учетной записи для аудита, если их нет
cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'nt[ybrf', 'admin')") # nt[ybrf - Пароль учетной записи admin

cursor.execute("SELECT * FROM users WHERE username='audit'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (username, password, role) VALUES ('audit', 'audit', 'audit')")

conn.commit()


class EquipmentApp:
    def __init__(self, root, username, role):
        self.root = root
        self.root.title("Учет техники на предприятиях холдинга v 1.5.9.4")
        self.root.state('zoomed') # Разворачиваем окно на весь экран

        # Отображение имени пользователя вверху
        self.username_label = tk.Label(self.root, text=f"Пользователь: {username}", font=("Arial", 12))
        self.username_label.pack(side=tk.TOP, anchor='w')

        self.role = role
        self.user_list_window = None # Переменная для хранения окна списка пользователей
        self.create_widgets()
        self.populate_treeview()

    def create_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        # Определение колонок
        columns = ('id', 'org', 'dept', 'bldg', 'flr', 'rm', 'user', 'acct', 'ph', 'pc_mod', 'pc_name', 'pc_inv',
                 'mon_mod', 'mon_inv', 'prn_mod', 'prn_inv', 'other_eq_1', 'other_eq_2', 'other_eq_3', 'other_eq_4', 'status')

        self.tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='extended')

        # Установка заголовков колонок
        headings = ['№ п/п', 'Организация', 'Отдел', 'Корпус', 'Этаж', 'Кабинет', 'Пользователь Ф.И.О', 'Учетная Запись (Логин)',
                    'Телефон', 'Модель ПК', 'Имя ПК', 'Инвентарный № ПК', 'Модель монитора', 'Инвентарный № монитора',
                    'Модель принтера', 'Инвентарный № принтера', 'Иное оборудование № 1', 'Иное оборудование № 2',
                    'Иное оборудование № 3', 'Иное оборудование № 4', 'Статус']

        for col, heading in zip(columns, headings):
            self.tree.heading(col, text=heading)

        # Установка ширины колонок и вертикальных границ
        for col in columns:
            self.tree.column(col, width=200, anchor='center')
            self.tree.tag_configure('oddrow', background='white')
            self.tree.tag_configure('evenrow', background='lightgrey')

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Добавление вертикального скроллинга справа
        y_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scrollbar.set)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Кнопки управления
        self.add_button = tk.Button(self.root, text="Добавить", command=self.add_record)
        self.add_button.pack(side=tk.LEFT)
        self.edit_button = tk.Button(self.root, text="Редактировать", command=self.edit_record)
        self.edit_button.pack(side=tk.LEFT)
        self.delete_button = tk.Button(self.root, text="Удалить", command=self.delete_record)
        self.delete_button.pack(side=tk.LEFT)
        self.copy_button = tk.Button(self.root, text="Дублировать", command=self.copy_record)
        self.copy_button.pack(side=tk.LEFT)

        # Кнопки для импорта и экспорта
        self.export_button = tk.Button(self.root, text="Выгрузить в XLS", command=self.export_to_xls)
        self.export_button.pack(side=tk.LEFT)
        self.import_button = tk.Button(self.root, text="Загрузить из XLS", command=self.import_from_xls)
        self.import_button.pack(side=tk.LEFT)

        # Горизонтальный скроллинг между кнопками
        x_scrollbar = ttk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=x_scrollbar.set)
        x_scrollbar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Кнопка для отображения списка пользователей, доступна только администратору
        if self.role == 'admin':
            self.user_list_button = tk.Button(self.root, text="Список пользователей", command=self.show_user_list)
            self.user_list_button.pack(side=tk.BOTTOM)

        # Деактивация кнопок для роли 'audit'
        if self.role == 'audit':
            self.add_button.config(state=tk.DISABLED)
            self.edit_button.config(state=tk.DISABLED)
            self.delete_button.config(state=tk.DISABLED)
            self.copy_button.config(state=tk.DISABLED)
            self.import_button.config(state=tk.DISABLED)

        # Привязка клавиши Enter ко всем кнопкам
        self.bind_buttons_to_enter()

    def bind_buttons_to_enter(self):
        # Привязываем клавишу Enter к каждой кнопке
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Button):
                widget.bind('<Return>', lambda event, btn=widget: btn.invoke())

    def populate_treeview(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        cursor.execute("SELECT * FROM equipment")
        rows = cursor.fetchall()
        for index, row in enumerate(rows):
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.tree.insert('', tk.END, values=row, tags=(tag,))

    def add_record(self):
        self.edit_window(title="Добавление записи")

    def edit_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            self.edit_window(item['values'])

    def delete_record(self):
        selected_items = self.tree.selection()
        if selected_items:
            confirm = messagebox.askyesno("Подтверждение удаления", "Вы уверены, что хотите удалить выбранные записи?")
            if confirm:
                for selected_item in selected_items:
                    item = self.tree.item(selected_item)
                    cursor.execute("DELETE FROM equipment WHERE id=?", (item['values'][0],))
                conn.commit()
                self.populate_treeview()

    def copy_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            values = item['values'][1:] # Исключаем ID
            cursor.execute(
                '''INSERT INTO equipment (organization, department, building, floor, room, user_name, account, phone, pc_model, pc_name, pc_inventory, monitor_model, monitor_inventory, printer_model, printer_inventory, other_equipment_1, other_equipment_2, other_equipment_3, other_equipment_4, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                values)
            conn.commit()
            new_id = cursor.lastrowid # Получаем ID новой записи
            self.populate_treeview()
            # Открываем форму для редактирования новой записи
            cursor.execute("SELECT * FROM equipment WHERE id=?", (new_id,))
            new_record = cursor.fetchone()
            if new_record:
                self.edit_window(new_record)

    def edit_window(self, values=None, title="Редактирование записи"):
        window = tk.Toplevel(self.root)
        window.title(title)

        labels = ['Организация', 'Отдел', 'Корпус', 'Этаж', 'Кабинет', 'Пользователь Ф.И.О', 'Учетная Запись (Логин)',
                 'Телефон', 'Модель ПК', 'Имя ПК', 'Инвентарный № ПК', 'Модель монитора', 'Инвентарный № монитора',
                 'Модель принтера', 'Инвентарный № принтера', 'Иное оборудование № 1', 'Иное оборудование № 2',
                 'Иное оборудование № 3', 'Иное оборудование № 4', 'Статус']
        entries = []

        def validate_phone(char):
            return char.isdigit() or char in "+-(); "

        def validate_inventory(char):
            return char.isdigit()

        for i, label in enumerate(labels):
            tk.Label(window, text=label).grid(row=i, column=0)
            entry = tk.Entry(window)
            entry.grid(row=i, column=1)
            if values:
                entry.insert(0, values[i + 1])
            if label == 'Телефон':
                entry.config(validate='key', validatecommand=(window.register(validate_phone), '%S'))
            elif label in ['Инвентарный № ПК', 'Инвентарный № монитора', 'Инвентарный № принтера']:
                entry.config(validate='key', validatecommand=(window.register(validate_inventory), '%S'))
            entries.append(entry)

        def save():
            data = [entry.get() for entry in entries]
            if values:
                cursor.execute(
                    '''UPDATE equipment SET organization=?, department=?, building=?, floor=?, room=?, user_name=?, account=?, phone=?, pc_model=?, pc_name=?, pc_inventory=?, monitor_model=?, monitor_inventory=?, printer_model=?, printer_inventory=?, other_equipment_1=?, other_equipment_2=?, other_equipment_3=?, other_equipment_4=?, status=? WHERE id=?''',
                    (*data, values[0]))
            else:
                cursor.execute(
                    '''INSERT INTO equipment (organization, department, building, floor, room, user_name, account, phone, pc_model, pc_name, pc_inventory, monitor_model, monitor_inventory, printer_model, printer_inventory, other_equipment_1, other_equipment_2, other_equipment_3, other_equipment_4, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    data)
            conn.commit()
            self.populate_treeview()
            window.destroy()

        save_button = tk.Button(window, text="Сохранить", command=save)
        save_button.grid(row=len(labels), column=0, columnspan=2)

        # Привязка клавиши Enter к кнопке сохранения
        save_button.bind('<Return>', lambda event: save_button.invoke())

    def export_to_xls(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            cursor.execute("SELECT * FROM equipment")
            rows = cursor.fetchall()
            df = pd.DataFrame(rows,
                             columns=['№ п/п', 'Организация', 'Отдел', 'Корпус', 'Этаж', 'Кабинет', 'Пользователь Ф.И.О',
                                     'Учетная Запись (Логин)', 'Телефон', 'Модель ПК', 'Имя ПК', 'Инвентарный № ПК',
                                     'Модель монитора', 'Инвентарный № монитора', 'Модель принтера',
                                     'Инвентарный № принтера', 'Иное оборудование № 1', 'Иное оборудование № 2',
                                     'Иное оборудование № 3', 'Иное оборудование № 4', 'Статус'])

            # Создание Excel файла с помощью openpyxl
            wb = Workbook()
            ws = wb.active
            ws.title = "Equipment Data"

            for r in dataframe_to_rows(df, index=False, header=True):
                ws.append(r)

            # Настройка ширины колонок и выравнивания
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter # Получение буквы колонки
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column].width = adjusted_width
                for cell in col:
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    cell.border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin')) # Табличное обрамление

            wb.save(file_path)
            messagebox.showinfo("Экспорт", f"Данные успешно выгружены в {file_path}")

    def import_from_xls(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            df = pd.read_excel(file_path)
            for _, row in df.iterrows():
                # Заменяем None на пустые строки
                row = row.fillna('')
                # Убедимся, что количество данных соответствует количеству столбцов в базе данных
                if len(row) == 21: # Учитываем, что первая колонка - это ID
                    cursor.execute(
                        '''INSERT INTO equipment (organization, department, building, floor, room, user_name, account, phone, pc_model, pc_name, pc_inventory, monitor_model, monitor_inventory, printer_model, printer_inventory, other_equipment_1, other_equipment_2, other_equipment_3, other_equipment_4, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        tuple(row[1:])) # Пропускаем ID при вставке
            conn.commit()
            self.populate_treeview() # Обновление списка после импорта
            messagebox.showinfo("Импорт", "Данные успешно загружены из файла")

    def show_user_list(self):
        if self.user_list_window is None or not self.user_list_window.winfo_exists():
            self.user_list_window = tk.Toplevel(self.root)
            self.user_list_window.title("Список пользователей")

            columns = ('id', 'username', 'role')
            tree = ttk.Treeview(self.user_list_window, columns=columns, show='headings')

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=100)

            tree.pack(fill=tk.BOTH, expand=True)

            cursor.execute("SELECT id, username, role FROM users")
            rows = cursor.fetchall()
            for row in rows:
                tree.insert('', tk.END, values=row)

            def delete_user():
                selected_item = tree.selection()
                if selected_item:
                    item = tree.item(selected_item)
                    user_id = item['values'][0]
                    confirm = messagebox.askyesno("Подтверждение удаления", "Вы уверены, что хотите удалить выбранного пользователя?")
                    if confirm:
                        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
                        conn.commit()
                        tree.delete(selected_item)

            delete_button = tk.Button(self.user_list_window, text="Удалить", command=delete_user)
            delete_button.pack(side=tk.BOTTOM)

            # Кнопка для добавления пользователя
            add_user_button = tk.Button(self.user_list_window, text="Добавить пользователя", command=self.add_user)
            add_user_button.pack(side=tk.BOTTOM)

    def add_user(self):
        window = tk.Toplevel(self.root)
        window.title("Добавить пользователя")
        window.geometry("300x70") # Увеличение ширины окна

        tk.Label(window, text="Логин").grid(row=0, column=0)
        username_entry = tk.Entry(window)
        username_entry.grid(row=0, column=1)

        tk.Label(window, text="Пароль").grid(row=1, column=0)
        password_entry = tk.Entry(window, show="*")
        password_entry.grid(row=1, column=1)

        def save_user():
            username = username_entry.get()
            password = password_entry.get()
            try:
                cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'user')", (username, password))
                conn.commit()
                messagebox.showinfo("Успех", "Пользователь успешно добавлен")
                window.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Ошибка", "Пользователь с таким логином уже существует")

        save_user_button = tk.Button(window, text="Сохранить", command=save_user)
        save_user_button.grid(row=2, column=0, columnspan=2)

        # Привязка клавиши Enter к кнопке сохранения пользователя
        save_user_button.bind('<Return>', lambda event: save_user_button.invoke())


class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Авторизация")
        self.root.geometry("250x70") # Увеличение ширины окна авторизации

        tk.Label(root, text="Логин").grid(row=0, column=0)
        self.username_entry = tk.Entry(root)
        self.username_entry.grid(row=0, column=1)

        tk.Label(root, text="Пароль").grid(row=1, column=0)
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.grid(row=1, column=1)

        login_button = tk.Button(root, text="Войти", command=self.login)
        login_button.grid(row=2, column=0, columnspan=2)

        # Привязка клавиши Enter к кнопке входа
        self.root.bind('<Return>', lambda event: login_button.invoke())

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        if user:
            self.root.destroy()
            main_app = tk.Tk()
            EquipmentApp(main_app, username, user[3]) # Передаем роль пользователя
            main_app.mainloop()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")


if __name__ == "__main__":
    root = tk.Tk()
    LoginApp(root)
    root.mainloop()