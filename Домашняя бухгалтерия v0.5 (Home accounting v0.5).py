import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime

# Создание базы данных и таблицы
conn = sqlite3.connect('finance.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transactions
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, description TEXT, amount REAL, type TEXT)''')

# Проверка наличия столбца type перед добавлением
c.execute("PRAGMA table_info(transactions)")
columns = [column[1] for column in c.fetchall()]
if 'type' not in columns:
    c.execute('''ALTER TABLE transactions ADD COLUMN type TEXT''')

conn.commit()

# Функции для работы с данными
def add_transaction():
    date = date_cal.get_date()
    description = description_entry.get()
    transaction_type = type_combo.get()
    amount = float(amount_entry.get())
    c.execute("INSERT INTO transactions (date, description, amount, type) VALUES (?, ?, ?, ?)",
              (date, description, amount, transaction_type))
    conn.commit()
    update_tree()
    clear_entries()

def delete_transaction():
    selected = tree.selection()
    if selected:
        c.execute("DELETE FROM transactions WHERE id = ?", (tree.set(selected[0], '#1'),))
        conn.commit()
        update_tree()

def update_tree():
    tree.delete(*tree.get_children())
    c.execute("SELECT * FROM transactions")
    for row in c:
        tree.insert("", "end", values=row)

def clear_entries():
    date_cal.set_date(None)
    description_entry.delete(0, tk.END)
    type_combo.set("")
    amount_entry.delete(0, tk.END)

def generate_report():
    total_income = 0
    total_expense = 0
    income_by_month = {}
    expense_by_month = {}

    c.execute("SELECT date, amount, type FROM transactions")
    for row in c:
        date_str = row[0]
        amount = row[1]
        transaction_type = row[2]

        # Разделение по месяцам
        month = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m")

        if transaction_type == "Приход":
            total_income += amount
            income_by_month[month] = income_by_month.get(month, 0) + amount
        else:
            total_expense += amount
            expense_by_month[month] = expense_by_month.get(month, 0) + amount

    profit_loss = total_income - total_expense

    report_text = f"Общий приход: {total_income}\nОбщий расход: {total_expense}\nИтоговый результат: {profit_loss}\n\n"

    # Добавление разделения по месяцам и подсчет итогов прибыли и убытков по каждому месяцу
    report_text += "Приход по месяцам:\n"
    for month, amount in income_by_month.items():
        report_text += f"{month}: {amount}\n"
    report_text += f"Итог приход: {total_income}\n\n"

    report_text += "Расход по месяцам:\n"
    for month, amount in expense_by_month.items():
        report_text += f"{month}: {amount}\n"
    report_text += f"Итог Расход: {total_expense}\n"

    report_window = tk.Toplevel(root)
    report_window.title("Финансовый отчет")
    report_label = tk.Label(report_window, text=report_text)
    report_label.pack(padx=70, pady=70)

# Создание GUI
root = tk.Tk()
root.title("Домашняя бухгалтерия v0.5")

# Верхняя панель
top_frame = tk.Frame(root)
top_frame.pack(pady=10)

date_label = tk.Label(top_frame, text="Дата:")
date_label.grid(row=0, column=0, padx=5)
date_cal = DateEntry(top_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
date_cal.grid(row=0, column=1, padx=5)

description_label = tk.Label(top_frame, text="Описание:")
description_label.grid(row=0, column=2, padx=5)
description_entry = tk.Entry(top_frame)
description_entry.grid(row=0, column=3, padx=5)

type_label = tk.Label(top_frame, text="Тип:")
type_label.grid(row=0, column=4, padx=5)
type_combo = ttk.Combobox(top_frame, values=["Приход", "Расход"])
type_combo.grid(row=0, column=5, padx=5)

amount_label = tk.Label(top_frame, text="Сумма:")
amount_label.grid(row=0, column=6, padx=5)
amount_entry = tk.Entry(top_frame)
amount_entry.grid(row=0, column=7, padx=5)

add_button = tk.Button(top_frame, text="Добавить", command=add_transaction)
add_button.grid(row=0, column=8, padx=5)

# Таблица транзакций
tree = ttk.Treeview(root, columns=("id", "date", "description", "amount", "type"))
tree.heading("#0", text="")
tree.heading("#1", text="ID")
tree.heading("#2", text="Дата")
tree.heading("#3", text="Описание")
tree.heading("#4", text="Сумма")
tree.heading("#5", text="Тип")
tree.pack(pady=10)

# Кнопка удаления
delete_button = tk.Button(root, text="Удалить", command=delete_transaction)
delete_button.pack(pady=5)

# Кнопка формирования отчета
report_button = tk.Button(root, text="Сформировать отчет", command=generate_report)
report_button.pack(pady=5)

update_tree()
root.mainloop()