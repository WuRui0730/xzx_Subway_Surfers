# -*- coding: utf-8 -*-
"""
Created on Wed May 28 20:21:09 2025

@author: 棋子
"""

import pgzrun
import random
from pgzero.actor import Actor
import time
import json
from pathlib import Path
import pygame
import pygame.freetype

#常量
WIDTH = 449
HEIGHT = 799
new_coin = 0
game_over = False 
background_speed = 3
obj_speed = 4

GRAVITY = 0.33       # 重力加速度
JUMP_SPEED = -3     # 角色跳跃初速度

create_interval = 1.0  # 初始生成间隔（秒）
next_barrier_time = time.time() + create_interval  # 障碍物下次生成时间
next_coin_time = time.time() + create_interval  # 金币下次生成时间
next_magnet_time = time.time() + create_interval  # 磁铁下次生成时间
next_shield_time = time.time() + create_interval  # 护盾下次生成时间


# 背景循环滚动
background1 = Actor('background')  # 导入背景图片：像素为800*800
background1.x = WIDTH/2
background1.y = HEIGHT/2
background2 = Actor('background')
background2.x = WIDTH/2
background2.y = -HEIGHT/2

# ------------------------------------------------------------------- 角色 -------- #
# 角色状态
player = {
    'x': WIDTH / 2 ,          # X轴位置
    'y': HEIGHT - 200,            # Y轴位置
    'velocity_y': 0,       # 垂直速度
    'lane': 'center',       # 当前所在跑道（left/center/right）
    'prev_lane':'center',   # 之前所在跑道（left/center/right）
    'is_jumping': False,          # 是否处于跳跃状态
    'is_squating': False,        # 是否处于下蹲状态
    'is_hit': False             # 是否与障碍物碰撞
}

# 加载角色动画）
player_anim = [
    Actor('dave_run_12'),
    Actor('dave_run_22'),
    Actor('dave_run_3'),
    Actor('dave_run_22')
]
animation_frame = 0  # 动画帧计数器
animation_speed = 0.12  # 动画切换速度

hit_check = Actor('dave_run_12')    # 检测角色列车碰撞
hit_check.x = -WIDTH
hit_check.y = -HEIGHT

def end_hit_check():
    hit_check.x = -WIDTH
    hit_check.y = -HEIGHT

dave_squat = Actor('dave_squat')
dave_squat.x = -WIDTH
dave_squat.y = -HEIGHT

# ------------------------------------------------------------------- 障碍物 -------- #
#障碍物
#列车
trains = [
    'train_1',
    'train_2'
]
train_1_objs = []   # 存储生成的有头列车对象
train_2_objs = []   # 存储生成的无头列车对象

# 栅栏障碍物
#fences = ['fence']
fence_up_objs = []   # 上栅栏
fence_down_objs = []   # 下栅栏

all_barrier = []   # 存放所有障碍物

create_positions = {
    'left': (100, -350),
    'center': (WIDTH/2, -350),
    'right': (345, -350)
}

# 创建各种障碍物
def create_barrier():
    global next_barrier_time

    train_1 = Actor('train_1')
    train_2 = Actor('train_2')
    fence_up = Actor('fence_up')
    fence_down = Actor('fence_down')

    # 随机生成新障碍物的位置和类型（循环直到找到合法位置）
    while True:
        # 随机选择障碍物类型（列车或栅栏）
        obstacle_type = random.choice(['train', 'fence'])
        if obstacle_type == 'train':
            # 随机选择列车类型（train_1或train_2）
            obj = random.choice([train_1, train_2])
            position = random.choice(list(create_positions.keys()))
            x, y = create_positions[position]
            obj.x, obj.y = x, y
            new_objs = [obj]
        else:
            # 栅栏同时生成上下两部分
            obj_up = fence_up
            obj_down = fence_down
            position = random.choice(list(create_positions.keys()))
            x, y = create_positions[position]
            obj_up.x, obj_up.y = x, y
            obj_down.x, obj_down.y = x, y + obj_up.height/2 + obj_down.height/2
            new_objs = [obj_up, obj_down]
            
        
        # 检测新障碍物与现有障碍物是否重叠
        has_collision = False
        for new_obj in new_objs:
            for old_obj in all_barrier:
                if new_obj.colliderect(old_obj):
                    has_collision = True
                    break
            if has_collision:
                break
        
        if not has_collision:
            # 无碰撞时，添加到对应障碍物列表
            if obstacle_type == 'train':
                if obj == train_1:
                    train_1_objs.append(obj)
                    all_barrier.append(obj)
                else:
                    train_2_objs.append(obj)
                    all_barrier.append(obj)
            else:
                fence_up_objs.append(obj_up)
                all_barrier.append(obj_up)
                fence_down_objs.append(obj_down)
                all_barrier.append(obj_down)
            break  # 成功生成，退出循环
    
    # 更新下次生成时间（随机间隔：1~3秒）
    next_barrier_time = time.time() + random.uniform(0.5, 3)


# ------------------------------------------------------------------- 金币 -------- #
coin_objs = []

def create_coin():
    global next_coin_time

    coin = Actor('coin')
    
    position = random.choice(list(create_positions.keys()))
    x, y = create_positions[position]
    coin.x, coin.y = x, y

    # 检查 coin 是否不与 fence_up_objs 和 fence_down_objs 中的任何对象发生碰撞
    if not any(coin.colliderect(obj) for obj in fence_up_objs) and \
       not any(coin.colliderect(obj) for obj in fence_down_objs):
        # 如果没有碰撞，则将 coin 添加到 coin_objs 列表中
        coin_objs.append(coin)

    # 更新下次生成时间（随机间隔：1~3秒）
    next_coin_time = time.time() + random.uniform(0.4, 0.8)

# ------------------------------------------------------------------- 磁铁 -------- #
magnet_objs = []
magnet ={
        'effect':False
}

def create_magnet():
    global next_magnet_time

    magnet = Actor('magnet')
    
    position = random.choice(list(create_positions.keys()))
    x, y = create_positions[position]
    magnet.x, magnet.y = x, y

    # 检查 magnet 是否不与 coin_objs 中的任何对象发生碰撞
    if not any(magnet.colliderect(obj) for obj in coin_objs)and \
       not any(magnet.colliderect(train) for train in train_1_objs):
           magnet_objs.append(magnet)

    # 更新下次生成时间（随机间隔：1~3秒）
    next_magnet_time = time.time() + random.uniform(10, 12)
    


def end_magnet():
    magnet['effect'] = False
    
# ------------------------------------------------------------------- 护盾 -------- #
shield_objs = []
shield ={
        'effect':False
}
shield_effect = Actor('shield_effect')


def create_shield():
    global next_shield_time

    shield = Actor('shield')
    
    position = random.choice(list(create_positions.keys()))
    x, y = create_positions[position]
    shield.x, shield.y = x, y

    if not any(shield.colliderect(obj) for obj in coin_objs) and \
       not any(shield.colliderect(obj) for obj in magnet_objs) and \
       not any(shield.colliderect(train) for train in train_1_objs):
           shield_objs.append(shield)

    # 更新下次生成时间（随机间隔：1~3秒）
    next_shield_time = time.time() + random.uniform(8, 10)

def end_shield():
    shield['effect'] = False

# ------------------------------------------------------------------- 字体文本 -------- #
pygame.init()  # 初始化pygame
# 加载字体文件，设置不同字体大小
font_score_1 = pygame.freetype.Font('s.ttf', 40) 
font_best_1 = pygame.freetype.Font('s.ttf', 20) 
font_score_2 = pygame.freetype.Font('s.ttf', 40) 
font_best_2 = pygame.freetype.Font('s.ttf', 40) 
font_all = pygame.freetype.Font('s.ttf', 40) 

reset = Actor('reset')
reset.x = WIDTH / 2
reset.y = 550

# ------------------------------------------------------------------- 音乐音效 -------- #
# 加载音乐：此方法需将音频文件与本py文件放在同目录，不要放在sounds/music目录中
pygame.mixer.init()  # 初始化pygame的混音器模块

bgm = pygame.mixer.Sound("bgm.mp3")
bgm.play(-1)

# 加载各音效
got_coin = pygame.mixer.Sound("got_coin.wav")
jump_sound = pygame.mixer.Sound("jump.mp3")   #子弹击中敌机音效
move_sound = pygame.mixer.Sound("move.mp3")
squat_sound = pygame.mixer.Sound("squat2.mp3")
game_over_sound = pygame.mixer.Sound("game_over_sound.mp3")


    
    
# ------------------------------------------------------------------- draw() -------- #
def draw():
    screen.clear()
    
    background1.draw()
    background2.draw()
    
    """
    train_1.draw()
    train_2.draw()
    fence.draw()
    """

    # 绘制列车
    for obj in train_1_objs:
        obj.draw()
    for obj in train_2_objs:
        obj.draw()
        
    # 绘制下栅栏
    for obj in fence_down_objs:
        obj.draw()
    
    if player['is_squating'] == True:
        dave_squat.draw()
    
    # 绘制上栅栏
    for obj in fence_up_objs:
        obj.draw()
        
    # 绘制金币
    for obj in coin_objs:
        obj.draw()
        
    # 绘制磁铁
    for obj in magnet_objs:
        obj.draw()
    
    for obj in shield_objs:
        obj.draw()
        
    hit_check.draw()

    if player['is_squating'] == False:
        # 绘制角色（根据状态选择动画帧）
        current_anim = player_anim[int(animation_frame)]
        current_anim.x = player['x']
        current_anim.y = player['y']
        current_anim.draw()
        
    if shield['effect'] == True:
        shield_effect.draw()
    
    # 加载当前分数
    all_coin, best_coin = load_score()
    if game_over == False:
        # 本局得分
        text_surface, rect = font_score_1.render(f"本局得分 {new_coin}", fgcolor='blue')
        rect.topleft = (WIDTH / 2 - 100, 20)
        screen.blit(text_surface, rect)
        # 历史最高分
        text_surface, rect = font_best_1.render(f"历史最高分:{best_coin}", fgcolor='yellow')
        rect.topleft = (WIDTH / 2 - 70, 60)
        screen.blit(text_surface, rect)
    else:
        text_surface, rect = font_score_2.render(f"本局金币 {new_coin}", fgcolor='blue')
        rect.topleft = (WIDTH / 2 - 100, 250)
        screen.blit(text_surface, rect)
        # 历史最高分
        text_surface, rect = font_best_2.render(f"历史最高金币:{best_coin}", fgcolor='yellow')
        rect.topleft = (WIDTH / 2 - 160, 320)
        screen.blit(text_surface, rect)
        text_surface, rect = font_all.render(f"当前所有金币:{all_coin}", fgcolor='black')
        rect.topleft = (WIDTH / 2 - 160, 390)
        screen.blit(text_surface, rect)
        
        reset.draw()

        
        
# ------------------------------------------------------------------- update() -------- #
def update():
    global animation_frame, game_over,new_coin,background_speed,obj_speed
    
    if game_over:
        return  # 游戏结束后停止更新
    
    background1.y += background_speed   # 背景滚动
    background2.y += background_speed
    if background1.y > HEIGHT/2 + HEIGHT:
        background1.y = -HEIGHT/2
    if background2.y > HEIGHT/2 + HEIGHT:
        background2.y = -HEIGHT/2  
    
    # 动画帧更新
    animation_frame += animation_speed
    if animation_frame >= len(player_anim):
        animation_frame = 0
        
    current_time = time.time()   # 获取当前时间
    if current_time > next_barrier_time:  # 检查是否到达生成时间
        create_barrier()
    if current_time > next_coin_time:  # 检查是否到达生成时间
        create_coin()
    if current_time > next_magnet_time:  # 检查是否到达生成时间
        create_magnet()
    if current_time > next_shield_time:  # 检查是否到达生成时间
        create_shield()

# ------------------------------------------------------------------- 障碍物update() -------- #
    # 更新所有 列车 障碍物的位置
    for obj in train_1_objs[:]:
        obj.y = obj.y + obj_speed
        if obj.y > HEIGHT + obj.height / 2:
            train_1_objs.remove(obj) 
            all_barrier.remove(obj)
            
    for obj in train_2_objs[:]:
        obj.y += background_speed
        if obj.y > HEIGHT + obj.height / 2:
            train_2_objs.remove(obj) 
            all_barrier.remove(obj)
    
    # 更新所有 栅栏 障碍物的位置
    for obj in fence_up_objs[:]:
        obj.y += background_speed   
        if obj.y > HEIGHT + obj.height / 2:
            fence_up_objs.remove(obj)
            all_barrier.remove(obj)
            
    for obj in fence_down_objs[:]:
        obj.y += background_speed   
        if obj.y > HEIGHT + obj.height / 2:
            fence_down_objs.remove(obj)
            all_barrier.remove(obj)

    # 障碍物间的避免碰撞
    for train1_obj in train_1_objs[:]:
        train1_x = train1_obj.x
        train1_y = train1_obj.y
        
        # train_1_objs与 train_2_objs 的 x 坐标相同且、y 坐标差小于1300、y 坐标小于train_2_objs
        for train2_obj in train_2_objs:
            if train1_x == train2_obj.x and train1_y >= train2_obj.y - 1500 and train1_y < train2_obj.y:
                train_1_objs.remove(train1_obj)
                all_barrier.remove(train1_obj)
                break
        # train_1_objs与 fence_up_objs 的 x 坐标相同且、y 坐标差小于1000、y 坐标小于train_2_objs
        if train1_obj in train_1_objs:
            for fence_up_obj in fence_up_objs:
                if train1_x == fence_up_obj.x and train1_y >= fence_up_obj.y - 1200 and train1_y < fence_up_obj.y:
                    train_1_objs.remove(train1_obj)
                    all_barrier.remove(train1_obj)
                    break

# ------------------------------------------------------------------- 角色update() -------- #
    # 角色物理更新
    if player['is_jumping'] == False:
        player['velocity_y'] += GRAVITY  # 重力影响
    player['y'] += player['velocity_y']

    # 边界检测（地面碰撞）
    if player['y'] >= HEIGHT - 100:
        player['y'] = HEIGHT - 100
        player['velocity_y'] = 0
        
    if player['is_squating'] == True:
        dave_squat.x = player['x']   # 下蹲时的位置和当前角色位置保持一致
        dave_squat.y = HEIGHT - 100
        
# ------------------------------------------------------------------- 金币update() -------- #
    for obj in coin_objs[:]:
        if obj.y > HEIGHT + (obj.height / 2):
            coin_objs.remove(obj)
        elif any(obj.colliderect(train) for train in train_1_objs):
            obj.y += obj_speed
        else:
            obj.y += background_speed
            
        # 角色获取金币
    for obj in coin_objs[:]:
        if obj.colliderect(player_anim[0]):
            coin_objs.remove(obj)
            new_coin += 1
            
            got_coin.play()
            
            if new_coin % 5 == 0:
                obj_speed += 1 
                background_speed += 1   
            
# ------------------------------------------------------------------- 磁铁update() -------- #
    for obj in magnet_objs[:]:
        if obj.y > HEIGHT + (obj.height / 2):
            magnet_objs.remove(obj)
        elif any(obj.colliderect(train) for train in train_1_objs):
            obj.y += obj_speed
        else:
            obj.y += background_speed
            
        # 角色获取磁铁
    for obj in magnet_objs[:]:
        if obj.colliderect(player_anim[0]):
            magnet['effect'] = True
            magnet_objs.remove(obj)
            got_coin.play()
    if magnet['effect'] == True:
        speed = 5
        for obj in coin_objs[:]:
            dx = player['x'] - obj.x
            dy = player['y'] - obj.y
            distance = (dx**2 + dy**2)**0.5
            if obj.y >= player['y'] - 500:
                obj.x += (dx / distance) * speed
                obj.y += (dy / distance) * speed
                clock.schedule(end_magnet, 6)


# ------------------------------------------------------------------- 护盾update() -------- #
    for obj in shield_objs[:]:
        if obj.y > HEIGHT + (obj.height / 2):
            shield_objs.remove(obj)
        elif any(obj.colliderect(train) for train in train_1_objs):
            obj.y += obj_speed
        else:
            obj.y += background_speed

        # 角色获取护盾
    for obj in shield_objs[:]:
        if obj.colliderect(player_anim[0]):
            shield['effect'] = True
            shield_objs.remove(obj)
            got_coin.play()
            clock.schedule(end_shield, 8)
            
    if shield['effect'] == True: 
        shield_effect.x = player['x']
        shield_effect.y = player['y']
        
# ------------------------------------------------------------------- 角色碰撞检测 -------- #

    if shield['effect'] == False:

        # 列车碰撞检测，！！！game_over 的状态会紊乱
        '''
        for obj1 in train_1_objs:    
            #for obj3 in train_1_objs:
                #if hit_check.colliderect(obj1) and hit_check.colliderect(obj3):
                    #game_over = False
                    #continue

            for obj2 in train_2_objs:
                #for obj4 in train_2_objs:
                    #if hit_check.colliderect(obj2) and hit_check.colliderect(obj4):
                        #game_over = False
                        #continue
                        
                if hit_check.colliderect(obj2) and not hit_check.colliderect(obj1):
                    if get_train_lane(obj2) == player['lane']:
                        game_over = True
                        break
            if game_over == True:
                break
            
        if not game_over:
            for obj1 in train_1_objs:
                for obj2 in train_2_objs:
                    if hit_check.colliderect(obj1) and not hit_check.colliderect(obj2):
                        if get_train_lane(obj1) == player['lane']:
                            game_over = True
                            break
                if game_over == True:
                    break
        '''
        
        for obj1 in train_1_objs:
            if hit_check.colliderect(obj1):
                if get_train_lane(obj1) == player['lane']:
                    game_over = True
                    break
        
        # 如果列车1已经检测到碰撞，跳过列车2的检测
        if not game_over:
            # 检测列车2的物体与玩家的碰撞
            for obj2 in train_2_objs:
                if hit_check.colliderect(obj2):
                    if get_train_lane(obj2) == player['lane']:
                        game_over = True
                        break
        
         # 列车头单区域检测
        for obj1 in train_1_objs:
            if get_train_lane(obj1) == player['lane'] and obj1.y >= player['y'] - 330 and \
            obj1.y <= player['y'] - 310:
                game_over = True
                break       

        
        # 与栅栏
        for obj in fence_down_objs[:]:
            if not player['is_squating'] and not player['is_jumping'] and (player_anim[0]).colliderect(obj):
                game_over = True
                break


def get_train_lane(train_obj):
    """获取列车所在轨道（根据x坐标判断）"""
    if train_obj.x == 100:
        return 'left'
    elif train_obj.x == WIDTH/2:
        return 'center'
    elif train_obj.x == 345:
        return 'right'
    else:
        return None




            

# ------------------------------------------------------------------- 键盘、鼠标 -------- #
def on_key_down(key):
    """键盘事件处理"""

    if key == keys.UP:
        jump()
        jump_sound.play()
    elif key == keys.DOWN:
        squat()
        squat_sound.play()
    elif key == keys.LEFT:
        move_lane('left')
        move_sound.play()
    elif key == keys.RIGHT:
        move_lane('right')
        move_sound.play()

def on_mouse_down():
    if game_over:   # 如果游戏结束，点击重置游戏
        reset_game()
        
if game_over == True:
    game_over_sound.play()
        
# ------------------------------------------------------------------- reset_game() -------- #
# 游戏重置
def reset_game():  
    global new_coin, game_over, background_speed, obj_speed
    new_coin = 0
    game_over = False 
    background_speed = 3
    obj_speed = 4
    hit_check.x = -WIDTH/2
    hit_check.y = -HEIGHT
    player['x'] = WIDTH/2
    player['y'] = HEIGHT - 200
    
    # 清除屏幕上的金币、障碍物、道具
    for obj in coin_objs[:]:
        obj.x = -500
        obj.y = -500
    for obj in all_barrier[:]:
        obj.x = -500
        obj.y = -500
    for obj in magnet_objs[:]:
        obj.x = -500
        obj.y = -500
    for obj in shield_objs[:]:
        obj.x = -500
        obj.y = -500
        
        
        

    
    #GRAVITY = 0.15       # 重力加速度
    #JUMP_SPEED = -6     # 角色跳跃初速度










# ------------------------------------------------------------------- 跳跃 -------- #
def jump():
    """跳跃控制"""
    if not player['is_jumping'] and not player['is_squating']:
        player['velocity_y'] = JUMP_SPEED
        player['is_jumping'] = True
        clock.schedule(end_jump, 0.8)

def end_jump():
    """结束跳跃状态"""
    player['is_jumping'] = False
    
# ------------------------------------------------------------------- 下蹲 -------- #

def squat():
    """下蹲控制"""
    if not player['is_squating']:
        player['is_squating'] = True
        #pygame.mixer.Sound.play(sound_effects['crouch'])
        clock.schedule(end_squat, 1.5)  # 保持1秒下蹲
  
def end_squat():
    """结束下蹲状态"""
    player['is_squating'] = False
  
# ------------------------------------------------------------------- 左右换道 -------- #
def move_lane(target_lane):
    """更换轨道"""
    # 根据目标轨道设置X坐标
    # 往左的三种情况
    if target_lane == 'left' and player['lane'] == 'left':
        player['lane'] = 'left'
        player['x'] = 100
        #player['prev_lane'] = 'center'
        
    if target_lane == 'left' and player['lane'] == 'center':
        player['lane'] = 'left'
        player['x'] = 100
        #player['prev_lane'] = 'center'
        hit_check.x = 162
        hit_check.y = player['y']
        clock.schedule(end_hit_check, 0.1)  # 保持极短时间在屏幕上绘制
        
    if target_lane == 'left' and player['lane'] == 'right':
        player['lane'] = 'center'
        #player['prev_lane'] = 'right'
        player['x'] = WIDTH/2
        hit_check.x = 285
        hit_check.y = player['y']
        clock.schedule(end_hit_check, 0.1)  # 保持极短时间在屏幕上绘制
    
    # 往右的三种情况
    elif target_lane == 'right' and player['lane'] == 'left':
        player['lane'] = 'center'
        #player['prev_lane'] = 'left'
        player['x'] = WIDTH/2
        hit_check.x = 162
        hit_check.y = player['y']
        clock.schedule(end_hit_check, 0.1)  # 保持极短时间在屏幕上绘制
        
    elif target_lane == 'right' and player['lane'] == 'center':
        player['lane'] = 'right'
        #player['prev_lane'] = 'center'
        player['x'] = 345
        hit_check.x = 285
        hit_check.y = player['y']
        clock.schedule(end_hit_check, 0.1)  # 保持极短时间在屏幕上绘制
        
    elif target_lane == 'right' and player['lane'] == 'right':
        player['lane'] = 'right'
        #player['prev_lane'] = 'center'
        player['x'] = 345

# ------------------------------------------------------------------- json文件 -------- #

def load_score():
    #获取coin.json文件中的所有金币数all_coin和历史最高金币数best_coin
    coin_file = Path('coin.json')
    default_data = {'all_coin': 0, 'best_coin': 0}
    
    try:
        if not coin_file.exists():
            with coin_file.open('w') as f:
                json.dump(default_data, f)
            return default_data['all_coin'], default_data['best_coin']
            
        with coin_file.open('r') as f:
            data = json.load(f)
            # 验证数据结构完整性
            all_coin = data.get('all_coin', 0)
            best_coin = data.get('best_coin', 0)
            return all_coin, best_coin
            
    except (json.JSONDecodeError, PermissionError) as e:
        print(f"加载分数文件时出错: {e}")
        return default_data['all_coin'], default_data['best_coin']

def save_score(coin):
    #保存数据到coin.json文件：
    #当前金币数为coin，更新all_coin为all_coin+=coin，若coin>best_coin则更新best_coin

    coin_file = Path('coin.json')
    default_data = {'all_coin': 0, 'best_coin': 0}
    
    try:
        # 读取原先数据
        if coin_file.exists():
            with coin_file.open('r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = default_data.copy()
        else:
            data = default_data.copy()
            
        # 更新数据
        data['all_coin'] = data.get('all_coin', 0) + coin
        if coin > data.get('best_coin', 0):
            data['best_coin'] = coin
            
        # 保存更新后的数据
        with coin_file.open('w') as f:
            json.dump(data, f, indent=2)
            
        return True
        
    except (IOError, PermissionError, TypeError) as e:
        print(f"保存分数文件时出错: {e}")
        return False

if game_over ==True:
    save_score(new_coin)

pgzrun.go()

    