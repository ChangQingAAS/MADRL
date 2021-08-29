#include <iostream>
#include <time.h>
#include <stdlib.h>
#include <cmath>
#include <fstream>
#include <iomanip>
using namespace std;

const int NP = 40;             //种群的规模，采蜜蜂+观察蜂
const int FoodNumber = NP / 2; //食物的数量，为采蜜蜂的数量
const int limit = 20;          //限度，超过这个限度没有更新采蜜蜂变成侦查蜂
const int maxCycle = 10000;    //停止条件

/*****函数的特定参数*****/
const int D = 2;        //函数的参数个数
const double lb = -100; //函数的下界
const double ub = 100;  //函数的上界

double result[maxCycle] = {0};

/*****种群的定义****/
struct BeeGroup
{
    double code[D]; //函数的维数
    double trueFit; //记录真实的最小值
    double fitness;
    double rfitness; //相对适应值比例
    int trail;       //表示实验的次数，用于与limit作比较
} Bee[FoodNumber];

BeeGroup NectarSource[FoodNumber]; //蜜源，注意：一切的修改都是针对蜜源而言的
BeeGroup EmployedBee[FoodNumber];  //采蜜蜂
BeeGroup OnLooker[FoodNumber];     //观察蜂
BeeGroup BestSource;               //记录最好蜜源

/*****函数的声明*****/
double random(double, double);       //产生区间上的随机数
void initilize();                    //初始化参数
double calculationTruefit(BeeGroup); //计算真实的函数值
double calculationFitness(double);   //计算适应值
void CalculateProbabilities();       //计算轮盘赌的概率
void evalueSource();                 //评价蜜源
void sendEmployedBees();
void sendOnlookerBees();
void sendScoutBees();
void MemorizeBestSource();

/*******主函数*******/
int main()
{
    ofstream output;
    output.open("dataABC.txt");

    srand((unsigned)time(NULL));
    initilize();          //初始化
    MemorizeBestSource(); //保存最好的蜜源

    //主要的循环
    int gen = 0;
    while (gen < maxCycle)
    {
        sendEmployedBees();

        CalculateProbabilities();

        sendOnlookerBees();

        MemorizeBestSource();

        sendScoutBees();

        MemorizeBestSource();

        output << setprecision(30) << BestSource.trueFit << endl;

        gen++;
    }

    output.close();
    cout << "运行结束!!" << endl;
    return 0;
}

/*****函数的实现****/
double random(double start, double end) //随机产生区间内的随机数
{
    return start + (end - start) * rand() / (RAND_MAX + 1.0);
}

void initilize() //初始化参数
{
    int i, j;
    for (i = 0; i < FoodNumber; i++)
    {
        for (j = 0; j < D; j++)
        {
            NectarSource[i].code[j] = random(lb, ub);
            EmployedBee[i].code[j] = NectarSource[i].code[j];
            OnLooker[i].code[j] = NectarSource[i].code[j];
            BestSource.code[j] = NectarSource[0].code[j];
        }
        /****蜜源的初始化*****/
        NectarSource[i].trueFit = calculationTruefit(NectarSource[i]);
        NectarSource[i].fitness = calculationFitness(NectarSource[i].trueFit);
        NectarSource[i].rfitness = 0;
        NectarSource[i].trail = 0;
        /****采蜜蜂的初始化*****/
        EmployedBee[i].trueFit = NectarSource[i].trueFit;
        EmployedBee[i].fitness = NectarSource[i].fitness;
        EmployedBee[i].rfitness = NectarSource[i].rfitness;
        EmployedBee[i].trail = NectarSource[i].trail;
        /****观察蜂的初始化****/
        OnLooker[i].trueFit = NectarSource[i].trueFit;
        OnLooker[i].fitness = NectarSource[i].fitness;
        OnLooker[i].rfitness = NectarSource[i].rfitness;
        OnLooker[i].trail = NectarSource[i].trail;
    }
    /*****最优蜜源的初始化*****/
    BestSource.trueFit = NectarSource[0].trueFit;
    BestSource.fitness = NectarSource[0].fitness;
    BestSource.rfitness = NectarSource[0].rfitness;
    BestSource.trail = NectarSource[0].trail;
}

double calculationTruefit(BeeGroup bee) //计算真实的函数值
{
    double truefit = 0;
    /******测试函数1******/
    truefit = 0.5 + (sin(sqrt(bee.code[0] * bee.code[0] + bee.code[1] * bee.code[1])) * sin(sqrt(bee.code[0] * bee.code[0] + bee.code[1] * bee.code[1])) - 0.5) / ((1 + 0.001 * (bee.code[0] * bee.code[0] + bee.code[1] * bee.code[1])) * (1 + 0.001 * (bee.code[0] * bee.code[0] + bee.code[1] * bee.code[1])));

    return truefit;
}

double calculationFitness(double truefit) //计算适应值
{
    double fitnessResult = 0;
    if (truefit >= 0)
    {
        fitnessResult = 1 / (truefit + 1);
    }
    else
    {
        fitnessResult = 1 + abs(truefit);
    }
    return fitnessResult;
}

void sendEmployedBees() //修改采蜜蜂的函数
{
    int i, j, k;
    int param2change; //需要改变的维数
    double Rij;       //[-1,1]之间的随机数
    for (i = 0; i < FoodNumber; i++)
    {

        param2change = (int)random(0, D); //随机选取需要改变的维数

        /******选取不等于i的k********/
        while (1)
        {
            k = (int)random(0, FoodNumber);
            if (k != i)
            {
                break;
            }
        }

        for (j = 0; j < D; j++)
        {
            EmployedBee[i].code[j] = NectarSource[i].code[j];
        }

        /*******采蜜蜂去更新信息*******/
        Rij = random(-1, 1);
        EmployedBee[i].code[param2change] = NectarSource[i].code[param2change] + Rij * (NectarSource[i].code[param2change] - NectarSource[k].code[param2change]);
        /*******判断是否越界********/
        if (EmployedBee[i].code[param2change] > ub)
        {
            EmployedBee[i].code[param2change] = ub;
        }
        if (EmployedBee[i].code[param2change] < lb)
        {
            EmployedBee[i].code[param2change] = lb;
        }
        EmployedBee[i].trueFit = calculationTruefit(EmployedBee[i]);
        EmployedBee[i].fitness = calculationFitness(EmployedBee[i].trueFit);

        /******贪婪选择策略*******/
        if (EmployedBee[i].trueFit < NectarSource[i].trueFit)
        {
            for (j = 0; j < D; j++)
            {
                NectarSource[i].code[j] = EmployedBee[i].code[j];
            }
            NectarSource[i].trail = 0;
            NectarSource[i].trueFit = EmployedBee[i].trueFit;
            NectarSource[i].fitness = EmployedBee[i].fitness;
        }
        else
        {
            NectarSource[i].trail++;
        }
    }
}

void CalculateProbabilities() //计算轮盘赌的选择概率
{
    int i;
    double maxfit;
    maxfit = NectarSource[0].fitness;
    for (i = 1; i < FoodNumber; i++)
    {
        if (NectarSource[i].fitness > maxfit)
            maxfit = NectarSource[i].fitness;
    }

    for (i = 0; i < FoodNumber; i++)
    {
        NectarSource[i].rfitness = (0.9 * (NectarSource[i].fitness / maxfit)) + 0.1;
    }
}

void sendOnlookerBees() //采蜜蜂与观察蜂交流信息，观察蜂更改信息
{
    int i, j, t, k;
    double R_choosed; //被选中的概率
    int param2change; //需要被改变的维数
    double Rij;       //[-1,1]之间的随机数
    i = 0;
    t = 0;
    while (t < FoodNumber)
    {

        R_choosed = random(0, 1);
        if (R_choosed < NectarSource[i].rfitness) //根据被选择的概率选择
        {
            t++;
            param2change = (int)random(0, D);

            /******选取不等于i的k********/
            while (1)
            {
                k = (int)random(0, FoodNumber);
                if (k != i)
                {
                    break;
                }
            }

            for (j = 0; j < D; j++)
            {
                OnLooker[i].code[j] = NectarSource[i].code[j];
            }

            /****更新******/
            Rij = random(-1, 1);
            OnLooker[i].code[param2change] = NectarSource[i].code[param2change] + Rij * (NectarSource[i].code[param2change] - NectarSource[k].code[param2change]);

            /*******判断是否越界*******/
            if (OnLooker[i].code[param2change] < lb)
            {
                OnLooker[i].code[param2change] = lb;
            }
            if (OnLooker[i].code[param2change] > ub)
            {
                OnLooker[i].code[param2change] = ub;
            }
            OnLooker[i].trueFit = calculationTruefit(OnLooker[i]);
            OnLooker[i].fitness = calculationFitness(OnLooker[i].trueFit);

            /****贪婪选择策略******/
            if (OnLooker[i].trueFit < NectarSource[i].trueFit)
            {
                for (j = 0; j < D; j++)
                {
                    NectarSource[i].code[j] = OnLooker[i].code[j];
                }
                NectarSource[i].trail = 0;
                NectarSource[i].trueFit = OnLooker[i].trueFit;
                NectarSource[i].fitness = OnLooker[i].fitness;
            }
            else
            {
                NectarSource[i].trail++;
            }
        }
        i++;
        if (i == FoodNumber)
        {
            i = 0;
        }
    }
}

/*******只有一只侦查蜂**********/
void sendScoutBees() //判断是否有侦查蜂的出现，有则重新生成蜜源
{
    int maxtrialindex, i, j;
    double R; //[0,1]之间的随机数
    maxtrialindex = 0;
    for (i = 1; i < FoodNumber; i++)
    {
        if (NectarSource[i].trail > NectarSource[maxtrialindex].trail)
        {
            maxtrialindex = i;
        }
    }
    if (NectarSource[maxtrialindex].trail >= limit)
    {
        /*******重新初始化*********/
        for (j = 0; j < D; j++)
        {
            R = random(0, 1);
            NectarSource[maxtrialindex].code[j] = lb + R * (ub - lb);
        }
        NectarSource[maxtrialindex].trail = 0;
        NectarSource[maxtrialindex].trueFit = calculationTruefit(NectarSource[maxtrialindex]);
        NectarSource[maxtrialindex].fitness = calculationFitness(NectarSource[maxtrialindex].trueFit);
    }
}

void MemorizeBestSource() //保存最优的蜜源
{
    int i, j;
    for (i = 1; i < FoodNumber; i++)
    {
        if (NectarSource[i].trueFit < BestSource.trueFit)
        {
            for (j = 0; j < D; j++)
            {
                BestSource.code[j] = NectarSource[i].code[j];
            }
            BestSource.trueFit = NectarSource[i].trueFit;
        }
    }
}
