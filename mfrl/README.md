# fork from https://github.com/mlii/mfrl
这是这篇paper [《Mean Field Multi-Agent Reinforcement Learning》](https://arxiv.org/pdf/1802.05438.pdf)中的MF-Q和MF-AC算法的实现

# 一些想法：
虽然还没完全看懂这个代码，但是code感觉和paper里的algo有区别:

1.在伊辛模型里看不到MF的应用（明天再看看）

2.在battle_model，ValueNet的定义是不是》。。？

3.不知道为啥没有高斯压缩的model_code

# 下面为原README.md的说明

## Example

![image](https://github.com/mlii/mfrl/blob/master/resources/line.gif)
 
 An 20x20 Ising model example under the low temperature.

<img src="https://github.com/mlii/mfrl/blob/master/resources/battle.gif" width='300' height='300'/>

 A 40x40 Battle Game gridworld example with 128 agents, the blue one is MFQ, and the red one is IL.
 
## Code structure

- `main_MFQ_Ising.py`: contains code for running tabular based MFQ for Ising model.

- `./examples/`: contains scenarios for Ising Model and Battle Game (also models).

- `battle.py`: contains code for running Battle Game with trained model

- `train_battle.py`: contains code for training Battle Game models

## Compile Ising environment and run

**Requirements**
- `python==3.6.1`
- `gym==0.9.2` (might work with later versions)
- `matplotlib` if you would like to produce Ising model figures

## Compile MAgent platform and run

Before running Battle Game environment, you need to compile it. You can get more helps from: [MAgent](https://github.com/geek-ai/MAgent)

**Steps for compiling**

```shell
cd examples/battle_model
./build.sh
```

**Steps for training models under Battle Game settings**

1. Add python path in your `~/.bashrc` or `~/.zshrc`:

    ```shell
    vim ~/.zshrc
    export PYTHONPATH=./examples/battle_model/python:${PYTHONPATH}
    source ~/.zshrc
    ```

2. Run training script for training (e.g. mfac):

    ```shell
    python3 train_battle.py --algo mfac
    ```

    or get help:

    ```shell
    python3 train_battle.py --help
    ```
