#include <iostream>
#include <random>
#include <vector>
#include <algorithm>
#include <chrono>
#include <thread>
using namespace std;


/* utilisation d'un buffer pour les nombres random : incompatible avec le multithreading

std::random_device rd;
std::mt19937 gen;
std::uniform_int_distribution<short> distribution;
int id;
int taille_liste = 1'000'000'000;
short* random_buffer = nullptr;
void gen_random();
void init_random()
{
    gen = mt19937(rd());
    distribution = uniform_int_distribution<short>(1, 6);
    random_buffer = new short[taille_liste];
    gen_random();
}
void gen_random()
{
    id = 0;
    wcout << L"Génération du stock de nombres aléatoires...\n";
    // Chrono pour mesurer le temps de génération
    auto start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < taille_liste; i++)
    {
        random_buffer[i] = distribution(gen);
    }

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> temps_generation = end - start;
    std::wcout << L"Temps de génération : " << temps_generation.count() << L" secondes" << std::endl;
}

    static short& get_random()
   {
    if (id == taille_liste)
    {
        gen_random();
    }
    return random_buffer[id++];

}
*/





struct Random_base
{
    std::random_device rd;
    std::mt19937 gen;
    std::uniform_int_distribution<short> distribution;
    Random_base()
    {
        gen = mt19937(rd());
        distribution = uniform_int_distribution<short>(1, 6);
    }
    short get_random()
    {
        return this->distribution(gen);
    }
};



void help();

//Return the number of soldier remain at the end ob fight
static int simulate_fight(int defense, int attack,Random_base& alea)
{
    vector<short> die_defend;
    vector<short> die_attack;
    while (defense>0 && attack >0)
    {
        die_attack = vector<short>();
        die_defend = vector<short>();
        if (attack > 2)
        {
            die_attack.push_back(alea.get_random());
            die_attack.push_back(alea.get_random());
            die_attack.push_back(alea.get_random());
        }
        else if (attack == 2)
        {
            die_attack.push_back(alea.get_random());
            die_attack.push_back(alea.get_random());
        }
        else
        {
            die_attack.push_back(alea.get_random());
        }
        sort(die_attack.begin(), die_attack.end(), [](char a, char b) { return a > b; });

        if (defense > 1)
        {
            die_defend.push_back(alea.get_random());
            die_defend.push_back(alea.get_random());
        }
        else
        {
            die_defend.push_back(alea.get_random());
        }
        sort(die_defend.begin(), die_defend.end(), [](char a, char b) { return a > b; });

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

    return  (attack > 0)?(attack):(-defense);
}


#define RESULT_WIN(value) ((value&(0xFFFFFFFF00000000))>>32)
#define RESULT_MEAN_RESTE(value) (value&(0x00000000FFFFFFFF))
#define SET_RESULT_WIN(value) (value<<32)
#define SET_RESULT_MEAN_RESTE(value) (value)
#define SET_RETURN_ECHANTILLONNAGE(win,reste) (SET_RESULT_WIN(win) | SET_RESULT_MEAN_RESTE(reste))
/*
* Retourne le nombre de victoire sur n_echantillon avec n_defend defenseur et n_attack attaquant
* avec l'utilisation de n_thread
*/
static __int64 echantillonage(int n_defend, int n_attack, int n_echantillon,int n_thread)
{
    
    __int64 n_win = 0;
    int reste = 0;
    thread *threads = new thread[n_thread];
    int *n_wins = new int[n_thread];
    int* modulo = new int[n_thread];
    for (int i = 0; i < n_thread; i++)
    {
        threads[i] = thread([](int n_defend,int n_attack,int n_echantillon,int* out,int*reste) {
            //printf("lancement du thread sur %i valeurs\n", n_echantillon);
            *out = 0;
            *reste = 0;
            Random_base alea;
            for (int j = 0; j < n_echantillon; j++)
            {
                int temp = simulate_fight(n_defend, n_attack, alea);
                if(temp>0)
                    (*out)++;
                *reste += temp;
            }
            },n_defend,n_attack,(i<n_echantillon%n_thread)?(n_echantillon/n_thread+1):(n_echantillon/n_thread), & (n_wins[i]),&(modulo[i]));
    }
    for (int i = 0; i < n_thread; i++)
    {
        threads[i].join();
        n_win +=n_wins[i];
        reste += modulo[i];
    }
    delete[] n_wins;
    delete[] modulo;
    delete[] threads;
    return (reste>=0)?SET_RETURN_ECHANTILLONNAGE(n_win,reste) :-SET_RETURN_ECHANTILLONNAGE(n_win,-reste);
}

int main(int argc,char **argv) {
    
    int n_defence = 100;
    int n_attack = 85;
    int n_echantillon = 10000;
    int n_thread = thread::hardware_concurrency();
    bool verbose = true;
    for (int i = 0; i < argc; i++)
    {
        if (strcmp(argv[i], "--def")==0)
        {
            n_defence = stoi(argv[++i]);
        }else
        if (strcmp(argv[i], "--att") == 0)
        {
                n_attack = stoi(argv[++i]);
        }else
        if (strcmp(argv[i], "--thread") == 0)
        {
            n_thread = stoi(argv[++i]);
        }
        else
        if (strcmp(argv[i], "--N") == 0)
        {
                n_echantillon = stoi(argv[++i]);
        }else
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
    Random_base r;

    auto start = std::chrono::high_resolution_clock::now();

    if(verbose)
        cout << "Lancement de la simulation avec " << n_defence << " defenseurs, " << n_attack << " attaquants et " << n_thread << " threads de calcul sur "<<n_echantillon <<" calculs \n";
   
    auto result = echantillonage(n_defence, n_attack, n_echantillon, n_thread);
    if (verbose)
    {
        auto temp_result = result;
        bool sign = temp_result >= 0;
        if (!sign)
            temp_result *= -1;
        int win = RESULT_WIN(temp_result);
        int reste = RESULT_MEAN_RESTE(temp_result);
        cout << "Result : " << win << " victoires soit a rate of : " << (double)(win) / n_echantillon << " with a mean of " << (double)reste / n_echantillon << " soldier alive at the end" << std::endl;
        auto end = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double> temps_generation = end - start;
        std::cout << "Temps de generation : " << temps_generation.count() << " secondes" << std::endl;
        cout << result << endl;
    }
    
    cout.write((char*)&result,8);
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