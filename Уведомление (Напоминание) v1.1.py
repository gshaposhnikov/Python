import tkinter as tk

def countdown():
    global remaining_time
    if remaining_time > 0:
        remaining_time -= 1
        time_label.config(text=f"{remaining_time//60:02d}:{remaining_time%60:02d}")
        time_label.after(1000, countdown)
    else:
        time_label.config(text="00:00")
        show_notification()

def show_notification():
    notification_window = tk.Toplevel(root)
    notification_window.title("Уведомление о задаче")
    notification_window.attributes("-topmost", True)  # Делаем окно поверх всех других
    notification_window.grab_set()  # Блокируем взаимодействие с другими окнами
    notification_label = tk.Label(notification_window, text=f"Уведомление о: {event_entry.get()}\nВремя истекло (мин): {time_entry.get()}", font=("Arial", 16))
    notification_label.pack(padx=40, pady=40)

    # Центрируем окно уведомления относительно главного окна
    notification_window.update_idletasks()
    x = (root.winfo_width() - notification_window.winfo_width()) // 5
    y = (root.winfo_height() - notification_window.winfo_height()) // 5
    notification_window.geometry(f"+{x}+{y}")

    # Ждем закрытия окна уведомления
    notification_window.wait_window()

root = tk.Tk()
root.title("Уведомление v1.1")

event_label = tk.Label(root, text="Напомнить о:")
event_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

event_entry = tk.Entry(root)
event_entry.grid(row=0, column=1, padx=10, pady=10)

time_label = tk.Label(root, text="Количество минут:")
time_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

time_entry = tk.Entry(root)
time_entry.grid(row=1, column=1, padx=10, pady=10)

start_button = tk.Button(root, text="Старт", command=lambda: start_countdown(int(time_entry.get())))
start_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

remaining_time = 0

def start_countdown(minutes):
    global remaining_time
    remaining_time = minutes * 60
    countdown()

root.mainloop()