from typing import Mapping
from math import tanh, cos, sin, pi
from displayer import TraceDisplay

class TrackTarget:

    THETA = (90 + 87.78) / 180 * pi

    @staticmethod
    def create_by_list(id, dx, dy, vx, vy):
        # 坐标转换
        nx = dx * cos(TrackTarget.THETA) - dy * sin(TrackTarget.THETA)
        ny = dx * sin(TrackTarget.THETA) + dy * cos(TrackTarget.THETA)
        t  = TrackTarget(id, nx, ny, vx, vy, True)
        return t

    def __init__(self, id, dx, dy, vx, vy, updated):
        # 雷达数据
        self.id = id
        self.dx = dx
        self.dy = dy
        self.vx = vx
        self.vy = vy

        # 模型数据
        self.m_dx = dx
        self.m_dy = dy
        self.m_vx = vx
        self.m_vy = vy
        
        # 标志位
        self.updated = updated

    def update_radar(self, t):
        """
        使用新目标数据更新雷达数据
        """
        self.dx = t.dx
        self.dy = t.dy
        self.vx = t.vx
        self.vy = t.vy
        self.updated = True

    def update_radar_and_model(self, t):
        """
        使用新目标数据更新模型数据和雷达数据
        """
        self.update_radar(t)
        self.m_dx = t.dx
        self.m_dy = t.dy
        self.m_vx = t.vx
        self.m_vy = t.vy

    def update_model_from_radar(self):
        """
        使用雷达数据更新模型数据
        """
        self.m_dx = self.dx
        self.m_dy = self.dy
        self.m_vx = self.vx
        self.m_vy = self.vy

    def is_stop(self):
        return self.m_vy == 0

    def __str__(self) -> str:
        return f'Target<id={self.id}, dx={int(self.dx)}, dy={int(self.dy)}, vx={int(self.vx)}, vy={int(self.vy)}, u={self.updated}, s={self.is_stop()}>'

    def __repr__(self) -> str:
        return self.__str__()

class TraceModel:
    def __init__(self, 
            frame_interval=0.02,  # 时间间隔
            stop_lane=-47,  # 停车线位置
            safe_speed=7,  # 安全车速
            car_length=4.8, # 车长
            update_speed=2.9,  # 速度判断阈值
            alpha = 2,  # 跟车模型
            vmax=10,  # 跟车模型
            hc=15,  # 跟车模型
            lanes=[2.23, 4.26, 6.92, 9.23] # 车道线坐标
        ):
        self.stop_lane = stop_lane
        self.safe_speed = safe_speed
        self.update_speed= update_speed
        self.alpha = alpha
        self.vmax = vmax
        self.hc = hc
        self.lanes = lanes
        self.car_length = car_length
        self.frame_interval = frame_interval
    
        self.tracked : Mapping[str, TrackTarget] = {}

    def on_new_frame(self, frame):
        new_targets = list(map(lambda t: TrackTarget.create_by_list(id=t[0], dx=t[2], dy=t[1], vx=t[5], vy=t[3]), frame))
        
        print(new_targets)

        updated_targets = []

        # 更新ID相同目标数据
        for new_target in new_targets:
            if new_target.id in self.tracked:
                tracked = self.tracked[new_target.id]
                # 只与标志为 update 的目标对比
                if not tracked.updated:
                    continue
                # TODO ID与lose中重复
                # 新数据速度大于阈值，更新雷达与模型数据
                if abs(new_target.vy) >= self.update_speed:
                    tracked.update_radar_and_model(new_target)
                # 新数据速度小于阈值，只更新雷达数据
                else:
                    tracked.update_radar(new_target)
                del self.tracked[tracked.id]
                new_targets.remove(new_target)
                updated_targets.append(tracked)
        
        # 与stop数据匹配
        for new_target in new_targets:
            matched_target = self.find_matched_stop_target(new_target)
            if matched_target is None:
                continue

            del self.tracked[matched_target.id]
            new_targets.remove(new_target)

            updated_targets.append(new_target)

        # 与lose数据匹配
        for new_target in new_targets:
            matched_target = self.find_matched_lose_taget(new_target)
            if matched_target is None:
                continue
            del self.tracked[matched_target.id]
            new_targets.remove(new_target)
            updated_targets.append(new_target)


        deleted_ids = []
        # 处理 lose 目标（剩余的目标一定是lose的）
        for t in self.tracked.values():
            # 标记为 false
            t.updated = False
            
            # 已停车目标保留原始位置
            if t.is_stop():
                continue
            
            # 超出范围目标直接删除
            if self.is_out_of_range(t):
                deleted_ids.append(t.id)
            else:
            # 未超出范围，更新模型数据
                # TODO 更新模型位置：需调整时间间隔
                t.m_vy += t.m_vx * self.frame_interval

        for idx in deleted_ids:
            del self.tracked[idx]

        # 将数据更新到跟踪目标中
        for t in updated_targets:
            self.tracked[t.id] = t

        # 将新目标添加到跟踪目标中
        for t in new_targets:
            self.tracked[t.id] = t

        group_by_lane = {}
        # 按车道对目标进行分组
        for t in self.tracked.values():
            group = group_by_lane.setdefault(self.get_lane(t), [])
            group.append(t)

        # 分别处理每个车道的车辆
        for group in group_by_lane.values():
            # sorted_group = sorted(filter(lambda t:t.updated, group), key=lambda t: t.dy)
            sorted_group = sorted(group, key=lambda t: abs(t.dy))
            if len(sorted_group) == 0:
                continue
            # 没有在停车线附近
            if not self.should_start_parking_process(sorted_group[0]):
                for t in sorted_group:
                    if t.vy < self.update_speed:
                        t.update_model_from_radar()
                continue
            # 在停车线附近
            prev_target = sorted_group[0]
            self.optimize_model_location(sorted_group[0])
            for t in sorted_group[1:]:
                if abs(t.vy) > self.update_speed:
                    prev_target = t
                    continue

                if abs(t.m_dy - prev_target.m_dy) > self.hc:
                    # TODO 判断正负
                    v, l = self.track_model(t, abs(t.m_dy - prev_target.m_dy))
                    t.m_vy = v
                    t.m_dy = prev_target.m_dy - l

                    if abs(t.m_dy - prev_target.m_dy) > self.hc:
                        prev_target = t
                        continue
                self.optimize_model_location(t)
                prev_target = t
            
        # 碰撞消失
        deleted_by_colsion = []
        for group in group_by_lane.values():
            sorted_group = sorted(group, key=lambda t:t.dy)
            if len(sorted_group) < 2:
                continue
            prev = sorted_group[0]
            for t in sorted_group[1:]:
                if abs(t.m_dy - prev.m_dy) <= self.car_length:
                    deleted_by_colsion.append(t)
                else:
                    prev = t
        for t in deleted_by_colsion:
            del self.tracked[t.id]
        
        return self.tracked.values()
        
    def track_model(self, t, l):
        a = self.alpha * (self.vmax / 2 * (tanh(l - self.hc) + tanh(self.hc))  + t.m_vy)
        # TODO 修改时间间隔
        v = t.m_vy - a * self.frame_interval
        l = abs(l) + v * self.frame_interval
        return v, l

    def optimize_model_location(self, t):
        """
        优化模型坐标
        """
        lane_no = self.get_lane(t)
        center = (self.lanes[lane_no] + self.lanes[lane_no + 1])/2
        t.m_dx = center
                
    def should_start_parking_process(self, t):
        """
        判断头车是否开始停车处理
        """
        # return  t.dy > self.stop_lane - self.car_length and t.dy < self.stop_lane + self.car_length and t.vy < self.update_speed
        # print(abs(t.dy - self.stop_lane) < 3, t.dy - self.stop_lane)
        return abs(t.dy - self.stop_lane) < self.car_length and abs(t.vy) < self.update_speed

    def get_lane(self, t):
        """
        获取车辆所在车道编号（从0开始）
        """
        loc1 = self.lanes[0]
        for idx, loc2 in enumerate(self.lanes[1:]):
            if t.dx > loc1 and t.dx <= loc2:
                return idx
            loc1 = loc2
        return -1

    def find_matched_stop_target(self, new_target):
        """
        查找与新目标匹配的停车车辆
        """
        for tracked in self.tracked.values():
            if tracked.updated or not tracked.is_stop():
                continue
            # 与 stop 目标匹配
            if self.is_in_same_lane(new_target, tracked) and abs(new_target.dy - tracked.dy) < 1:
                return tracked
        return None

    def find_matched_lose_taget(self, new_target):
        """
        查找与新目标匹配的丢失车辆
        """
        for tracked in self.tracked.values():
            if tracked.updated:
                continue
            if self.is_in_same_lane(new_target, tracked) and abs(new_target.dy - tracked.dy) < 1:
                return tracked
        return None

    def is_in_same_lane(self, new, old):
        """
        判断两个目标是否在同一车道
        """
        return self.get_lane(new) == self.get_lane(old)
        
    def is_out_of_range(self, t):
        # print(t)
        # print(f'{t.id} x={t.dx >= self.lanes[0] and t.dx < self.lanes[-1]} y={t.dy < self.stop_lane + self.car_length}')
        # return not (t.dx >= self.lanes[0] and t.dx < self.lanes[-1] and t.dy < self.stop_lane + self.car_length)
        print(t)
        print(f'{t.id} x={t.dx >= self.lanes[0] and t.dx < self.lanes[-1]} y={t.dy < -10}')
        return not (t.dx >= self.lanes[0] and t.dx < self.lanes[-1] and t.dy < -10)

class FrameSource:
    def __init__(self, filename):
        self.filename = filename

    def frames(self):
        with open(self.filename) as f:
            frame = []
            last_no = -1
            for line in f:
                item = list(map(float, line.split(',')))
                if item[4] != 2:
                    continue
                # 原始ID列0
                if item[7] != last_no and last_no != -1:
                    yield frame
                    frame.clear()
                frame.append(item)
                last_no = item[7]


if __name__ == '__main__':
    # source = FrameSource('./data-1104.csv')
    # source = FrameSource('./yanzheng5.csv')
    # source = FrameSource('./data-1104-3.csv')
    source = FrameSource('./2020_12_23.csv')
    model = TraceModel()
    display = TraceDisplay()
    for frame in source.frames():
        opted_frame = model.on_new_frame(frame)
        frame_src = list(map(lambda t: TrackTarget.create_by_list(id=t[0], dx=t[2], dy=t[1], vx=t[5], vy=t[3]), frame))
        display.update(opted_frame, frame_src)