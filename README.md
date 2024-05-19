# Python

В этом репозитории будут представлены, простые программы на языке Python.
1. --- Домашняя бухгалтерия v0.5 (Home accounting v0.5) ---
Это программа на языке Python с использованием библиотек Tkinter и SQLite3 для создания простой системы учета домашних расходов. С возможностью формирования отчета и выводом финансового результата за весь период. 
- Вот краткое описание основных функций:
- Создание базы данных и таблицы:
Создается база данных "finance.db" и таблица "transactions" с полями id, date, description, amount и type.
Проверяется наличие столбца "type" в таблице, и если его нет, то он добавляется.
- Функции для работы с данными:

- add_transaction(): Добавляет новую транзакцию в базу данных, используя введенные пользователем данные (дата, описание, тип, сумма). Обновляет дерево отображения транзакций и очищает поля ввода.

- delete_transaction(): Удаляет выбранную транзакцию из базы данных. Обновляет дерево отображения транзакций.

- update_tree(): Обновляет дерево отображения транзакций, загружая все записи из базы данных.

- clear_entries(): Очищает поля ввода даты, описания, типа и суммы.

- generate_report(): Генерирует финансовый отчет, подсчитывая общий приход, расход. Также подсчитывает приход и расход по месяцам и выводит отчет в отдельном окне.

- Создание графического интерфейса GUI:

- Создается главное окно приложения с заголовком "Домашняя бухгалтерия v0.5".

- Верхняя панель содержит поля выбора даты, описания, типа (приход или расход) и суммы, а также кнопку "Добавить" для добавления новой операции.

- Ниже располагается табличная часть с колонками ID, дата, описание, сумма и тип.

- Под табличной частью находятся кнопки "Удалить" для удаления выбранной операции (строки) и "Сформировать отчет" для генерации финансового отчета.

- Обновление табличной части и отображение финансовых операции:

- При запуске программы вызывается функция update_tree(), которая загружает все записи из базы данных и отображает их в табличной части.

- Комментарий: Это приложение позволяет пользователям вести учет своих финансовых операций, добавлять новые строки прихода и расхода, при необходимости удалять существующие и получать финансовый отчет с подведением итогов по приходу, расходу и выводу результатов (прибыль или убыток) за весь период.

 2. --- Уведомление (Напоминание) v1.1 --- Это приложение на tkinter, которое позволяет пользователям установить напоминание о чём-то важном с обратным отсчетом (указывается в минутах), по истечении времени создаётся дополнительная форма с уведомлением о чем-то важном. Поверх всех открытых окон.
- Вот краткое описание основных функций:
 
- Функция countdown(): Уменьшает переменную remaining_time на 1 секунду до тех пор, пока она не достигнет 0.

- Обновляет метку time_label с оставшимся временем в формате минут и секунд.
 
- При достижении отсчета 0 вызывает функцию show_notification().
 
- Функция show_notification(): Создает новое окно верхнего уровня (Toplevel) для отображения уведомления о событии.
Устанавливает заголовок окна, делает его поверх всех открытых окон и блокирует взаимодействие с другими окнами до его закрытия.
 
- Отображает название напоминания чём-то важном и прошедшее время в минутах, внутри окна уведомления.

- Располагает окно уведомления левее, относительно главного окна.

- Ожидает закрытия окна уведомления перед продолжением.

- Создание графического интерфейса GUI:

- Создается главное окно приложения с помощью tk.Tk() и названием "Уведомление v1.1".
 
- Предоставляются поля для ввода названия напоминания о: (том что нужно сделать)  и количества минут: (до момента когда это нужно сделать).
 
- Кнопка запуска (Старт) инициирует обратный отсчет при нажатии, вызывая start_countdown() с введенными минутами.
 
- Функция start_countdown() устанавливает remaining_time на основе введенных минут и запускает обратный отсчет.
 
- Комментарий: Это приложение-напоминание с обратным отсчетом с использованием tkinter в Python, позволяет пользователям устанавливать напоминания о событиях и получать уведомления, когда отсчет достигает нуля. Очень удобно когда в назначенное время нужно срочно что-то сделать, но при этом выполнять параллельно другую задачу. Важно: После нажатия кнопки старт не нажимайте её повторно секунды идут в двое быстрее. Если время введено не верно, закройте программу введи нужные значения и нажмите Старт.
- Возможно будут доработки.

3. --- Игра Быки и коровы (загаданы 4 цифры) --- Это интересная реализация логической игры "Быки и коровы" на Python. Эта игра написана в 2023г, при содействии моего коллеги по работе.

- Вот краткое описание основных компонентов и функций:

- Константы:

- NUM_DIGITS: Количество цифр в загаданном числе (по умолчанию 4).

- MAX_GUESSES: Максимальное количество попыток (по умолчанию 12).

 - Функции:

- main(): Основная функция, запускающая игру.

- getSecretNum(): Генерирует случайное секретное число.

- getClues(guess, secretNum): Определяет количество "быков" и "коров" для данной догадки.

- О коде:

- Функция main() выводит правила игры и запускает основной цикл игры.

- В цикле игры:

- Генерируется случайное секретное число с помощью getSecretNum().

- Игрок делает попытки угадать число, пока не закончатся попытки или пока не будет угадано число.

- Для каждой попытки:

- Игрок вводит число.

- Функция getClues() определяет количество "быков" и "коров" для введенного числа.

- Выводится результат попытки.

- Если число угадано, игрок выигрывает.

- Если закончились попытки, игрок проигрывает.

- После окончания игры игроку предлагается сыграть еще раз.

- Функция getSecretNum() генерирует случайное число из уникальных цифр. Она создает список цифр от 0 до 9, перемешивает его случайным образом и берет первые NUM_DIGITS цифр для формирования секретного числа.

- Функция getClues() определяет количество "быков" и "коров" для данной догадки. Она сравнивает каждую цифру догадки с соответствующей цифрой секретного числа. Если цифры совпадают и находятся на своих местах, это "бык". Если цифра есть в секретном числе, но находится не на своем месте, это "корова". Если нет ни одной правильной цифры, возвращается "Нет".

- Особенности реализации:

- Игра использует цикл while True для основного цикла игры, чтобы игрок мог играть снова после окончания игры.

- Для генерации случайного секретного числа используется модуль random и функция random.shuffle().

- Подсказки "бык" и "корова" выводятся в алфавитном порядке, чтобы не выдавать информацию о порядке правильных цифр.

- Игра использует input() для получения ввода от игрока и print() для вывода информации.

- Комментарий: Это реализация классической игры "Быки и коровы" на Python. Она демонстрирует использование циклов, функций, строк, списков и модуля random для создания интерактивной игры. В игре исправлены ошибки, это рабочий проект.