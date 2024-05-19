import pygame
import random

# Инициализация Pygame
pygame.init()

# Установка размеров окна
width, height = 800, 600
win = pygame.display.set_mode((width, height))
pygame.display.set_caption("Змейка")

# Цвета
black = (0, 0, 0)
white = (255, 255, 255)
green = (0, 255, 0)

# Параметры змейки
snake_block = 10
snake_speed = 15

# Функция отрисовки змейки
def draw_snake(snake_block, snake_list):
    for x in snake_list:
        pygame.draw.rect(win, green, [x[0], x[1], snake_block, snake_block])

# Основной игровой цикл
def game_loop():
    game_over = False
    game_close = False

    x1, y1 = width / 2, height / 2
    x1_change, y1_change = 0, 0

    snake_list = []
    length_of_snake = 1

    foodx, foody = round(random.randrange(0, width - snake_block) / 10.0) * 10.0, round(random.randrange(0, height - snake_block) / 10.0) * 10.0

    while not game_over:
        while game_close == True:
            # Действия при проигрыше
            win.fill(black)
            font = pygame.font.SysFont(None, 29)
            text = font.render("Вы проиграли! Нажмите R для рестарта или Q для выхода.", True, white)
            win.blit(text, (width / 6, height / 3))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_r:
                        game_loop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    x1_change = -snake_block
                    y1_change = 0
                elif event.key == pygame.K_RIGHT:
                    x1_change = snake_block
                    y1_change = 0
                elif event.key == pygame.K_UP:
                    y1_change = -snake_block
                    x1_change = 0
                elif event.key == pygame.K_DOWN:
                    y1_change = snake_block
                    x1_change = 0

        if x1 >= width or x1 < 0 or y1 >= height or y1 < 0:
            game_close = True
        x1 += x1_change
        y1 += y1_change
        win.fill(black)
        pygame.draw.rect(win, white, [foodx, foody, snake_block, snake_block])
        snake_head = []
        snake_head.append(x1)
        snake_head.append(y1)
        snake_list.append(snake_head)
        if len(snake_list) > length_of_snake:
            del snake_list[0]

        for x in snake_list[:-1]:
            if x == snake_head:
                game_close = True

        draw_snake(snake_block, snake_list)

        pygame.display.update()

        if x1 == foodx and y1 == foody:
            foodx, foody = round(random.randrange(0, width - snake_block) / 10.0) * 10.0, round(random.randrange(0, height - snake_block) / 10.0) * 10.0
            length_of_snake += 1

        pygame.time.Clock().tick(snake_speed)

    pygame.quit()
    quit()

game_loop()