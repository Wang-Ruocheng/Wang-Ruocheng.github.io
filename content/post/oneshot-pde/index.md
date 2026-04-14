

---
title: "One-Shot Learning for PDE Solution Operators"
subtitle: "笔记：一种基于单个数据对的半监督算子学习方法"
summary: "探讨如何通过局部算子的平移不变性，在仅有一个数据样本的情况下求解复杂 PDE 系统。"
authors: ["admin"]
tags: ["Neural Operators", "Scientific AI", "PDE"]
categories: ["Academic Notes"]
date: 2026-02-01
lastmod: 2026-02-01

# 支持 LaTeX
math: true

image:
  caption: "One-shot learning workflow"
  focal_point: "Smart"
---
无监督学习的神经算子是一个很有前景的方向，其目的旨在缓解算子学习对于数据的依赖问题。最显著的就是物理信息神经算子（Physical-Informed Neural Operator），其可以在没有数据的情况下仅仅依靠方程形式来对算子本身进行学习。One-shot learning for solution operators of partial differential equations（https://www.nature.com/articles/s41467-025-63076-z）这篇文章则另外独辟蹊径，其尝试通过单个数据对$(u, v)$来学习整个算子解，可以视为一种半监督的算子学习方法。

此方法最早版本见于ICLR2021的workshop文章ONE-SHOT LEARNING FOR SOLUTION OPERATORS OF PARTIAL DIFFERENTIAL EQUATIONS（https://arxiv.org/pdf/2104.05512v1），最终版于2025年发表于nature communications。

出于习惯，笔记的符号与原论文略有出入，如下：

| 符号            | 笔记                       | 原论文                                           |
| --------------- | -------------------------- | ------------------------------------------------ |
| 输入函数        | $u$                      | $f$                                            |
| 解函数          | $v$                      | $u$                                            |
| One-shot 数据对 | $\mathcal T = (u_0,v_0)$ | $\mathcal T = (u_{\mathcal T},v_{\mathcal T})$ |

论文首先定义了问题形式，对于定义在$\Omega\sub \R^d$的系统：

$$
\mathcal F [u({\bf x});v({\bf x})]=0, {\bf x}\in \Omega
$$

定义解算子为

$$
\mathcal G:u({\bf x})\to  v({\bf x})
$$

常规的神经算子方法基于大量的数据对$\mathcal T = \set{(u_i,v_i)}$来学习，但作者指出我们可以仅仅通过单个数据对$\mathcal T = (u_0,v_0)$从学习整个域上的算子转为学习某个目标点${\bf x}^*$附近的解$\mathcal G(u)$。核心在于，我们可以在一个局部区域$\tilde \Omega$定义一个局部算子$\tilde {\mathcal G}$，其同样满足相同的偏微分方程。这个局部区域$\tilde \Omega$可以在$\Omega$上任意移动，我们定义不包含${\bf x}^*$位置的辅助区域为：

$$
\tilde{\Omega}_{aux}=\set{{\bf x}\in \tilde\Omega|\mathbf x\neq \mathbf x^*}
$$

局部算子$\tilde {\mathcal G}$的定义如下：

$$
\tilde {\mathcal G}: (\set{v(\mathbf x):\mathbf x\in \tilde{\Omega}_{aux}}, \set{u(\mathbf x):\mathbf x\in \tilde{\Omega}})\to v (\mathbf x^*)
$$

其实际上将辅助区域的解函数以及局部区域上的输入函数映射为了需要求解位置处的值。这里有个十分重要的点！就是局部算子仅仅依赖于局部区域上的输入函数，这看起来十分不合理，因为按理来说一个位置的解$v(\mathbf x^*)$不应该仅仅依赖于附近局域的输入函数$\set{u(\mathbf x):\mathbf x\in \tilde{\Omega}}$，所以作者仅仅考虑了具有局域性质的算子，即局域外的作用可以完全通过$\set{v(\mathbf x):\mathbf x\in \tilde{\Omega}_{\text{aux}}}$来获得，而在局域内本身可以完全通过这些信息来求解，如Poisson 方程、扩散反应方程。这是这项工作的一个显著限制。

> Our goal is to learn the solution operator of an unknown underlying PDE system that maps variable inputs to the corresponding solutions. We only consider PDEs that are well-posed with suitable initial and boundary conditions (IC/BCs). We do not consider nonlocal PDEs such as integral equations and fractional differential equations.

一个容易产生的疑问是：为什么这种方法不适用于积分方程？直观上看，简单的积分问题似乎可以通过局域信息解决。例如，若解函数 $v$ 只是输入函数 $u$ 的简单不定积分（即 $v(x) = \int_0^x u(t)dt$），此时我们确实可以通过步进关系 $v(x^*) \approx v(x^*-\delta x) + u(x^*) \delta x$ 来定义局域算子求解。在这种情况下，辅助点 $\tilde{\Omega}_{\text{aux}}$ 的解确实完全反映了$x^*$之前的所有输入函数信息。然而，作者在文中明确排除的是具有强非局部性的全局积分方程 。为了理解这一点可以对比一个经典的物理案例：电荷分布与电势的关系。假设想通过空间中分布的电荷密度 $u(\mathbf{y})$ 来求解某点 $\mathbf{x}^*$ 处的总电势 $v(\mathbf{x}^*)$：根据库仑定律，电势的计算是全局性的，$v(\mathbf{x}^*) = \int_{\Omega} \frac{u(\mathbf{y})}{|\mathbf{x}^*-\mathbf{y}|} d\mathbf{y}$。在这个系统中，即使离点 $\mathbf{x}^*$ 非常远，只要那个遥远的地方存在电荷，就会对 $\mathbf{x}^*$ 点的电势产生直接且不可忽略的贡献。在局域性质的PDE（如泊松方程）中，远端的影响会被区域边缘的数值所屏蔽或代表；但在这种全局积分系统中，边缘点无法屏蔽远端的场。这意味着，即使你观测到的局域辅助点$\mathbf x\in \tilde{\Omega}_{\text{aux}}$上的数值完全相同，只要局域之外的电荷分布输入发生了变化，中心点 $\mathbf{x}^*$ 的电势就会随之改变，因此也就无法定义一一映射的局部算子$\tilde {\mathcal G}$。

 原文中提供了若干种区域的选择划分方法如下：

`<img src="oneshot.png" alt="image-20260201215531177" style="zoom:40%;" />`

在训练时，对于one-shot获得的单个数据对$\mathcal T = (u_0,v_0)$，我们可以划分大量的$\tilde \Omega $来获得新的数据，从而学习局部算子$\tilde {\mathcal G}$。关键在于推理阶段，需要根据全新的输入函数$u\neq u_0$，以及学习后的局部算子$\tilde {\mathcal G}$来获得整个$\Omega$上的解函数。作者提供了三种方法：

1. FPI（Fixed-Point Iteration，不动点迭代）。模型输入为目标点 $\mathbf x^*$ 周围辅助点的当前解数值 $\{v(\mathbf x) : \mathbf x \in \tilde{\Omega}_{\text{aux}}\}$ 以及目标点处的输入函数值 $u(\mathbf x^*)$ ，输出为目标点 $x^*$ 处更新后的解数值 $u(x^*)$ 。方法的核心在于，在初始化一个猜测解 $v_0$ 后，直接应用预训练好的局部解算子 $\tilde{\mathcal{G}}$ 作为更新规则，在整个区域$\Omega$上不断迭代重复上面的映射，直到全域解趋于目标解$v$。可以预期，方程的真解$v$应该是迭代的结果。
2. LOINN（Local-solution-operator Informed Neural Network，局域解算子信息神经网络）），类似于物理信息神经网络（PINN），但约束项来自局部算子 。模型输入为计算域$\Omega$内的自变量 $\mathbf x$ ，输出为该坐标处对应的预测解 $v(\mathbf x; \theta)$ 。其训练的目标是要求输出在局部邻域内必须满足训练局部算子 $\tilde{\mathcal{G}}$ ，可以看作PINN的一个变体，不同之处在于其无需方程的显式形式，而是依靠一个从one-shot数据中获得的局部算子$\tilde{\mathcal{G}}$ 。
3. CLOINN（LOINN with Correction，修正局域解算子信息神经网络），LOINN 的改进版本，转而学习解与初始猜测解之间的修正量，输出为预测解 $v(x; \theta) = \mathcal{N}(x; \theta) + v_0(x)$ ，其中 $\mathcal{N}(x)$ 是神经网络直接输出的差值。类似ResNet的思想。可能收敛更快、更加稳定。

作者在文中测试了从线性到非线性、从一维到二维以及实际应用中的多种 PDE 系统 ：

1. 一维泊松方程（1D Poisson equation）：

$$
\Delta v = 100u(x), \quad x \in [0, 1]
$$

2. 线性扩散方程（Linear diffusion equation）：

$$
\frac{\partial v}{\partial t} = D \frac{\partial^2 v}{\partial x^2} + u(x), \quad x \in [0, 1], t \in [0, 1]
$$

3. 非线性扩散反应方程（Nonlinear diffusion-reaction equation）：

$$
\frac{\partial v}{\partial t} = D \frac{\partial^2 v}{\partial x^2} + kv^2 + u(x)
$$

4. 对流方程（Advection equation）：

$$
\frac{\partial v}{\partial t} + u(x) \frac{\partial v}{\partial x} = 0
$$

5. 二维非线性泊松方程（2D nonlinear Poisson equation）：

$$
\nabla \cdot ((1+v^2)\nabla v) = 10u(x, y)
$$

在正方形区域以及带圆孔的复杂几何区域中均进行了验证 。

6. 多孔介质中的扩散反应系统（A diffusion-reaction system in porous media）：

   $$
   \frac{\partial C_A}{\partial t}=D\frac{\part^2 C_A}{\partial x^2}-k_f C_AC_B^2+f(x)\\
   \frac{\partial C_B}{\partial t}=D\frac{\part^2 C_B}{\partial x^2}-2k_f C_A C_B^2
   $$
7. 传染病空间扩散模型（SIR model）：

$$
\frac{\partial S}{\partial t} = -D(x)\beta S \frac{\partial^2 I}{\partial x^2} - \beta SI, \quad \frac{\partial I}{\partial t} = D(x) \dots
$$

在仅使用一个训练数据点（One-shot）的情况下，该方法在测试集上的 $L^2$ 相对误差显著低于基准模型 。例如在 1D 泊松方程中，DeepONet 的预测误差高达 $20.73\%$，而本文方法可降至 $5\%$ 以下 。不同之处在于，FPI 和 CLOINN-random 在所有测试用例中均具有相当的优异性能 ，CLOINN 通常优于普通的 LOINN，不仅收敛更快，且由于学习的是修正量，其预测精度也更高 。在随机采样点上训练的效果通常优于固定网格点 。源代码开源于https://github.com/lu-group/one-shot-pde，作者额外提供了Jupyter脚本进行直观展示。
