
#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include <curand_kernel.h>
#include <stdio.h>
#include <iostream>
#include <time.h>
#include <chrono>
#include <string>
using namespace std;
void help();
#define SET_RESULT_WIN(value) (value<<32)
#define SET_RESULT_MEAN_RESTE(value) (value)
#define SET_RETURN_ECHANTILLONNAGE(win,reste) (SET_RESULT_WIN((__int64)win) | SET_RESULT_MEAN_RESTE((__int64)reste))
__device__ char dice(curandState_t& state)
{
    return 1 + (char)(curand_uniform(&state) * (6 - 1 + 1));
}

__device__ inline void sort(short* data, short size)
{
    if (size == 1)
        return;
    else if (size == 2)
    {
        
        if (data[0] < data[1])
        {
            short temp;
            temp = data[0];
            data[0] = data[1];
            data[1] = temp;
        }
        return;
    }
    else
    {
        short temp;
#define A data[0]
#define B data[1]
#define C data[2]
        
        if (A>B)
        {
            if (C > B)
            {
                temp = B;
                B = C;
                C = temp;
            }
            else {
                temp = A;
                A = C;
                C = B;
                B = temp;
            }
        }
        else
        {
            if (B > C)
            {
                if (A > C)
                {
                    temp = A;
                    A = B;
                    B = temp;
                }
                else
                {
                    temp = A;
                    A = B;
                    B = C;
                    C = temp;
                }
            }
            else
            {
                temp = A;
                A = C;
                C = temp;
            }
        }
    }
}

__device__ int simulateFight(int defense, int attack, curandState_t& state)
{
    short die_defend[3];
    short die_attack[3];
    while (defense > 0 && attack > 0)
    {
        if (attack > 2)
        {
            die_attack[0]=  dice(state);
            die_attack[1] = dice(state);
            die_attack[2] = dice(state);
        }
        else if (attack == 2)
        {
            die_attack[0] = dice(state);
            die_attack[1] = dice(state);
        }
        else
        {
            die_attack[0] = dice(state);
        }
        sort(die_attack, attack);
        

        if (defense > 1)
        {
            die_defend[0] = dice(state);
            die_defend[1] = dice(state);
        }
        else
        {
            die_defend[0] = dice(state);
        }
        sort(die_defend, defense);

        int _min = min(attack, defense);
        if (die_attack[0] > die_defend[0])
        {
            defense--;
        }
        else
            attack--;

        if (_min > 1)
        {
            if (die_attack[1] > die_defend[1])
            {
                defense--;
            }
            else
                attack--;
        }
    }

    return  (attack > 0) ? (attack) : (-defense);
}


__global__ void makeRandom(int *data, unsigned int size,unsigned int n_thread,int seed,int def,int att)
{
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    unsigned int id = threadIdx.x;
    int start = size/n_thread * id + min(size%n_thread,id) ;
    int end = size /n_thread*(id+1) + min(size % n_thread, id + 1);
    curandState_t state;

    curand_init(seed, tid, 0, &state); // Initialisation du générateur de nombres aléatoires
    for (int i = start; i < end; i++)
    {
        
        data[i] = simulateFight(def,att,state);
    }
    
}

int main(int argc,char **argv)
{
    int n_thread = 100,n_block = 1;
    int n_defence = 3, n_attack = 3;
    int n_echantillon = 1000;
    bool verbose = true;
    for (int i = 0; i < argc; i++)
    {
        if (strcmp(argv[i], "--def") == 0)
        {
            n_defence = std::stoi(argv[++i]);
        }
        else
            if (strcmp(argv[i], "--att") == 0)
            {
                n_attack = std::stoi(argv[++i]);
            }
            else
                if (strcmp(argv[i], "--thread") == 0)
                {
                    n_thread = std::stoi(argv[++i]);
                }
                else
                    if (strcmp(argv[i], "--N") == 0)
                    {
                        n_echantillon = std::stoi(argv[++i]);
                    }
                    else
                        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0)
                        {
                            help();
                            return 0;
                        }
                        else
                            if (strcmp(argv[i], "-q") == 0 || strcmp(argv[i], "--quiet") == 0)
                            {
                                verbose = false;
                            }
    }


    auto start = std::chrono::high_resolution_clock::now();


    int* cpu_data = new int[n_echantillon];
    int* gpu_data = nullptr;
    cudaMalloc(&gpu_data, n_echantillon * sizeof(int));
    unsigned int seed = (unsigned int)time(NULL); // Utiliser le temps actuel comme graine

    makeRandom << <n_block, n_thread >> > (gpu_data, n_echantillon, n_thread,seed, n_defence,n_attack);
    cudaDeviceSynchronize();
    cudaMemcpy(cpu_data, gpu_data, n_echantillon *sizeof(int), cudaMemcpyKind::cudaMemcpyDeviceToHost);


    int n_win = 0;
    int n_remaining = 0;
  
    for (int i = 0; i < n_echantillon; i++)
    {
        n_remaining += cpu_data[i];
        if (cpu_data[i] > 0)
            n_win++;
    }
    
    if (verbose)
    {
        double win_rate = (double)n_win / n_echantillon;
        double remaining_mean = (double)n_remaining / n_echantillon;

        cout << "Result : " << n_win << " victoires soit a rate of : " << (double)(n_win) / n_echantillon << " with a mean of " << (double)n_remaining / n_echantillon << " soldier alive at the end" << std::endl;
        auto end = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> temps_generation = end - start;
        std::cout << "Temps de generation : " << temps_generation.count() << " secondes" << std::endl;
    }
    cout.write((char*)&n_win, 4);
    cout.write((char*)&n_remaining, 4);
    return 0;
}


void help()
{
    cout << "Programme de simulation de calcul pour le jeu RISK (rien à voir avec RISC) from aze\n\
            arguments disponible : \n\
                -h --help : affiche ce message d'aide\n\
                --N : defini le nombre d'execution du calul avant de rencoyer la somme\n\
                --def : defini le nombre de soldat defenseur\n\
                --att : defini le nombre de soldat attaquants\n\
                --thread : defini le nombre de thread a utiliser pour les calculs\n\
                -q --quiet : desactive l'usage de la sortie standard pour un usage autre que le resultat\n\
\n\n            La valeur de retour designe ici les 8 derniers octets ecrit sur la sortie standard\n\
                La valeur de retour est encode comme ceci : \n\
                le signe indique le camp des soldats restant + pour les attauqants - pour les defenseurs\n\
                les 4 premiers octets indique le nombre de victoire des attaquants sur les N echantillons\n\
                les 4 dernniers octets indiquer le nombre de soldat restant à la fin de la bataille\n\
                il est attendu que ces octets soit pris sur la valeur absolue du code de retour.\n";



}