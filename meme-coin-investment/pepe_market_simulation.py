"""Pepe 固定供应模型 —— 纯粹博弈市场模拟。

模型核心：总量固定（420.69 万亿枚）+ 无生态/无销毁，价格完全由
叙事、事件与交易者博弈驱动。本脚本复现课程大作业《各种狗币投资研究》
中 PEPE 的市场行为建模：用事件驱动的随机游走刻画价格、收益率分布、
市值、持有者增长与价格自相关性。

依赖：numpy / pandas / matplotlib / scipy。headless 环境自动保存 PNG。

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


def simulate_pepe_fixed_supply(
    total_days=365, initial_price=0.000001, total_supply=420.69e12, initial_market_cap=1e6
):
    """模拟 PEPE 固定供应模型下的价格行为，返回 DataFrame。"""
    if initial_price <= 0:
        initial_price = initial_market_cap / total_supply

    days = np.arange(0, total_days)
    prices = np.zeros(total_days)
    volumes = np.zeros(total_days)
    market_caps = np.zeros(total_days)
    holders = np.zeros(total_days)

    prices[0] = initial_price
    volumes[0] = 1e6
    market_caps[0] = prices[0] * total_supply
    holders[0] = 10000

    base_volatility = 0.4
    volume_impact = 0.001
    holder_growth_rate = 0.001

    event_days = {
        30: {"type": "positive", "impact": 5.0, "description": "交易所上线"},
        60: {"type": "negative", "impact": 0.3, "description": "大户抛售"},
        120: {"type": "positive", "impact": 3.0, "description": "名人提及"},
        180: {"type": "negative", "impact": 0.2, "description": "市场回调"},
        240: {"type": "positive", "impact": 2.0, "description": "社区活动"},
        300: {"type": "negative", "impact": 0.4, "description": "竞争加剧"},
    }

    np.random.seed(42)  # 确保可重现
    for day in range(1, total_days):
        daily_return = np.random.normal(0, base_volatility)
        volume_change = volumes[day - 1] / volumes[max(0, day - 2)] if day > 1 else 1
        volume_effect = (volume_change - 1) * volume_impact
        holder_growth = (
            (holders[day - 1] - holders[max(0, day - 2)]) / holders[max(0, day - 2)]
            if day > 1
            else 0
        )
        network_effect = holder_growth * 0.01

        event_effect = 1.0
        if day in event_days:
            event = event_days[day]
            event_effect = event["impact"]

        new_price = (
            prices[day - 1]
            * (1 + daily_return + volume_effect + network_effect)
            * event_effect
        )
        prices[day] = max(new_price, initial_price * 0.0001)

        volumes[day] = volumes[day - 1] * np.random.lognormal(-0.1, 0.5)
        holders[day] = holders[day - 1] * (1 + holder_growth_rate + np.random.normal(0, 0.01))
        market_caps[day] = prices[day] * total_supply

        if day > 10:
            recent_return = (prices[day] / prices[day - 10]) - 1
            volumes[day] *= (1 + recent_return * 2)

    import pandas as pd

    return pd.DataFrame(
        {
            "天数": days,
            "价格(美元)": prices,
            "日交易量(百万美元)": volumes / 1e6,
            "市值(百万美元)": market_caps / 1e6,
            "持有者数量": holders,
            "日收益率(%)": np.concatenate(([0], np.diff(prices) / prices[:-1] * 100)),
        }
    )


def plot(df_pepe, out_path):
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle("PEPE固定供应模型 - 纯粹博弈市场", fontsize=16, fontweight="bold")

    ax1 = axes[0, 0]
    ax1.plot(df_pepe["天数"], df_pepe["价格(美元)"], "g-", linewidth=1.5, alpha=0.8)
    ax1.set_xlabel("天数")
    ax1.set_ylabel("价格(美元)")
    ax1.set_title("1. PEPE价格走势 (固定供应)")
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale("log")

    events = {30: "交易所上线", 60: "大户抛售", 120: "名人提及", 180: "市场回调", 240: "社区活动", 300: "竞争加剧"}
    for day, event in events.items():
        if day < len(df_pepe):
            ax1.axvline(x=day, color="r", linestyle="--", alpha=0.3, linewidth=0.5)
            ax1.text(day, df_pepe.loc[day, "价格(美元)"] * 1.5, event, rotation=90, fontsize=8, alpha=0.7)

    ax2 = axes[0, 1]
    returns = df_pepe["日收益率(%)"][1:]
    ax2.hist(returns, bins=50, edgecolor="black", alpha=0.7, color="green")
    ax2.axvline(x=returns.mean(), color="r", linestyle="--", label=f"均值: {returns.mean():.2f}%")
    ax2.axvline(x=returns.std(), color="b", linestyle="--", label=f"标准差: {returns.std():.2f}%")
    ax2.set_xlabel("日收益率(%)")
    ax2.set_ylabel("频数")
    ax2.set_title("2. 日收益率分布 (肥尾特征)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3 = axes[0, 2]
    scatter = ax3.scatter(
        df_pepe["价格(美元)"][1:],
        df_pepe["日交易量(百万美元)"][1:],
        c=df_pepe["日收益率(%)"][1:],
        cmap="RdYlGn",
        alpha=0.6,
        s=20,
        edgecolors="none",
    )
    ax3.set_xlabel("价格(美元)")
    ax3.set_ylabel("日交易量(百万美元)")
    ax3.set_title("3. 价格-交易量关系")
    ax3.grid(True, alpha=0.3)
    ax3.set_xscale("log")
    ax3.set_yscale("log")
    plt.colorbar(scatter, ax=ax3, label="日收益率(%)")

    ax4 = axes[1, 0]
    ax4.plot(df_pepe["天数"], df_pepe["市值(百万美元)"], "purple", linewidth=2, alpha=0.8)
    ax4.fill_between(df_pepe["天数"], 0, df_pepe["市值(百万美元)"], alpha=0.2, color="purple")
    ax4.set_xlabel("天数")
    ax4.set_ylabel("市值(百万美元)")
    ax4.set_title("4. 市值变化")
    ax4.grid(True, alpha=0.3)
    ax4.set_yscale("log")

    max_mcap = df_pepe["市值(百万美元)"].max()
    min_mcap = df_pepe["市值(百万美元)"].min()
    final_mcap = df_pepe.loc[len(df_pepe) - 1, "市值(百万美元)"]
    ax4.text(
        0.05,
        0.95,
        f"最高: ${max_mcap:.1f}M\n最低: ${min_mcap:.1f}M\n最终: ${final_mcap:.1f}M",
        transform=ax4.transAxes,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    ax5 = axes[1, 1]
    ax5.plot(df_pepe["天数"], df_pepe["持有者数量"], "orange", linewidth=2)
    ax5.set_xlabel("天数")
    ax5.set_ylabel("持有者数量")
    ax5.set_title("5. 持有者数量增长")
    ax5.grid(True, alpha=0.3)

    ax6 = axes[1, 2]
    lags = 20
    autocorr = [df_pepe["价格(美元)"].autocorr(lag) for lag in range(lags)]
    ax6.bar(range(lags), autocorr, alpha=0.7, color="blue")
    ax6.axhline(y=0, color="r", linestyle="-", alpha=0.3)
    ax6.set_xlabel("滞后天数")
    ax6.set_ylabel("自相关系数")
    ax6.set_title("6. 价格自相关性 (随机游走检验)")
    ax6.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    plt.savefig(out_path, dpi=110)
    plt.close(fig)
    print("已保存:", out_path)


if __name__ == "__main__":
    df_pepe = simulate_pepe_fixed_supply(total_days=365, initial_price=0.000001)
    out = os.path.join(HERE, "pepe_market_simulation.png")
    plot(df_pepe, out)

    print("PEPE固定供应模型关键统计")
    print("=" * 50)
    print("总供应量: 420.69 万亿枚")
    print(f"初始价格: ${df_pepe.loc[0, '价格(美元)']:.10f}")
    print(f"最终价格: ${df_pepe.loc[len(df_pepe) - 1, '价格(美元)']:.10f}")
    chg = (df_pepe.loc[len(df_pepe) - 1, "价格(美元)"] / df_pepe.loc[0, "价格(美元)"] - 1) * 100
    print(f"价格变化: {chg:.2f}%")
    print(f"最高市值: ${df_pepe['市值(百万美元)'].max():.1f}M")
    print(f"最低市值: ${df_pepe['市值(百万美元)'].min():.1f}M")
    print(f"平均日波动率: {df_pepe['日收益率(%)'][1:].std():.2f}%")
    print(f"最大单日涨幅: {df_pepe['日收益率(%)'].max():.2f}%")
    print(f"最大单日跌幅: {df_pepe['日收益率(%)'].min():.2f}%")
