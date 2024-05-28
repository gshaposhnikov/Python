import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime
import babel.numbers
import babel.dates

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

# Регистрация адаптера даты
def adapt_datetime(dt):
    return dt.isoformat()

sqlite3.register_adapter(datetime, adapt_datetime)

# Функции для работы с данными
def add_transaction():
    date = date_cal.get_date()
    description = description_entry.get()
    transaction_type = type_combo.get()
    amount = float(amount_entry.get())
    c.execute("INSERT INTO transactions (date, description, amount, type) VALUES (?, ?, ?, ?)",
              (date.isoformat(), description, amount, transaction_type))
    conn.commit()
    update_tree(filter_year.get(), filter_month.get(), filter_type.get())
    clear_entries()


def delete_transaction():
    selected = tree.selection()
    if selected:
        c.execute("DELETE FROM transactions WHERE id = ?", (tree.set(selected[0], '#1'),))
        conn.commit()
        update_tree(filter_year.get(), filter_month.get(), filter_type.get())


def update_tree(year=None, month=None, transaction_type=None):
    tree.delete(*tree.get_children())
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if year and year != "Все":
        query += " AND date LIKE ?"
        params.append(f'{year}-%')

    if month and month != "Все":
        query += " AND date LIKE ?"
        params.append(
            f'%-{list(babel.dates.get_month_names("wide", locale='ru_RU').keys())[list(babel.dates.get_month_names("wide", locale='ru_RU').values()).index(month)]:02d}-%')

    if transaction_type and transaction_type != "Все":
        query += " AND type = ?"
        params.append(transaction_type)

    c.execute(query, params)
    for i, row in enumerate(c, start=1):
        tree.insert("", "end", values=(row[0], i, row[1], row[2], row[3], row[4]))


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

    report_text = f"Общий приход: {babel.numbers.format_currency(total_income, 'RUB', locale='ru_RU')}\n" \
                  f"Общий расход: {babel.numbers.format_currency(total_expense, 'RUB', locale='ru_RU')}\n" \
                  f"Итоговый результат: {babel.numbers.format_currency(profit_loss, 'RUB', locale='ru_RU')}\n\n"

    report_text += "Приход по месяцам:\n"
    for month, amount in income_by_month.items():
        report_text += f"{babel.dates.format_date(datetime.strptime(month, '%Y-%m'), format='MMMM yyyy', locale='ru_RU')}: " \
                       f"{babel.numbers.format_currency(amount, 'RUB', locale='ru_RU')}\n"
    report_text += f"Итог приход: {babel.numbers.format_currency(total_income, 'RUB', locale='ru_RU')}\n\n"

    report_text += "Расход по месяцам:\n"
    for month, amount in expense_by_month.items():
        report_text += f"{babel.dates.format_date(datetime.strptime(month, '%Y-%m'), format='MMMM yyyy', locale='ru_RU')}: " \
                       f"{babel.numbers.format_currency(amount, 'RUB', locale='ru_RU')}\n"
    report_text += f"Итог Расход: {babel.numbers.format_currency(total_expense, 'RUB', locale='ru_RU')}\n"

    report_window = tk.Toplevel(root)
    report_window.title("Финансовый отчет")
    report_label = tk.Label(report_window, text=report_text)
    report_label.pack(padx=70, pady=70)


# Создание GUI
root = tk.Tk()
root.title("Домашняя бухгалтерия v1.0")

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

# Панель фильтров
filter_frame = tk.Frame(root)
filter_frame.pack(pady=10)

filter_year_label = tk.Label(filter_frame, text="Год:")
filter_year_label.grid(row=0, column=0, padx=5)
filter_year = ttk.Combobox(filter_frame, values=[], state="readonly")
filter_year.grid(row=0, column=1, padx=5)

filter_month_label = tk.Label(filter_frame, text="Месяц:")
filter_month_label.grid(row=0, column=2, padx=5)
month_names = babel.dates.get_month_names("wide", locale='ru_RU')
filter_month = ttk.Combobox(filter_frame, values=["Все"] + list(month_names.values())[0:], state="readonly")
filter_month.grid(row=0, column=3, padx=5)

filter_type_label = tk.Label(filter_frame, text="Тип:")
filter_type_label.grid(row=0, column=4, padx=5)
filter_type = ttk.Combobox(filter_frame, values=["Все", "Приход", "Расход"], state="readonly")
filter_type.grid(row=0, column=5, padx=5)

filter_button = tk.Button(filter_frame, text="Фильтровать",
                          command=lambda: update_tree(filter_year.get(), filter_month.get(), filter_type.get()))
filter_button.grid(row=0, column=6, padx=5)

# Таблица транзакций
tree_frame = tk.Frame(root)
tree_frame.pack(pady=10)

tree = ttk.Treeview(tree_frame, columns=("id", "№", "date", "description", "amount", "type"), show="headings")
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

tree.column("id", width=50)
tree.column("№", width=50)
tree.column("date", width=100)
tree.column("description", width=200)
tree.column("amount", width=100)
tree.column("type", width=100)

tree.heading("id", text="ID")
tree.heading("№", text="№")
tree.heading("date", text="Дата")
tree.heading("description", text="Описание")
tree.heading("amount", text="Сумма")
tree.heading("type", text="Тип")

total_label = tk.Label(tree_frame, text="Итого:")
total_label.pack(side=tk.LEFT, padx=10)

total_amount_label = tk.Label(tree_frame, text="0.00")
total_amount_label.pack(side=tk.LEFT)

scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
scrollbar.pack(side=tk.LEFT, fill=tk.Y)
tree.configure(yscrollcommand=scrollbar.set)

# Кнопки для удаления и генерации отчета
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

delete_button = tk.Button(button_frame, text="Удалить", command=delete_transaction)
delete_button.pack(side=tk.LEFT, padx=5)

report_button = tk.Button(button_frame, text="Отчет", command=generate_report)
report_button.pack(side=tk.LEFT, padx=5)

# Заполнение списка годов
c.execute("SELECT DISTINCT substr(date, 1, 4) AS year FROM transactions ORDER BY year DESC")
years = [row[0] for row in c]
filter_year['values'] = ["Все"] + years

# Обновление дерева виджетов при запуске
update_tree()

def calculate_total_amount():
    total_amount = 0
    for item in tree.get_children():
        amount = float(tree.set(item, "amount"))
        total_amount += amount
    return total_amount

def update_tree(year=None, month=None, transaction_type=None):
    tree.delete(*tree.get_children())
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if year and year != "Все":
        query += " AND date LIKE ?"
        params.append(f'{year}-%')

    if month and month != "Все":
        query += " AND date LIKE ?"
        params.append(
            f'%-{list(babel.dates.get_month_names("wide", locale='ru_RU').keys())[list(babel.dates.get_month_names("wide", locale='ru_RU').values()).index(month)]:02d}-%')

    if transaction_type and transaction_type != "Все":
        query += " AND type = ?"
        params.append(transaction_type)

    c.execute(query, params)
    for i, row in enumerate(c, start=1):
        tree.insert("", "end", values=(row[0], i, row[1], row[2], row[3], row[4]))

    total_amount = calculate_total_amount()
    total_amount_label.config(text=f"{total_amount:.2f}")

root.mainloop()