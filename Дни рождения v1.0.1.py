import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime, date
import os

# Функция для добавления человека в листбокс
def add_person():
    name = name_entry.get()
    birthday = birthday_entry.get()
    if name and birthday:
        people_listbox.insert(tk.END, f"{name} ({birthday})")
        name_entry.delete(0, tk.END)
        birthday_entry.delete(0, tk.END)
        with open("people.txt", "a") as file:
            file.write(f"{name} ({birthday})\n")

# Функция для удаления выбранного человека из листбокс
def delete_person():
    selected = people_listbox.curselection()
    if selected:
        people_listbox.delete(selected)
        with open("people.txt", "r") as file:
            lines = file.readlines()
        with open("people.txt", "w") as file:
            for i, line in enumerate(lines):
                if i != selected[0]:
                    file.write(line)

# Функция для проверки дней рождения
def check_birthdays():
    today = date.today()
    birthday_listbox.delete(0, tk.END)
    for i in range(people_listbox.size()):
        person = people_listbox.get(i)
        name, birthday = person.split(" (")
        birthday = birthday[:-1]
        birthday_day, birthday_month = map(int, birthday.split("."))
        birthday = date(today.year, birthday_month, birthday_day)
        if today.month == birthday.month and today.day == birthday.day:
            birthday_listbox.insert(tk.END, person)
            tk.messagebox.showinfo("День рождения", f"Сегодня день рождения у {name}!")

# Функция для проверки дней рождения за 1 месяц
def check_next_month_birthdays():
    today = date.today()
    next_month = today.month + 1 if today.month < 12 else 1
    next_year = today.year if today.month < 12 else today.year + 1

    soon_birthday_listbox.delete(0, tk.END)
    for i in range(people_listbox.size()):
        person = people_listbox.get(i)
        name, birthday = person.split(" (")
        birthday = birthday[:-1]
        birthday_day, birthday_month = map(int, birthday.split("."))
        birthday = date(today.year, birthday_month, birthday_day)
        days_until_birthday = (birthday - today).days
        if 1 <= days_until_birthday <= 30:
            soon_birthday_listbox.insert(tk.END, person)
            tk.messagebox.showinfo("Скоро день рождения", f"До дня рождения у {name} осталось {days_until_birthday} дней.")

# Функция для импорта данных
def import_data():
    import_file = filedialog.askopenfilename()
    if import_file:
        with open(import_file, "r") as file:
            for line in file:
                people_listbox.insert(tk.END, line.strip())

# Создание главного окна
root = tk.Tk()
root.title("Дни рождения v1.0.1")

# Задание размера формы
root.geometry("300x800")

# Создание виджетов
name_label = tk.Label(root, text="Фамилия Имя Отчество:")
name_label.grid(row=0, column=0, columnspan=2)

name_entry = tk.Entry(root)
name_entry.grid(row=1, column=0, columnspan=2)

birthday_label = tk.Label(root, text="День рождения (ДД.ММ):")
birthday_label.grid(row=2, column=0, columnspan=2)

birthday_entry = tk.Entry(root)
birthday_entry.grid(row=3, column=0, columnspan=2)

# Размещение кнопок "Добавить" и "Удалить" на одной строке
add_button = tk.Button(root, text="Добавить", command=add_person)
add_button.grid(row=4, column=0)

delete_button = tk.Button(root, text="Удалить", command=delete_person)
delete_button.grid(row=4, column=1)

import_button = tk.Button(root, text="Импорт", command=import_data)
import_button.grid(row=5, column=0, columnspan=2)

check_button = tk.Button(root, text="Проверить дни рождения", command=check_birthdays)
check_button.grid(row=6, column=0, columnspan=2)

next_month_button = tk.Button(root, text="Проверить дни рождения за 1 месяц", command=check_next_month_birthdays)
next_month_button.grid(row=7, column=0, columnspan=2)

people_label = tk.Label(root, text="Список людей:")
people_label.grid(row=8, column=0, columnspan=2)

people_listbox = tk.Listbox(root, width=40)
people_listbox.grid(row=9, column=0, columnspan=2)

birthday_label = tk.Label(root, text="Дни рождения сегодня:")
birthday_label.grid(row=10, column=0, columnspan=2)

birthday_listbox = tk.Listbox(root, width=40)
birthday_listbox.grid(row=11, column=0, columnspan=2)

soon_birthday_label = tk.Label(root, text="Скоро день рождения:")
soon_birthday_label.grid(row=12, column=0, columnspan=2)

soon_birthday_listbox = tk.Listbox(root, width=40)
soon_birthday_listbox.grid(row=13, column=0, columnspan=2)

# Загрузка людей из файла
if os.path.exists("people.txt"):
    with open("people.txt", "r") as file:
        for line in file:
            people_listbox.insert(tk.END, line.strip())

# Запуск главного цикла
root.mainloop()