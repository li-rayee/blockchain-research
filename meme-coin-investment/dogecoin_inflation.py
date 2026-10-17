"""Dogecoin 适应性通货膨胀模型分析。

模型核心：无限供应 + 固定年增发（约 52.6 亿枚/年）。
本脚本复现课程大作业《各种狗币投资研究》中 Dogecoin 的经济学建模，
给出 30 年流通量、通胀率衰减、以及与比特币固定总量模型的对比。

运行环境：Python 3.8+，依赖 numpy / matplotlib。
在 headless 环境（无显示器）下自动保存为 PNG，而非弹窗。

Author: 李瑞宇（深圳大学 电子信息工程）
"""
import os
import numpy as np
import matplotlib

matplotlib.use("Agg")  # 无显示器环境也能跑
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

# 中文标签回退：系统无 SimHei 时退到 DejaVu Sans（仅影响渲染，不影响计算）
matplotlib.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))


def format_percent(x, pos):
    """百分比刻度格式化。"""
    return f"{x:.1f}%"


def simulate_and_plot_fixed():
    """模拟并绘制 Dogecoin 适应性通胀模型。"""
    years = 30
    initial_supply = 142.67e9  # 当前流通量
    annual_issuance = 5.256e9  # 年增发量

    year = np.arange(0, years + 1)
    supply = np.zeros(years + 1)
    inflation_rate = np.zeros(years + 1)
    issuance_percentage = np.zeros(years + 1)

    supply[0] = initial_supply

    for i in range(1, years + 1):
        supply[i] = supply[i - 1] + annual_issuance
        inflation_rate[i] = (annual_issuance / supply[i - 1]) * 100
        issuance_percentage[i] = (annual_issuance / supply[i]) * 100

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("狗狗币适应性通货膨胀模型分析", fontsize=16, fontweight="bold")

    percent_formatter = FuncFormatter(format_percent)

    # 1. 流通总量线性增长
    ax1 = axes[0, 0]
    ax1.plot(year, supply / 1e9, "b-", linewidth=2.5, label="流通总量")
    ax1.fill_between(year, 0, supply / 1e9, alpha=0.2, color="blue")
    ax1.set_xlabel("年份")
    ax1.set_ylabel("流通总量 (十亿枚)")
    ax1.set_title("1. 流通总量线性增长")
    ax1.grid(True, alpha=0.3, linestyle="--")
    ax1.legend(loc="upper left")
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
    ax1.yaxis.set_major_locator(MaxNLocator(nbins=6))

    # 2. 通胀率衰减曲线
    ax2 = axes[0, 1]
    ax2.plot(year[1:], inflation_rate[1:], "r-", linewidth=2.5, label="通胀率")
    ax2.set_xlabel("年份")
    ax2.set_ylabel("年通货膨胀率")
    ax2.set_title("2. 通货膨胀率衰减曲线 (双曲线下降)")
    ax2.grid(True, alpha=0.3, linestyle="--")
    ax2.legend(loc="upper right")
    ax2.yaxis.set_major_formatter(percent_formatter)
    ax2.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    # 3. 与比特币通胀模型对比
    ax3 = axes[1, 0]
    btc_inflation = []
    btc_supply = 19.2e6
    btc_total = 21e6
    btc_block_reward = 6.25
    blocks_per_year = 144 * 365

    for y in range(years + 1):
        if y in [4, 8, 12, 16, 20, 24, 28]:
            btc_block_reward /= 2
        btc_issuance = btc_block_reward * blocks_per_year
        btc_inflation.append((btc_issuance / btc_supply) * 100 if btc_supply > 0 else 0)
        btc_supply = min(btc_supply + btc_issuance, btc_total)

    ax3.plot(year, inflation_rate, "b-", linewidth=2.5, label="狗狗币 (适应性通胀)")
    ax3.plot(year, btc_inflation, "g-", linewidth=2.5, label="比特币 (固定总量)", alpha=0.8)
    ax3.set_xlabel("年份")
    ax3.set_ylabel("年通货膨胀率")
    ax3.set_title("3. 通胀模型对比: 适应性通胀 vs 固定总量")
    ax3.grid(True, alpha=0.3, linestyle="--")
    ax3.legend()
    ax3.yaxis.set_major_formatter(percent_formatter)
    ax3.set_yscale("log")
    ax3.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    # 4. 年增发占比变化
    ax4 = axes[1, 1]
    ax4.plot(year[1:], issuance_percentage[1:], "purple", linewidth=2.5, label="年增发占比")
    ax4.set_xlabel("年份")
    ax4.set_ylabel("年增发量占流通量比例")
    ax4.set_title("4. 固定增发在流通量中占比变化")
    ax4.grid(True, alpha=0.3, linestyle="--")
    ax4.legend(loc="upper right")
    ax4.yaxis.set_major_formatter(percent_formatter)
    ax4.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    out = os.path.join(HERE, "dogecoin_inflation.png")
    plt.savefig(out, dpi=110)
    plt.close(fig)
    print("已保存:", out)

    metrics = {
        "initial_supply_billion": initial_supply / 1e9,
        "annual_issuance_billion": annual_issuance / 1e9,
        "initial_inflation_pct": inflation_rate[1],
        "final_inflation_pct": inflation_rate[-1],
        "final_supply_billion": supply[-1] / 1e9,
        "avg_decay_pct_per_yr": (inflation_rate[1] - inflation_rate[-1]) / years,
    }
    return metrics


if __name__ == "__main__":
    m = simulate_and_plot_fixed()
    print("狗狗币适应性通货膨胀模型关键指标")
    print("=" * 50)
    print(f"初始流通量: {m['initial_supply_billion']:.2f} 十亿枚")
    print(f"年固定增发: {m['annual_issuance_billion']:.2f} 十亿枚")
    print(f"初始通胀率: {m['initial_inflation_pct']:.2f}%")
    print(f"{30}年后通胀率: {m['final_inflation_pct']:.4f}%")
    print(f"{30}年后流通量: {m['final_supply_billion']:.2f} 十亿枚")
    print(f"年均通胀率衰减: {m['avg_decay_pct_per_yr']:.4f}%/年")
