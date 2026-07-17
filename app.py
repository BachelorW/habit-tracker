from pyngrok import ngrok, conf
import getpass
import sys

# 你的 ngrok authtoken（把下面的 YOUR_TOKEN 换成你刚才在 ngrok 网页复制的那一串）
conf.get_default().authtoken = "3FrEDIUWFbmyUPcnmATwTULYivG_4u62HwPLE7CxP9AaRT4yu"

# 建立隧道，把本地8501端口变成公网网址
try:
    public_url = ngrok.connect(8501, "http")
    print(f"\n✅ 手机访问链接：{public_url}\n")
except Exception as e:
    print(f"ngrok 启动失败：{e}")
    print("请在手机使用局域网地址或检查 Token。")
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date, timedelta
import random
import os
import requests
import json
from streamlit.components.v1 import html

# ======================== 页面设置 ========================
st.set_page_config(page_title="🌱 习惯圆环 Pro", page_icon="🌱", layout="wide")

# ======================== 数据路径 ========================
DATA_FILE = "data/habit_log.csv"
os.makedirs("data", exist_ok=True)

# ======================== 本地备用语录 ========================
FALLBACK_QUOTES = [
    "行动催化动力，先做5分钟再说。",
    "忙碌不等于产出，专注才是。",
    "如果某个环节崩了，没关系，保持“非零和”，明天是新的循环。",
    "今天你吃掉的那只青蛙，是明天自由的翅膀。",
    "你不是在坚持习惯，你是在塑造身份。",
    "每一个微小的完成，都在对明天的你说：交给我吧。",
    "流水不争先，争的是滔滔不绝。",
    "别让完美主义吃掉行动力，先完成再完美。",
]

# ======================== 习惯定义 ========================
HABITS = [
    "⏰ 8:30 起床｜不刷手机，喝水",
    "🥚 早餐｜优质蛋白，拒绝糖油",
    "📐 上午深度学习｜先吃最难的青蛙",
    "🏀 运动时光｜篮球/健身/跑步",
    "🗣️ 弹性时间｜口语/社交/补漏",
    "🛌 24:00 睡觉｜放下手机",
]

# ======================== 加载 / 初始化数据 ========================
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        return df
    else:
        return pd.DataFrame(columns=["date"] + HABITS + ["note"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()
today = date.today()

# 确保今日行存在
if df.empty or not (df["date"] == today).any():
    new_row = {"date": today}
    for h in HABITS:
        new_row[h] = False
    new_row["note"] = ""
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)

# 获取今日数据
today_row = df[df["date"] == today].iloc[0]
today_habits = today_row[HABITS].to_dict()
today_note = today_row.get("note", "")

# ======================== 深色模式 & 动态背景 ========================
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# 根据时间生成背景渐变
hour = datetime.now().hour
if 6 <= hour < 12:
    bg_gradient = "linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%)"   # 晨
elif 12 <= hour < 18:
    bg_gradient = "linear-gradient(135deg, #ffffff 0%, #f1f1f1 100%)"   # 午
else:
    bg_gradient = "linear-gradient(135deg, #2b2b2b 0%, #1a1a2e 100%)"   # 夜

# 根据主题覆盖背景
if st.session_state.theme == "dark":
    bg_style = "background: #0e1117; color: #e0e0e0;"
    card_bg = "#1e1e1e"
    text_color = "#e0e0e0"
else:
    bg_style = f"background: {bg_gradient}; color: #333;"
    card_bg = "white"
    text_color = "#333"

st.markdown(f"""
<style>
    .stApp {{
        {bg_style}
        transition: background 0.5s ease;
    }}
    .css-1d391kg, .css-1wrcr7z, .stTextInput>div>div>input, .stTextArea textarea {{
        background-color: {card_bg};
        color: {text_color};
    }}
    .stButton>button {{
        background-color: #4CAF50;
        color: white;
        border-radius: 12px;
        padding: 0.5em 1.5em;
    }}
    .habit-done {{
        background-color: #4CAF50 !important;
    }}
</style>
""", unsafe_allow_html=True)

# ======================== 侧边栏：主题切换与天气 ========================
with st.sidebar:
    st.markdown("## ⚙️ 控制台")
    theme_toggle = st.toggle("🌙 暗夜模式", value=(st.session_state.theme == "dark"))
    st.session_state.theme = "dark" if theme_toggle else "light"

    st.markdown("---")
    st.markdown("### 🌤️ 今日天气")
    city = "Beijing"
    try:
        weather_url = f"https://wttr.in/{city}?format=%C+%t+%w&lang=zh"
        resp = requests.get(weather_url, timeout=5)
        if resp.status_code == 200:
            weather_info = resp.text.strip()
            st.success(f"**{weather_info}**")
            # 简单运动建议
            if "雨" in weather_info or "雪" in weather_info:
                st.info("💡 今天适合室内运动（瑜伽/拉伸）")
            elif "晴" in weather_info or "云" in weather_info:
                st.info("☀️ 天气不错，鼓励户外跑步/篮球！")
        else:
            st.warning("天气暂不可用")
    except:
        st.warning("天气加载失败")

# ======================== 每日双金句 ========================
@st.cache_data(ttl=3600, show_spinner=False)
def get_hitokoto(category=None):
    try:
        url = "https://v1.hitokoto.cn/"
        params = {"c": category} if category else {}
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get("hitokoto", ""), data.get("from", "")
    except:
        pass
    return "", ""

quote1, from1 = get_hitokoto()  # 随机
# 第二个金句特意从诗词或哲学中取
quote2, from2 = get_hitokoto(category=random.choice(["i", "k"]))
if not quote2:
    quote2, from2 = get_hitokoto(category="d")  # 文学兜底

main_quote = quote1 if quote1 else random.choice(FALLBACK_QUOTES)
sub_quote = quote2 if quote2 else ""

# 根据完成情况加前缀
completed_today = sum(today_habits.values())
if completed_today >= 4:
    prefix = "🏆 "
elif completed_today >= 1:
    prefix = "🚀 "
else:
    prefix = "🌅 "

st.markdown(f"## {prefix}{main_quote}")
if sub_quote:
    st.markdown(f"*“{sub_quote}”*  —— {from2 if from2 else '佚名'}")

# ======================== 连续打卡天数计算 ========================
def calc_streak(df, habit):
    """返回今日之前的连续打卡天数（今日未算）"""
    if df.empty:
        return 0
    df_sorted = df.sort_values("date", ascending=False)
    streak = 0
    check_date = today - timedelta(days=1)
    for _, row in df_sorted.iterrows():
        if row["date"] == check_date and row[habit] == True:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    return streak

streaks = {h: calc_streak(df, h) for h in HABITS}

# 惩罚提醒：连续3天未完成某习惯（含今日未完成）
for h in HABITS:
    if not today_habits[h] and calc_streak(df, h) == 0 and calc_streak(df, h) == 0:  # 简化：检查前三天
        # 更严谨：检查前三天是否都未完成
        past_3 = [today - timedelta(days=i) for i in range(1,4)]
        all_missed = True
        for d in past_3:
            row = df[df["date"] == d]
            if not row.empty and row.iloc[0][h] == True:
                all_missed = False
                break
        if all_missed:
            st.warning(f"⚡ {h.split('｜')[0]} 已经连续3天未完成！今天就是重启连胜的最好时机。")

# ======================== 今日打卡区 ========================
st.subheader("📋 今日习惯打卡")
st.caption("点击开关完成打卡，数据自动保存")

cols_form = st.columns(2)
updated_habits = {}
with st.form("habit_form"):
    for i, habit in enumerate(HABITS):
        with cols_form[i % 2]:
            current_val = today_habits[habit]
            updated_habits[habit] = st.toggle(
                f"{habit}   🔥{streaks[habit]}天", value=current_val, key=f"habit_{i}"
            )
    submitted = st.form_submit_button("✅ 保存今日打卡")

if submitted:
    for h in HABITS:
        df.loc[df["date"] == today, h] = updated_habits[h]
    save_data(df)
    # 触发彩带效果
    confetti_html = """
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1"></script>
    <script>
    confetti({ particleCount: 150, spread: 70, origin: { y: 0.6 } });
    </script>
    """
    html(confetti_html, height=0)
    st.success("🎉 打卡成功！彩带为你而飘")
    st.rerun()

# ======================== 今日复盘 ========================
with st.expander("📝 今日复盘备忘录"):
    new_note = st.text_area("今天学到的事 / 想感谢的人 / 闪念", value=today_note, key="note_input")
    if st.button("保存备忘录"):
        df.loc[df["date"] == today, "note"] = new_note
        save_data(df)
        st.success("备忘录已保存")

# ======================== 当月圆环 + 热力图 ========================
st.subheader("📊 本月全景")
st.caption("圆环 = 完成率   |   热力图 = 每天完成情况")

df["date"] = pd.to_datetime(df["date"]).dt.date
current_month = today.month
current_year = today.year
month_df = df[(df["date"].apply(lambda d: d.month) == current_month) &
              (df["date"].apply(lambda d: d.year) == current_year)]

if not month_df.empty:
    # 准备本月所有日期
    first_day = date(current_year, current_month, 1)
    last_day = date(current_year, current_month + 1, 1) - timedelta(days=1) if current_month < 12 else date(current_year, 12, 31)
    all_dates = pd.date_range(first_day, last_day).date
    
    # 每个习惯一行：圆环 + 热力图
    for habit in HABITS:
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            # 圆环
            completed = month_df[habit].sum()
            possible_days = len(month_df)
            rate = completed / possible_days if possible_days > 0 else 0
            fig_pie = go.Figure(go.Pie(
                labels=["完成", "未完成"],
                values=[rate, 1-rate],
                hole=0.7,
                marker=dict(colors=["#4CAF50", "#E0E0E0"]),
                textinfo='none',
                hoverinfo='label+percent',
                showlegend=False
            ))
            fig_pie.update_layout(
                title=f"{habit.split('｜')[0]}  {rate*100:.0f}%",
                title_font_size=14,
                annotations=[dict(text=f"{rate*100:.0f}%", x=0.5, y=0.5, font_size=16, showarrow=False)],
                height=150,
                margin=dict(t=30, b=10)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            st.markdown(f"**连🔥 {streaks[habit]} 天**")
        with col3:
            # 热力图：显示本月每天完成情况（绿色/灰色）
            heat_data = []
            for d in all_dates:
                if d <= today:  # 只显示已过去的日子
                    row = month_df[month_df["date"] == d]
                    val = 1 if not row.empty and row.iloc[0][habit] else 0
                else:
                    val = -1  # 未来的日子不显示
                heat_data.append(val if val != -1 else -1)
            
            fig_heat = go.Figure(go.Heatmap(
                z=[heat_data],
                x=[d.day for d in all_dates],
                y=[habit.split('｜')[0][:6]],
                colorscale=[[0, '#E0E0E0'], [1, '#4CAF50']],
                showscale=False,
                zmin=0, zmax=1,
                xgap=2,
                ygap=2
            ))
            fig_heat.update_layout(
                height=80,
                margin=dict(t=0, b=0, l=0, r=0),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
            st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("本月暂无数据，开始打卡吧！")

# ======================== 月度成就总结 ========================
if not month_df.empty and today.day > 5:  # 月初几天不显示
    total_checks = month_df[HABITS].sum().sum()
    days_with_data = len(month_df)
    avg_rate = (month_df[HABITS].sum() / days_with_data).mean() * 100
    st.success(f"🏅 本月已坚持 **{total_checks}** 次习惯，平均完成率 **{avg_rate:.1f}%**。继续加油！")

# ======================== 历史数据下载 ========================
with st.expander("📅 查看/下载历史数据"):
    st.dataframe(df.sort_values("date", ascending=False).reset_index(drop=True))
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 下载完整数据 CSV", csv, "habit_log.csv", "text/csv")
