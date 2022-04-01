import numpy as np 
from matplotlib import pyplot as plt 
from matplotlib import animation

FN = 0
ID = 1
DY = 2
DX = 3
VY = 4
VX = 5
P  = 6
R  = 7



fig = plt.figure()
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(-100, 100)
ax.set_ylim(0, 300)

scat = ax.scatter([], [])


def new_frame():
    with open('data-1104.csv') as f:
        frame = []
        for line in f:
            obj = tuple(map(float, line.split(',')))
            if obj[VY] < 0 or obj[P] != 0:
                continue
            if len(frame) > 0 and frame[0][0] != obj[0]:
                yield frame
                frame.clear()
            frame.append(obj)


def animate(objs):
    locs = []
    for obj in objs:
        locs.append((obj[DX], obj[DY]))
    print(len(locs))
    scat.set_offsets(locs)

anim = animation.FuncAnimation(fig, animate, new_frame, interval=20, blit=False) 
plt.show() 