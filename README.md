# 雷达CAN数据分析

本项目包含以下内容
* 雷达数据采集日志
* 雷达数据采集日志解析程序
* 数据可视化程序
* 车辆跟踪算法及可视化程序

## 文件说明
* /data 采集数据
* /res 可视化程序资源
* data_parser.py 解析采集日志将结果并保存为CSV文件
* car_following.py  car_followingv2.py 实现了跟踪算法即可视化
    * 依赖：displayer.py
* displayer.py 实现跟踪算法的可视化逻辑
* animate.py 数据可视化程序
