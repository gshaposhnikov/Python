"""Логическая игра "Быки и коровы 2023 год"""

import random

NUM_DIGITS = 4  # Количество загаданных цифр от 1 до 10.
MAX_GUESSES = 12  # Количество попыток для разгадки числа от 1 до 100.


def main():
    print('''Разработка: Шапошников Геннадий Александрович.
Правки интерфейса: Петров Лев Николаевич.
Логическая игра: "Быки и коровы (4-значное число) v1.3.4.4 ".

Правила игры:

Программа загадывает 4-значное число (все цифры разные), вам нужно его угадать.
У вас есть 12 попыток.
Введите 4-значное число.  Программа сообщит результат попытки:
 Бык    -   Цифра угадана и находится на своем месте.
 Корова -   Цифра угадана, но находится не на своем месте.
 Нет    -   Ни одна цифра не угадана.
Например, если программа загадала число 2481, а вы ввели 4783,
то результат будет: Бык Корова.

Выход из игры: Ctrl+C 	
'''.format(NUM_DIGITS))
    while True:  # Основной цикл игры.
        # Переменная, в которой хранится секретное число, которое должен угадать игрок:
        secretNum = getSecretNum()
        print('')
        print('Поехали!')

        print('Число загадано.')

        print('У вас есть {} попыток.'.format(MAX_GUESSES))

        numGuesses = 1
        while numGuesses <= MAX_GUESSES:
            guess = ''
            # Продолжаем итерации до получения правильной догадки:
            while len(guess) != NUM_DIGITS or not guess.isdecimal():
                print('')
                print('Попытка №{}: '.format(numGuesses))
                guess = input('> ')

            clues = getClues(guess, secretNum)
            print(clues)
            numGuesses += 1

            if guess == secretNum:
                break  # Правильно, выходим из цикла.
            if numGuesses > MAX_GUESSES:
                print('Вы проиграли! Использованы все попытки!')
                print('Вы отгадывали число {}.'.format(secretNum))

                print('Спасибо за игру!')
                print('')

        # Спрашиваем игрока, хочет ли он сыграть еще раз.
        print('Хотите сыграть еще раз (Y/N)?')
        if not input('> ').lower().startswith('y'):  # y
            break
    # print('Спасибо за игру!')


def getSecretNum():
    """Возвращает строку из NUM_DIGITS уникальных случайных цифр."""
    numbers = list('0123456789')  # Создает список цифр от 0 до 9.
    random.shuffle(numbers)  # Перетасовываем их случайным образом.

    # Берем первые NUM_DIGITS цифр списка для нашего секретного числа:
    secretNum = ''
    for i in range(NUM_DIGITS):
        secretNum += str(numbers[i])
    return secretNum


def getClues(guess, secretNum):
    """Возвращает строку с подсказками Корова, Бык и Нет
73. для полученной на входе пары из догадки и секретного числа."""
    if guess == secretNum:
        return 'Это верное число!'

    clues = []

    for i in range(len(guess)):
        if guess[i] == secretNum[i]:
            # Правильная цифра на правильном месте.
            clues.append('Бык')  # Бык: верная цифра на своём месте
        elif guess[i] in secretNum:
            # Правильная цифра на неправильном месте.
            clues.append('Корова')  # Корова: правильная цифра не на своём месте.
    if len(clues) == 0:
        return 'Нет'  # Нет верных цифр: Правильных цифр нет вообще.
    else:
        # Сортируем подсказки в алфавитном порядке, чтобы их исходный порядок ничего не выдавал.
        clues.sort()
        # Склеиваем список подсказок в одно строковое значение.
        return ' '.join(clues)


# Производим запуск программы:
if __name__ == '__main__':
    main()

