#include <iostream>
#include <time.h>
#include <stdlib.h>
#include <cmath>
#include <fstream>
#include <iomanip>
using namespace std;

const int NP = 40;             //��Ⱥ�Ĺ�ģ�����۷�+�۲��
const int FoodNumber = NP / 2; //ʳ���������Ϊ���۷������
const int limit = 20;          //�޶ȣ���������޶�û�и��²��۷�������
const int maxCycle = 10000;    //ֹͣ����

/*****�������ض�����*****/
const int D = 2;        //�����Ĳ�������
const double lb = -100; //�������½�
const double ub = 100;  //�������Ͻ�

double result[maxCycle] = {0};

/*****��Ⱥ�Ķ���****/
struct BeeGroup
{
    double code[D]; //������ά��
    double trueFit; //��¼��ʵ����Сֵ
    double fitness;
    double rfitness; //�����Ӧֵ����
    int trail;       //��ʾʵ��Ĵ�����������limit���Ƚ�
} Bee[FoodNumber];

BeeGroup NectarSource[FoodNumber]; //��Դ��ע�⣺һ�е��޸Ķ��������Դ���Ե�
BeeGroup EmployedBee[FoodNumber];  //���۷�
BeeGroup OnLooker[FoodNumber];     //�۲��
BeeGroup BestSource;               //��¼�����Դ

/*****����������*****/
double random(double, double);       //���������ϵ������
void initilize();                    //��ʼ������
double calculationTruefit(BeeGroup); //������ʵ�ĺ���ֵ
double calculationFitness(double);   //������Ӧֵ
void CalculateProbabilities();       //�������̶ĵĸ���
void evalueSource();                 //������Դ
void sendEmployedBees();
void sendOnlookerBees();
void sendScoutBees();
void MemorizeBestSource();

/*******������*******/
int main()
{
    ofstream output;
    output.open("dataABC.txt");

    srand((unsigned)time(NULL));
    initilize();          //��ʼ��
    MemorizeBestSource(); //������õ���Դ

    //��Ҫ��ѭ��
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
    cout << "���н���!!" << endl;
    return 0;
}

/*****������ʵ��****/
double random(double start, double end) //������������ڵ������
{
    return start + (end - start) * rand() / (RAND_MAX + 1.0);
}

void initilize() //��ʼ������
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
        /****��Դ�ĳ�ʼ��*****/
        NectarSource[i].trueFit = calculationTruefit(NectarSource[i]);
        NectarSource[i].fitness = calculationFitness(NectarSource[i].trueFit);
        NectarSource[i].rfitness = 0;
        NectarSource[i].trail = 0;
        /****���۷�ĳ�ʼ��*****/
        EmployedBee[i].trueFit = NectarSource[i].trueFit;
        EmployedBee[i].fitness = NectarSource[i].fitness;
        EmployedBee[i].rfitness = NectarSource[i].rfitness;
        EmployedBee[i].trail = NectarSource[i].trail;
        /****�۲��ĳ�ʼ��****/
        OnLooker[i].trueFit = NectarSource[i].trueFit;
        OnLooker[i].fitness = NectarSource[i].fitness;
        OnLooker[i].rfitness = NectarSource[i].rfitness;
        OnLooker[i].trail = NectarSource[i].trail;
    }
    /*****������Դ�ĳ�ʼ��*****/
    BestSource.trueFit = NectarSource[0].trueFit;
    BestSource.fitness = NectarSource[0].fitness;
    BestSource.rfitness = NectarSource[0].rfitness;
    BestSource.trail = NectarSource[0].trail;
}

double calculationTruefit(BeeGroup bee) //������ʵ�ĺ���ֵ
{
    double truefit = 0;
    /******���Ժ���1******/
    truefit = 0.5 + (sin(sqrt(bee.code[0] * bee.code[0] + bee.code[1] * bee.code[1])) * sin(sqrt(bee.code[0] * bee.code[0] + bee.code[1] * bee.code[1])) - 0.5) / ((1 + 0.001 * (bee.code[0] * bee.code[0] + bee.code[1] * bee.code[1])) * (1 + 0.001 * (bee.code[0] * bee.code[0] + bee.code[1] * bee.code[1])));

    return truefit;
}

double calculationFitness(double truefit) //������Ӧֵ
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

void sendEmployedBees() //�޸Ĳ��۷�ĺ���
{
    int i, j, k;
    int param2change; //��Ҫ�ı��ά��
    double Rij;       //[-1,1]֮��������
    for (i = 0; i < FoodNumber; i++)
    {

        param2change = (int)random(0, D); //���ѡȡ��Ҫ�ı��ά��

        /******ѡȡ������i��k********/
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

        /*******���۷�ȥ������Ϣ*******/
        Rij = random(-1, 1);
        EmployedBee[i].code[param2change] = NectarSource[i].code[param2change] + Rij * (NectarSource[i].code[param2change] - NectarSource[k].code[param2change]);
        /*******�ж��Ƿ�Խ��********/
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

        /******̰��ѡ�����*******/
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

void CalculateProbabilities() //�������̶ĵ�ѡ�����
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

void sendOnlookerBees() //���۷���۲�佻����Ϣ���۲�������Ϣ
{
    int i, j, t, k;
    double R_choosed; //��ѡ�еĸ���
    int param2change; //��Ҫ���ı��ά��
    double Rij;       //[-1,1]֮��������
    i = 0;
    t = 0;
    while (t < FoodNumber)
    {

        R_choosed = random(0, 1);
        if (R_choosed < NectarSource[i].rfitness) //���ݱ�ѡ��ĸ���ѡ��
        {
            t++;
            param2change = (int)random(0, D);

            /******ѡȡ������i��k********/
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

            /****����******/
            Rij = random(-1, 1);
            OnLooker[i].code[param2change] = NectarSource[i].code[param2change] + Rij * (NectarSource[i].code[param2change] - NectarSource[k].code[param2change]);

            /*******�ж��Ƿ�Խ��*******/
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

            /****̰��ѡ�����******/
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

/*******ֻ��һֻ����**********/
void sendScoutBees() //�ж��Ƿ�������ĳ��֣���������������Դ
{
    int maxtrialindex, i, j;
    double R; //[0,1]֮��������
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
        /*******���³�ʼ��*********/
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

void MemorizeBestSource() //�������ŵ���Դ
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
