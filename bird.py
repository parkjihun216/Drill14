import random

from pico2d import get_canvas_height, get_canvas_width, load_image

import game_framework


# LEC16 19, 23쪽: 10 pixel = 30 cm. 아래 새의 물리값은 구현용 가정이다.
PIXEL_PER_METER = 10.0 / 0.3
FLIGHT_SPEED_KMPH = 30.0
FLIGHT_SPEED_MPS = FLIGHT_SPEED_KMPH * 1000.0 / 3600.0
FLIGHT_SPEED_PPS = FLIGHT_SPEED_MPS * PIXEL_PER_METER
BIRD_WIDTH_M = 0.9  # 투명 여백을 포함한 한 프레임의 가로 길이
BIRD_WIDTH = BIRD_WIDTH_M * PIXEL_PER_METER

SHEET_COLUMNS = 5
SHEET_ROWS = 3
FRAMES_PER_FLIGHT = 14  # 마지막 행의 오른쪽 빈 칸은 제외
TIME_PER_FLIGHT = 0.5  # 날갯짓 한 주기에 걸리는 초
FRAMES_PER_SECOND = FRAMES_PER_FLIGHT / TIME_PER_FLIGHT
BIRD_COUNT = 10


class Bird:
    image = None

    def __init__(self, index=0):
        if Bird.image is None:
            Bird.image = load_image('bird_animation.png')

        self.width = BIRD_WIDTH
        self.height = self.width * (self.image.h / SHEET_ROWS) / (self.image.w / SHEET_COLUMNS)
        # 가로 위치를 나눠 배치해 시작부터 10마리가 겹치지 않게 한다.
        left, right = self.width / 2, get_canvas_width() - self.width / 2
        self.x = left + (right - left) * (index + 0.5) / BIRD_COUNT
        self.y = random.uniform(220, get_canvas_height() - self.height / 2)
        self.direction = random.choice((-1, 1))
        self.frame = random.random() * FRAMES_PER_FLIGHT

    def update(self):
        dt = game_framework.frame_time
        # LEC16 29쪽: 소수 부분을 버리지 않고 누적하고, 그릴 때만 정수화한다.
        self.frame = (self.frame + FRAMES_PER_SECOND * dt) % FRAMES_PER_FLIGHT

        left = self.width / 2
        span = get_canvas_width() - self.width
        # 왕복 경로를 펼쳐 거리 = 속도 * 시간만큼 이동한 뒤 화면 안으로 접는다.
        # 큰 dt로 여러 번 벽을 지나도 초과 이동 거리를 잃지 않는다.
        distance = self.x - left if self.direction == 1 else 2 * span - (self.x - left)
        distance = (distance + FLIGHT_SPEED_PPS * dt) % (2 * span)
        if distance < span:
            self.x = left + distance
            self.direction = 1
        else:
            self.x = left + 2 * span - distance
            self.direction = -1

    def draw(self):
        row, column = divmod(int(self.frame), SHEET_COLUMNS)
        # 918x506은 5열/3행으로 나누어떨어지지 않으므로 경계마다 정수화한다.
        left = column * self.image.w // SHEET_COLUMNS
        right = (column + 1) * self.image.w // SHEET_COLUMNS
        top = row * self.image.h // SHEET_ROWS
        bottom = (row + 1) * self.image.h // SHEET_ROWS
        self.image.clip_composite_draw(
            left, self.image.h - bottom, right - left, bottom - top,
            0, 'h' if self.direction == -1 else '',
            self.x, self.y, self.width, self.height,
        )
