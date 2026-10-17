import math
import random
import sys

import pygame

pygame.init()

# ---------------- НАСТРОЙКИ ----------------

WIDTH, HEIGHT = 960, 600
WORLD_W, WORLD_H = 2200, 1600
FPS = 60
TILE = 64

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Metro 2033: 2D Prototype")
clock = pygame.time.Clock()

# Цвета
BG = (24, 25, 27)
FLOOR = (49, 48, 45)
WALL = (75, 73, 67)
WHITE = (220, 216, 195)
BLUE = (80, 125, 155)

# ---------------- ГЕНЕРАЦИЯ МИРА ----------------

random.seed(2033)

world = pygame.Surface((WORLD_W, WORLD_H))
world.fill(BG)

# Плитки пола с небольшими различиями оттенков
for x in range(0, WORLD_W, TILE):
	for y in range(0, WORLD_H, TILE):
		shade = random.randint(-7, 7)
		color = tuple(max(0, min(255, c + shade)) for c in FLOOR)

		pygame.draw.rect(
			world, color,
			(x, y, TILE - 2, TILE - 2)
		)

		# Мелкие царапины и пятна
		for _ in range(3):
			px = x + random.randint(5, TILE - 6)
			py = y + random.randint(5, TILE - 6)
			length = random.randint(4, 17)

			pygame.draw.line(
				world, (36, 36, 34),
				(px, py), (px + length, py + 2), 1
			)

# ---------------- СТЕНЫ ----------------

walls = [
	# Внешние границы станции
	pygame.Rect(0, 0, WORLD_W, 48),
	pygame.Rect(0, WORLD_H - 48, WORLD_W, 48),
	pygame.Rect(0, 0, 48, WORLD_H),
	pygame.Rect(WORLD_W - 48, 0, 48, WORLD_H),

	# Внутренние перегородки
	pygame.Rect(250, 180, 550, 48),
	pygame.Rect(250, 180, 48, 350),
	pygame.Rect(800, 180, 48, 220),

	pygame.Rect(1050, 100, 48, 470),
	pygame.Rect(1050, 520, 360, 48),

	pygame.Rect(1450, 220, 500, 48),
	pygame.Rect(1450, 220, 48, 380),

	pygame.Rect(300, 850, 48, 400),
	pygame.Rect(300, 850, 520, 48),
	pygame.Rect(820, 850, 48, 300),

	pygame.Rect(1200, 950, 600, 48),
	pygame.Rect(1750, 950, 48, 350),
]

for wall in walls:
	pygame.draw.rect(world, WALL, wall)

	# Верхняя кромка стены
	pygame.draw.line(
		world, (105, 99, 88),
		wall.topleft,
		(wall.right, wall.top), 3
	)

	# Тёмная нижняя кромка
	pygame.draw.line(
		world, (25, 25, 25),
		(wall.left, wall.bottom - 2),
		wall.bottomright, 4
	)

# ---------------- ДЕКОРАЦИИ ----------------

# Металлические ящики
crates = [
	pygame.Rect(420, 350, 54, 48),
	pygame.Rect(480, 350, 54, 48),
	pygame.Rect(1250, 680, 64, 64),
	pygame.Rect(1550, 1100, 60, 60),
]

for crate in crates:
	pygame.draw.rect(world, (55, 51, 44), crate)
	pygame.draw.rect(world, (100, 88, 68), crate, 3)
	pygame.draw.line(
		world, (115, 100, 75),
		crate.topleft, crate.bottomright, 2
	)

# ---------------- ЛАМПЫ ----------------

lamps = [
	(400, 120),
	(900, 120),
	(1250, 380),
	(1700, 400),
	(600, 700),
	(1100, 760),
	(1550, 850),
	(1900, 1200),
]

# ---------------- ИГРОК ----------------

player = pygame.Rect(100, 100, 26, 32)
speed = 210  # пикселей в секунду

# Направление, в котором смотрит Артём
facing = pygame.Vector2(0, 1)

# ---------------- ОСВЕЩЕНИЕ ----------------

# Тёмный слой поверх всего мира
darkness = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
darkness.fill((0, 0, 0, 165))

# Свет рисуем отдельно и добавляем поверх темноты
light_layer = pygame.Surface((WIDTH, HEIGHT))


def draw_light(surface, x, y, radius, color):
	for r in range(radius, 0, -5):
		strength = int(2 + 15 * (1 - r / radius))
		pygame.draw.circle(
			surface,
			(
				min(255, color[0] * strength // 10),
				min(255, color[1] * strength // 10),
				min(255, color[2] * strength // 10),
			),
			(int(x), int(y)),
			r
		)


# ---------------- ИГРОВОЙ ЦИКЛ ----------------

font = pygame.font.Font(None, 26)
running = True

while running:
	dt = min(clock.tick(FPS) / 1000, 0.05)

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False

	keys = pygame.key.get_pressed()

	if keys[pygame.K_ESCAPE]:
		running = False

	# Движение WASD и стрелками
	movement = pygame.Vector2(0, 0)

	if keys[pygame.K_w] or keys[pygame.K_UP]:
		movement.y -= 1
	if keys[pygame.K_s] or keys[pygame.K_DOWN]:
		movement.y += 1
	if keys[pygame.K_a] or keys[pygame.K_LEFT]:
		movement.x -= 1
	if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
		movement.x += 1

	if movement.length_squared() > 0:
		movement = movement.normalize()
		facing = movement

	# Столкновения по отдельным осям
	player.x += round(movement.x * speed * dt)

	for wall in walls:
		if player.colliderect(wall):
			if movement.x > 0:
				player.right = wall.left
			elif movement.x < 0:
				player.left = wall.right

	player.y += round(movement.y * speed * dt)

	for wall in walls:
		if player.colliderect(wall):
			if movement.y > 0:
				player.bottom = wall.top
			elif movement.y < 0:
				player.top = wall.bottom

	# Камера следует за игроком
	camera_x = player.centerx - WIDTH // 2
	camera_y = player.centery - HEIGHT // 2

	camera_x = max(0, min(camera_x, WORLD_W - WIDTH))
	camera_y = max(0, min(camera_y, WORLD_H - HEIGHT))

	# Рисуем видимую часть мира
	screen.blit(
		world, (0, 0),
		pygame.Rect(camera_x, camera_y, WIDTH, HEIGHT)
	)

	# Лампы на экране
	for lx, ly in lamps:
		sx, sy = lx - camera_x, ly - camera_y

		if -30 < sx < WIDTH + 30 and -30 < sy < HEIGHT + 30:
			pygame.draw.circle(screen, (220, 175, 90), (sx, sy), 7)
			pygame.draw.circle(screen, (255, 220, 150), (sx, sy), 3)

	# Игрок: временный силуэт
	px = player.centerx - camera_x
	py = player.centery - camera_y

	pygame.draw.ellipse(
		screen, (18, 18, 18),
		(px - 15, py + 8, 30, 12)
	)

	pygame.draw.rect(
		screen, (90, 80, 65),
		(px - 10, py - 10, 20, 24)
	)

	pygame.draw.circle(
		screen, BLUE, (px, py - 12), 10
	)

	# Направление взгляда
	pygame.draw.line(
		screen, WHITE,
		(px, py - 12),
		(
			px + int(facing.x * 15),
			py - 12 + int(facing.y * 15)
		),
		3
	)

	# Затемнение
	screen.blit(darkness, (0, 0))

	# Добавляем свет от ламп
	light_layer.fill((0, 0, 0))

	for lx, ly in lamps:
		sx, sy = lx - camera_x, ly - camera_y

		if -180 < sx < WIDTH + 180 and -180 < sy < HEIGHT + 180:
			draw_light(light_layer, sx, sy, 105, (180, 135, 75))

	# Свет вокруг Артёма
	draw_light(
		light_layer,
		px, py, 90,
		(105, 125, 145)
	)

	screen.blit(
		light_layer, (0, 0),
		special_flags=pygame.BLEND_RGB_ADD
	)

	# Интерфейс
	label = font.render(
		"VDNKh | WASD: Move | ESC: Exit",
		True, WHITE
	)
	screen.blit(label, (16, 16))

	pygame.display.flip()

pygame.quit()
sys.exit()
