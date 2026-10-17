"""Shiba Inu 结构性通缩模型分析。

模型核心：初始超发（约 1000 万亿枚）+ 交易销毁机制，长期走向通缩。
本脚本复现课程大作业《各种狗币投资研究》中 SHIB 的经济学建模，
模拟 20 年内的流通量、累计销毁量、年通缩率与剩余占比。

依赖：numpy / pandas / matplotlib。headless 环境自动保存 PNG。

Author: 李瑞宇（深圳大学 电子信息工程）
"""
import os
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator

matplotlib.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))


def simulate_shib_deflation(
    years=20, initial_supply=589e12, daily_volume=100e6, burn_rate=0.0001
):
    """模拟 SHIB 结构性通缩模型，返回 DataFrame。"""
    year = np.arange(0, years + 1)
    supply = np.zeros(years + 1)
    burned = np.zeros(years + 1)
    deflation_rate = np.zeros(years + 1)

    supply[0] = initial_supply
    volume_growth_rate = 0.2

    for i in range(1, years + 1):
        current_daily_volume = daily_volume * ((1 + volume_growth_rate) ** (i - 1))
        annual_burned = current_daily_volume * burn_rate * 365
        avg_price = 0.00001
        shib_burned = annual_burned / avg_price

        burned[i] = burned[i - 1] + shib_burned
        supply[i] = max(supply[i - 1] - shib_burned, 0)

        if supply[i - 1] > 0:
            deflation_rate[i] = (shib_burned / supply[i - 1]) * 100

    import pandas as pd

    return pd.DataFrame(
        {
            "年份": year,
            "流通总量(万亿枚)": supply / 1e12,
            "累计销毁量(万亿枚)": burned / 1e12,
            "年通缩率(%)": deflation_rate,
            "剩余流通占比(%)": (supply / initial_supply) * 100,
        }
    )


def plot(df_shib, out_path):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("SHIB结构性通缩模型分析", fontsize=16, fontweight="bold")

    def format_percent(x, pos):
        return f"{x:.2f}%"

    percent_formatter = FuncFormatter(format_percent)

    ax1 = axes[0, 0]
    ax1.plot(df_shib["年份"], df_shib["流通总量(万亿枚)"], "r-", linewidth=2.5, label="流通总量")
    ax1.fill_between(df_shib["年份"], 0, df_shib["流通总量(万亿枚)"], alpha=0.2, color="red")
    ax1.set_xlabel("年份")
    ax1.set_ylabel("流通总量 (万亿枚)")
    ax1.set_title("1. SHIB流通总量通缩趋势")
    ax1.grid(True, alpha=0.3, linestyle="--")
    ax1.legend(loc="upper right")
    ax1.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    ax2 = axes[0, 1]
    ax2.plot(df_shib["年份"], df_shib["累计销毁量(万亿枚)"], "purple", linewidth=2.5, label="累计销毁")
    ax2.fill_between(df_shib["年份"], 0, df_shib["累计销毁量(万亿枚)"], alpha=0.2, color="purple")
    ax2.set_xlabel("年份")
    ax2.set_ylabel("累计销毁量 (万亿枚)")
    ax2.set_title("2. SHIB累计销毁量增长")
    ax2.grid(True, alpha=0.3, linestyle="--")
    ax2.legend(loc="upper left")
    ax2.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    ax3 = axes[1, 0]
    ax3.plot(df_shib["年份"][1:], df_shib["年通缩率(%)"][1:], "g-", linewidth=2.5, label="年通缩率")
    ax3.set_xlabel("年份")
    ax3.set_ylabel("年通缩率")
    ax3.set_title("3. SHIB年通缩率变化")
    ax3.grid(True, alpha=0.3, linestyle="--")
    ax3.legend(loc="upper right")
    ax3.yaxis.set_major_formatter(percent_formatter)
    ax3.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    ax4 = axes[1, 1]
    ax4.plot(df_shib["年份"], df_shib["剩余流通占比(%)"], "orange", linewidth=2.5, label="剩余流通占比")
    ax4.axhline(y=50, color="r", linestyle="--", alpha=0.5, label="50%线")
    ax4.fill_between(df_shib["年份"], 0, df_shib["剩余流通占比(%)"], alpha=0.2, color="orange")
    ax4.set_xlabel("年份")
    ax4.set_ylabel("剩余流通占比")
    ax4.set_title("4. SHIB剩余流通量占比")
    ax4.grid(True, alpha=0.3, linestyle="--")
    ax4.legend(loc="upper right")
    ax4.yaxis.set_major_formatter(percent_formatter)
    ax4.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    plt.savefig(out_path, dpi=110)
    plt.close(fig)
    print("已保存:", out_path)


if __name__ == "__main__":
    df = simulate_shib_deflation(
        years=20, initial_supply=589e12, daily_volume=100e6, burn_rate=0.0001
    )
    out = os.path.join(HERE, "shiba_deflation.png")
    plot(df, out)

    print("SHIB结构性通缩模型关键指标")
    print("=" * 50)
    print(f"初始流通量: {df.loc[0, '流通总量(万亿枚)']:.1f} 万亿枚")
    print(f"最终流通量: {df.loc[20, '流通总量(万亿枚)']:.1f} 万亿枚")
    print(f"累计销毁量: {df.loc[20, '累计销毁量(万亿枚)']:.1f} 万亿枚")
    print(f"20年后剩余流通占比: {df.loc[20, '剩余流通占比(%)']:.1f}%")
    print(f"平均年通缩率: {df['年通缩率(%)'][1:].mean():.3f}%")
