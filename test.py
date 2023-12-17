import matplotlib.pyplot as plt
import matplotlib.animation as animation

fig, ax = plt.subplots()
x = [1, 2, 3, 4, 5]
y = [2, 4, 6, 8, 10]
line, = ax.plot(x, y)

def update(num):
    line.set_ydata(y[:num])
    return line,

ani = animation.FuncAnimation(fig, update, frames=len(x), interval=500, blit=True)
ani.save('animation.mp4', writer='ffmpeg', fps=30)
