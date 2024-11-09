import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment

# Создание базы данных и таблицы
conn = sqlite3.connect('equipment.db')
cursor = conn.cursor()
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
                    pc_inventory TEXT,
                    monitor_model TEXT,
                    monitor_inventory TEXT,
                    printer_model TEXT,
                    printer_inventory TEXT,
                    other_equipment_1 TEXT,
                    other_equipment_2 TEXT,
                    other_equipment_3 TEXT,
                    other_equipment_4 TEXT,
                    status TEXT)''')
conn.commit()


class EquipmentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет техники на предприятиях холдинга v 1.2.0.0")

        self.create_widgets()
        self.populate_treeview()

    def create_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        # Определение колонок
        columns = ('id', 'org', 'dept', 'bldg', 'flr', 'rm', 'user', 'acct', 'ph', 'pc_mod', 'pc_name', 'pc_inv',
                 'mon_mod', 'mon_inv', 'prn_mod', 'prn_inv', 'other_eq_1', 'other_eq_2', 'other_eq_3', 'other_eq_4', 'status')

        self.tree = ttk.Treeview(frame, columns=columns, show='headings')

        # Установка заголовков колонок
        headings = ['№ п/п', 'Организация', 'Отдел', 'Корпус', 'Этаж', 'Кабинет', 'Пользователь Ф.И.О', 'Учетная Запись (Логин)',
                    'Телефон', 'Модель ПК', 'Имя ПК', 'Инвентарный № ПК', 'Модель монитора', 'Инвентарный № монитора',
                    'Модель принтера', 'Инвентарный № принтера', 'Иное оборудование № 1', 'Иное оборудование № 2',
                    'Иное оборудование № 3', 'Иное оборудование № 4', 'Статус']

        for col, heading in zip(columns, headings):
            self.tree.heading(col, text=heading)

        # Установка ширины колонок
        for col in columns:
            self.tree.column(col, width=200)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Добавление вертикального скроллинга
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

        # Горизонтальный скроллинг между кнопками
        x_scrollbar = ttk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=x_scrollbar.set)
        x_scrollbar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.import_button = tk.Button(self.root, text="Загрузить из XLS", command=self.import_from_xls)
        self.import_button.pack(side=tk.RIGHT)
        self.export_button = tk.Button(self.root, text="Выгрузить в XLS", command=self.export_to_xls)
        self.export_button.pack(side=tk.RIGHT)

    def populate_treeview(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        cursor.execute("SELECT * FROM equipment")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert('', tk.END, values=row)

    def add_record(self):
        self.edit_window()

    def edit_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            self.edit_window(item['values'])

    def delete_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            cursor.execute("DELETE FROM equipment WHERE id=?", (item['values'][0],))
            conn.commit()
            self.populate_treeview()

    def edit_window(self, values=None):
        window = tk.Toplevel(self.root)
        window.title("Редактирование записи")

        labels = ['Организация', 'Отдел', 'Корпус', 'Этаж', 'Кабинет', 'Пользователь Ф.И.О', 'Учетная Запись (Логин)',
                 'Телефон', 'Модель ПК', 'Имя ПК', 'Инвентарный № ПК', 'Модель монитора', 'Инвентарный № монитора',
                 'Модель принтера', 'Инвентарный № принтера', 'Иное оборудование № 1', 'Иное оборудование № 2',
                 'Иное оборудование № 3', 'Иное оборудование № 4', 'Статус']
        entries = []

        for i, label in enumerate(labels):
            tk.Label(window, text=label).grid(row=i, column=0)
            entry = tk.Entry(window)
            entry.grid(row=i, column=1)
            if values:
                entry.insert(0, values[i + 1])
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

        tk.Button(window, text="Сохранить", command=save).grid(row=len(labels), column=0, columnspan=2)

    def export_to_xls(self):
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

        wb.save('equipment.xlsx')
        messagebox.showinfo("Экспорт", "Данные успешно выгружены в equipment.xlsx")

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


if __name__ == "__main__":
    root = tk.Tk()
    app = EquipmentApp(root)
    root.mainloop()