from math import *
from random import *
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import time,sys,threading
import subprocess

last_n_win = 0
last_remaining = 0
def get_stat_cpu(n_defence:int,n_attack:int,n_echantillon:int)->tuple[int,int,float,float]:
    """Return number win  and mean of soldier remaining then rate of them"""
    global last_n_win,last_remaining
    process = subprocess.run([".\\RISK_CPP\\x64\\Release\\RISK_CPP.exe","--def",str(n_defence),"--att",str(n_attack),"--N",str(n_echantillon),'-q'],shell=True,capture_output=True)
    if process.returncode!=0:
        print(f"sdtout : {process.stdout} stderr : {process.stderr}")
        raise Exception("Erreur lors du lancement du noyau C++")

    n_win = int.from_bytes(process.stdout[-8:-4],"little",signed=True)
    n_soldier_remaining = int.from_bytes(process.stdout[-4:],"little",signed=True)
    mean_remaining = n_soldier_remaining/n_echantillon

    if  n_win< 0 or n_win>n_echantillon or abs(mean_remaining)>max(n_defence,n_attack):
        print(f"valeur aberrante sur le CPU : win rate : {n_win/n_echantillon} soldier remaining : {n_soldier_remaining} for {n_echantillon} echantillons and {max(n_defence,n_attack)} soldiers !")
        print(f"paramètres causant ce comportement  : --def {str(n_defence)} --att {str(n_attack)} --N {str(n_echantillon)} -q\n output : {process.stdout}")
        return last_n_win,last_remaining,last_n_win/n_echantillon,last_remaining/n_echantillon
    last_n_win = n_win
    las_mean_remaining = mean_remaining
    return n_win,mean_remaining,n_win/n_echantillon,n_soldier_remaining/n_echantillon

def get_stat_gpu(n_defence:int,n_attack:int,n_echantillon:int)->tuple[int,int,float,float]:
    """Return number win  and mean of soldier remaining then rate of them"""
    global last_n_win,last_remaining
    process = subprocess.run([".\\RISK_CUDA\\x64\\Release\\RISK_CUDA.exe","--def",str(n_defence),"--att",str(n_attack),"--N",str(n_echantillon),"-q"],shell=True,capture_output=True)
    if process.returncode!=0:
        print(f"stdout : {process.stdout} stderr : {process.stderr}")
        raise Exception("Erreur lors du lancement du noyau C++")
    
    n_win = int.from_bytes(process.stdout[-8:-4],"little",signed=True)
    n_soldier_remaining = int.from_bytes(process.stdout[-4:],"little",signed=True)
    mean_remaining = n_soldier_remaining/n_echantillon

    if n_win< 0 or n_win>n_echantillon or abs(mean_remaining)>max(n_defence,n_attack):
        print(f"valeur aberrante sur le GPU : win rate : {n_win/n_echantillon} soldier remaining : {n_soldier_remaining} for {n_echantillon} echantillons and {max(n_defence,n_attack)} soldiers !")
        print(f"paramètres causant ce comportement  : --def {str(n_defence)} --att {str(n_attack)} --N {str(n_echantillon)} -q\n output : {process.stdout}")
        return last_n_win,last_remaining,last_n_win/n_echantillon,last_remaining/n_echantillon
    last_n_win = n_win
    las_mean_remaining = mean_remaining
    return n_win,mean_remaining,n_win/n_echantillon,n_soldier_remaining/n_echantillon

def get_stat_python(n_defence:int,n_attack:int,n_echantillon:int)->tuple[int,int,float,float]:
    """Return number win  and mean of soldier remaining then rate of them"""
   

    n_win = 0
    n_soldier_remaining = 0

    for n in range(n_echantillon):
        DEF =  n_defence
        ATT = n_attack
        while DEF>0 and ATT>0:
            def_die = [randint(1,6) for i in range(min(3,DEF))]
            def_die.sort(reverse=True)
            att_die = [randint(1,6) for i in range(min(3,ATT))]
            att_die.sort(reverse=True)
            
            if min(DEF,ATT)==1:
                if att_die[0] > def_die[0]:
                    DEF-=1
                else:
                    ATT-=1
            else:
                if att_die[0] > def_die[0]:
                    DEF-=1
                else:
                    ATT-=1
                if att_die[1] > def_die[1]:
                    DEF-=1
                else:
                    ATT-=1
        if ATT>0:n_win+=1
        n_soldier_remaining+=ATT if(ATT>0)else -DEF

    mean_remaining = n_soldier_remaining/n_echantillon

    if  n_win< 0 or n_win>n_echantillon or abs(mean_remaining)>max(n_defence,n_attack):
        print(f"valeur aberrante sur le CPU : win rate : {n_win/n_echantillon} soldier remaining : {n_soldier_remaining} for {n_echantillon} echantillons and {max(n_defence,n_attack)} soldiers !")
        print(f"paramètres causant ce comportement  : --def {str(n_defence)} --att {str(n_attack)} --N {str(n_echantillon)} -q\n output : {process.stdout}")
        return last_n_win,last_remaining,last_n_win/n_echantillon,last_remaining/n_echantillon
    last_n_win = n_win
    las_mean_remaining = mean_remaining
    return n_win,mean_remaining,n_win/n_echantillon,n_soldier_remaining/n_echantillon

device = "gpu"

if device=="cpu":
    get_stat = get_stat_cpu
elif device=="gpu":
    get_stat = get_stat_gpu
elif device=="python":
    get_stat = get_stat_python
START_N = 1
END_N = 1500
STEPS = 10
SIZE = (END_N-START_N)//STEPS
TAILLE_ECHANTILLON = 10000

N_DEF =  np.array([[DEF for ATT in range(START_N,END_N,STEPS)] for DEF in range(START_N,END_N,STEPS)])
N_ATT = np.array([[ATT for ATT in range(START_N,END_N,STEPS)] for DEF in range(START_N,END_N,STEPS)])
N_REMAINING = np.zeros(N_DEF.shape)
N_WIN = np.zeros(N_DEF.shape)
change = False
end = False
x = 0
y = 0

def init():
    global x,y,end,change,N_DEF,N_ATT,N_REMAINING,N_WIN
    N_DEF =  np.array([[DEF for ATT in range(START_N,END_N,STEPS)] for DEF in range(START_N,END_N,STEPS)])
    N_ATT = np.array([[ATT for ATT in range(START_N,END_N,STEPS)] for DEF in range(START_N,END_N,STEPS)])
    N_REMAINING = np.zeros(N_DEF.shape)
    N_WIN = np.zeros(N_DEF.shape)
    change = False
    end = False
    x = 0
    y = 0


def computing():
    global x,y,change,end,SIZE,N_DEF,N_ATT,N_WIN,N_REMAINING
    for x in range(SIZE):
        for y in range(SIZE):
            DEF = N_DEF[x,y]
            ATT = N_ATT[x,y]
            win,remain,win_rate,remain_mean = get_stat(DEF,ATT,TAILLE_ECHANTILLON)
            N_WIN[x,y] = win_rate
            N_REMAINING[x,y] = remain_mean
            change = True
    end = True

last_start_time = time.monotonic()
start_time = time.monotonic()
last_x = 0
last_y  = 0

def update(index):
    global change
    
    if change:
        change = False
        global surf ,x,y,last_start_time,last_x,last_y
        ax.clear()
        surf = ax.plot_surface(X,Y,Z,cmap='viridis')
        # Étiquetage des axes
        ax.set_xlabel('N_DEF')
        ax.set_ylabel('N_ATT')
        ax.set_zlabel('Win_Rate')
        end_time = time.monotonic()
        print(f"update : {x}/{SIZE} {y}/{SIZE} soit {x*SIZE+y}/{SIZE*SIZE} <=> {round((x*SIZE+y)/(SIZE*SIZE)*100,2)}%  \
time elapsed since last iteration :  {round((end_time-last_start_time),2)} sec  pour  {(x-last_x)*SIZE+(y-last_y)} calculs soit {round(((x-last_x)*SIZE+(y-last_y))/(end_time-last_start_time),2)} calculs/s  et  {round((end_time-last_start_time)/((x-last_x)*SIZE+(y-last_y)),2)} s/calcul  time elapsed since begin : {round(time.monotonic()-start_time,0)} sec",
              end='\n'if(x==SIZE-1 and y==SIZE-1)else "\r")
        last_y = y
        last_x = x
        last_start_time = time.monotonic()
    if end:
        print("Fin de la génération !")
        ani.event_source.stop()
    return ax

X = N_DEF
Y = N_ATT
Z = N_WIN


# Initialisation du graphique
fig = plt.figure()
ax = fig.add_subplot(111,projection="3d")

surf = ax.plot_surface(X,Y,Z,cmap='viridis')



# Ajout d'une barre de couleur pour la surface
#fig.colorbar(surf)



ani = FuncAnimation(fig, update,frames=None, blit=False,interval=500,repeat=False)
compute = threading.Thread(target=computing)
compute.start()
# Affichage du graphe 3D
#ani.save('animation_3D.mp4', writer='ffmpeg', fps=30,savefig_kwargs={ 'pad_inches': 'tight'})
plt.show()

"""
last_start_time = time.monotonic()
def update(frame):
        global last_start_time
        i = x_data[frame]
        win,remain,win_rate,remain_mean = get_stat(i,ATT,TAILLE_ECHANTILLON)
        N_ATT.append(ATT)
        N_DEF.append(i)
        N_REMAINING.append(remain)
        N_WIN.append(win_rate*  ATT)
        
        for j, line in enumerate(lines):
            line.set_data(N_DEF, y_data[j])  # Mettre à jour les données du graphique
         # Mettre à jour les légendes
        if (i-START_N)%(STEPS*10) == 0:
            pass
        ax.autoscale_view()  # Ajuster automatiquement l'échelle des axes
        ax.relim()  # Recalculer les limites des axes en fonction des nouvelles données
        end_time = time.monotonic()
        print(i,"/",END_N,f" <=> {frame+1}/{len(x_data)} soit ",round((frame)/(len(x_data))*100,2),f"%    time elapsed since last iteration :  {round((end_time-last_start_time),2)} sec  ",end='\r'if(i<=END_N)else "\n")
        last_start_time = time.monotonic()
        return lines




#ani.save('animation_N_DEF.mp4', fps=30, extra_args=['-vcodec', 'libx264'])
plt.show()


"""