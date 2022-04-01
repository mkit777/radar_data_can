from pygame.sprite import Group
from pygame.sprite import Sprite
import pygame
import time
import sys

class Car(Sprite):
    def __init__(self,  screen):
        # Sprite 和 super 不加无法添加至cars的group中
        super(Car, self).__init__()
        # 初始化车并设置初始化位置
        self.screen = screen

        image = pygame.image.load('res/car1.png')
        self.image = pygame.transform.scale(image, (20, 18))

        # 获取车和屏幕的rect
        self.rect = self.image.get_rect()

class Car2(Sprite):
    def __init__(self,  screen):
        # Sprite 和 super 不加无法添加至cars的group中
        super(Car2, self).__init__()
        # 初始化车并设置初始化位置
        self.screen = screen

        image = pygame.image.load('res/car2.png')
        self.image = pygame.transform.scale(image, (20, 18))

        # 获取车和屏幕的rect
        self.rect = self.image.get_rect()

class TraceDisplay:
    def __init__(self):
        self.screen_witdh = 450
        self.screen_height = 700
        self.bg_color = (169, 169, 169)
        self.line_color = (30, 144, 255)
        self.width_line = 2

        # 初始化pygame，设置屏幕对象
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_witdh, self.screen_height))
        pygame.display.set_caption("Shandong university of Science and Technology")

    def update(self, frame, frame_src):
        cars, labels = self.build_car_and_labels(frame)
        cars_src = self.build_car2(frame_src)
        self.update_screen(cars, labels, cars_src)
        self.check_events()
        time.sleep(0.02)

    def check_events(self):
        # 响应按键和鼠标事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()

    def update_screen(self, cars, labels, cars_src):
        # 每次循环重新绘制屏幕
        self.screen.fill(self.bg_color)
        # 画线
        self.draw_lanes()
        # 可视化车
        cars_src.draw(self.screen)
        cars.draw(self.screen)
        
        
        
        # 可视化文字
        # self.display_labels(labels)
        # 让最近绘制的屏幕可见
        pygame.display.flip()

    def draw_lanes(self):
        pygame.draw.line(self.screen, self.line_color, (0, 600), (450, 600), self.width_line)
        pygame.draw.line(self.screen, (0, 0, 255), (260 - 30, 0), (260 - 30, 600), self.width_line)       # 对应于datax = 2.23
        pygame.draw.line(self.screen, self.line_color, (260 - 60, 0), (260 - 60, 600), self.width_line)   # 对应于datax = 4.26
        pygame.draw.line(self.screen, self.line_color, (260 - 90, 0), (260 - 90, 600), self.width_line)   # 对应于datax = 6.92
        pygame.draw.line(self.screen, (0, 0, 255), (260 - 120, 0), (260 - 120, 600), self.width_line)     # 对应与datax = 9.23

    def build_car_and_labels(self, frame):
        labels=[]
        cars = Group()
        for target in frame:
            car = Car(self.screen)
            car.rect.centerx = (24 - target.m_dx) * 10
            car.rect.centery = (300 + target.m_dy) * 2
            cars.add(car)
            labels.append((target.id, car.rect.centerx, car.rect.centery))
        return cars, labels

    def build_car2(self, frame):
        cars = Group()
        for target in frame:
            car = Car2(self.screen)
            car.rect.centerx = (24 - target.m_dx) * 10
            car.rect.centery = (300 + target.m_dy) * 2
            cars.add(car)
        return cars

    def display_labels(self, labels):
        for i in range(len(labels)):
            a = pygame.font.SysFont('PingFang SC Regular', 14)
            # text = a.render(str(labels[i][2]), True,(255,0,0),(0,0,0))
            # ztx, zty, ztw, zth = text.get_rect()
            # self.screen.blit(text, )
            # a.render_to(self.screen, (labels[i][0], labels[i][1]), label_strings, fgcolor=(240, 248, 255), bgcolor=(30, 144, 255), )