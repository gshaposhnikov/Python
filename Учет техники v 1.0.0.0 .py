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
                    other_equipment TEXT,
                    comment TEXT)''')
conn.commit()


class EquipmentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учет техники на предприятиях холдинга")

        self.create_widgets()
        self.populate_treeview()

    def create_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(frame, columns=(
        'id', 'org', 'dept', 'bldg', 'flr', 'rm', 'user', 'acct', 'ph', 'pc_mod', 'pc_name', 'pc_inv', 'mon_mod',
        'mon_inv', 'prn_mod', 'prn_inv', 'other_eq', 'cmt'), show='headings')

        self.tree.heading('id', text='№ п/п')
        self.tree.heading('org', text='Орг.')
        self.tree.heading('dept', text='Отдел')
        self.tree.heading('bldg', text='Корп.')
        self.tree.heading('flr', text='Этаж')
        self.tree.heading('rm', text='Каб.')
        self.tree.heading('user', text='Польз.')
        self.tree.heading('acct', text='Учет. Зап.')
        self.tree.heading('ph', text='Тел.')
        self.tree.heading('pc_mod', text='Мод. ПК')
        self.tree.heading('pc_name', text='Имя ПК')
        self.tree.heading('pc_inv', text='Инв. № ПК')
        self.tree.heading('mon_mod', text='Мод. мон.')
        self.tree.heading('mon_inv', text='Инв. № мон.')
        self.tree.heading('prn_mod', text='Мод. прин.')
        self.tree.heading('prn_inv', text='Инв. № прин.')
        self.tree.heading('other_eq', text='Иное оборуд.')
        self.tree.heading('cmt', text='Коммент.')

        # Установка ширины колонок
        self.tree.column('id', width=50)
        self.tree.column('org', width=100)
        self.tree.column('dept', width=100)
        self.tree.column('bldg', width=50)
        self.tree.column('flr', width=50)
        self.tree.column('rm', width=50)
        self.tree.column('user', width=100)
        self.tree.column('acct', width=100)
        self.tree.column('ph', width=100)
        self.tree.column('pc_mod', width=100)
        self.tree.column('pc_name', width=100)
        self.tree.column('pc_inv', width=100)
        self.tree.column('mon_mod', width=100)
        self.tree.column('mon_inv', width=100)
        self.tree.column('prn_mod', width=100)
        self.tree.column('prn_inv', width=100)
        self.tree.column('other_eq', width=100)
        self.tree.column('cmt', width=150)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.add_button = tk.Button(self.root, text="Добавить", command=self.add_record)
        self.add_button.pack(side=tk.LEFT)
        self.edit_button = tk.Button(self.root, text="Редактировать", command=self.edit_record)
        self.edit_button.pack(side=tk.LEFT)
        self.delete_button = tk.Button(self.root, text="Удалить", command=self.delete_record)
        self.delete_button.pack(side=tk.LEFT)

        # Перенос кнопок "Выгрузить в XLS" и "Загрузить из XLS" на правую сторону
        self.export_button = tk.Button(self.root, text="Выгрузить в XLS", command=self.export_to_xls)
        self.export_button.pack(side=tk.RIGHT)
        self.import_button = tk.Button(self.root, text="Загрузить из XLS", command=self.import_from_xls)
        self.import_button.pack(side=tk.RIGHT)

        # Добавление всплывающих подсказок
        self.add_tooltips()

    def add_tooltips(self):
        tooltips = {
            'org': 'Организация',
            'dept': 'Отдел',
            'bldg': 'Корпус',
            'flr': 'Этаж',
            'rm': 'Кабинет',
            'user': 'Пользователь Ф.И.О',
            'acct': 'Учетная Запись (Логин)',
            'ph': 'Телефон',
            'pc_mod': 'Модель ПК',
            'pc_name': 'Имя ПК',
            'pc_inv': 'Инвентарный № ПК',
            'mon_mod': 'Модель монитора',
            'mon_inv': 'Инвентарный № монитора',
            'prn_mod': 'Модель принтера',
            'prn_inv': 'Инвентарный № принтера',
            'other_eq': 'Иное оборудование',
            'cmt': 'Комментарий'
        }

        for col, text in tooltips.items():
            self.tree.heading(col, text=self.tree.heading(col)['text'],
                              command=lambda c=col: self.show_tooltip(c, text))

    def show_tooltip(self, col, text):
        x, y, width, height = self.tree.bbox('heading', col)
        x += self.tree.winfo_rootx() + width // 2
        y += self.tree.winfo_rooty() + height
        tooltip = tk.Toplevel(self.tree)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tooltip, text=text, background="yellow", relief='solid', borderwidth=1,
                         font=("Arial", 10, "normal"))
        label.pack()
        self.tree.after(1500, tooltip.destroy)

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
                  'Модель принтера', 'Инвентарный № принтера', 'Иное оборудование', 'Комментарий']
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
                    '''UPDATE equipment SET organization=?, department=?, building=?, floor=?, room=?, user_name=?, account=?, phone=?, pc_model=?, pc_name=?, pc_inventory=?, monitor_model=?, monitor_inventory=?, printer_model=?, printer_inventory=?, other_equipment=?, comment=? WHERE id=?''',
                    (*data, values[0]))
            else:
                cursor.execute(
                    '''INSERT INTO equipment (organization, department, building, floor, room, user_name, account, phone, pc_model, pc_name, pc_inventory, monitor_model, monitor_inventory, printer_model, printer_inventory, other_equipment, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
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
                                   'Инвентарный № принтера', 'Иное оборудование', 'Комментарий'])

        # Создание Excel файла с помощью openpyxl
        wb = Workbook()
        ws = wb.active
        ws.title = "Equipment Data"

        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)

        # Настройка ширины колонок и выравнивания
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter  # Получение буквы колонки
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
                cursor.execute(
                    '''INSERT INTO equipment (organization, department, building, floor, room, user_name, account, phone, pc_model, pc_name, pc_inventory, monitor_model, monitor_inventory, printer_model, printer_inventory, other_equipment, comment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    tuple(row[1:]))
            conn.commit()
            self.populate_treeview()
            messagebox.showinfo("Импорт", "Данные успешно загружены из файла")


if __name__ == "__main__":
    root = tk.Tk()
    app = EquipmentApp(root)
    root.mainloop()