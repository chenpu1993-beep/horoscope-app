import os
import requests
import json
from datetime import datetime
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv
from datetime import datetime, date
import json
import os

# 限制配置文件
RATE_LIMIT_FILE = "rate_limits.json"  # 存储用户调用次数的文件
DAILY_LIMIT = 3  # 每人每天免费次数

def load_rate_limits():
    """从文件加载调用次数记录"""
    if os.path.exists(RATE_LIMIT_FILE):
        with open(RATE_LIMIT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_rate_limits(limits):
    """保存调用次数记录到文件"""
    with open(RATE_LIMIT_FILE, 'w', encoding='utf-8') as f:
        json.dump(limits, f, ensure_ascii=False, indent=2)

# 获取用户标识（简单方案：用IP地址）
def get_user_id():
    """获取用户唯一标识，这里用IP + User-Agent做简单识别"""
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'unknown')[:20]
    return f"{ip}_{user_agent}"
# 加载 .env 文件
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# ============ 配置 ============
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

if not DEEPSEEK_API_KEY:
    print("⚠️ 警告: 请设置 DEEPSEEK_API_KEY 环境变量")


# ============ 星座判断 ============
def get_zodiac_sign(month, day):
    if (month == 1 and day >= 20) or (month == 2 and day <= 18):
        return "水瓶座"
    elif (month == 2 and day >= 19) or (month == 3 and day <= 20):
        return "双鱼座"
    elif (month == 3 and day >= 21) or (month == 4 and day <= 20):
        return "白羊座"
    elif (month == 4 and day >= 21) or (month == 5 and day <= 20):
        return "金牛座"
    elif (month == 5 and day >= 21) or (month == 6 and day <= 21):
        return "双子座"
    elif (month == 6 and day >= 22) or (month == 7 and day <= 22):
        return "巨蟹座"
    elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
        return "狮子座"
    elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
        return "处女座"
    elif (month == 9 and day >= 23) or (month == 10 and day <= 23):
        return "天秤座"
    elif (month == 10 and day >= 24) or (month == 11 and day <= 22):
        return "天蝎座"
    elif (month == 11 and day >= 23) or (month == 12 and day <= 21):
        return "射手座"
    else:
        return "摩羯座"


# ============ AI 生成运势 ============
def generate_horoscope(zodiac_sign, date_str, birth_date):
    """调用 DeepSeek API 生成运势（根据年龄调整内容）"""

    if not DEEPSEEK_API_KEY:
        return "⚠️ 请先设置 DeepSeek API Key"

    # ===== 计算年龄 =====
    today = datetime.now().date()
    age = today.year - birth_date.year
    # 如果还没过生日，年龄减1
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    # ===== 根据年龄选择不同的提示词 =====
    if age <= 6:
        age_prompt = f"""
        用户是一位{age}岁的小朋友，请用童趣、可爱的语气，为ta写一份今日“小星星指引”。
        内容要简单易懂，可以包含：
        1. 今天适合玩什么类型的游戏
        2. 和小朋友相处的小建议
        3. 今天可以学习什么新东西
        4. 一句鼓励的话
        不要出现“爱情”“事业”“财运”等成人话题。
        总字数控制在150字以内。
        """
    elif age <= 12:
        age_prompt = f"""
        用户是一位{age}岁的小学生，请用活泼、鼓励的语气，为ta写一份今日“成长小贴士”。
        内容可以包含：
        1. 今天的学习小建议
        2. 和朋友相处的小提醒
        3. 今天可以尝试的新事物
        4. 一句鼓励的话
        不要出现“爱情”“事业”“财运”等成人话题。
        总字数控制在150字以内。
        """
    elif age <= 18:
        age_prompt = f"""
        用户是一位{age}岁的青少年，请用温暖、朋友般的语气，为ta写一份今日“青春指引”。
        内容可以包含：
        1. 学业或兴趣上的小建议
        2. 人际关系（友情/亲情）的小提醒
        3. 情绪调节的小方法
        4. 一句鼓励的话
        适当关注成长和未来方向。
        总字数控制在200字以内。
        """
    else:
        age_prompt = f"""
        用户是一位成年人，请为{date_str}的{zodiac_sign}写一份当日运势指南。
        内容包含：
        1. 整体运势（1-5星）
        2. 爱情
        3. 事业
        4. 财运
        5. 健康
        6. 今日幸运色和幸运数字
        语言温暖、积极，像朋友在聊天。
        总字数控制在250字以内。
        """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    prompt = f"""
    你是一位温暖、专业的星座占星师。
    {age_prompt}
    注意：这是{date_str}的运势，不要提及这是AI生成的。
    直接输出运势内容，不要加标题。
    """

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位温暖、专业的星座占星师，擅长根据用户的年龄调整语气和内容。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 600
    }

    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return content
    except requests.exceptions.Timeout:
        return "⏰ 星星们有些害羞，响应超时了，请稍后再试～"
    except requests.exceptions.RequestException as e:
        return f"🌙 连接星星的通道暂时不太稳定，请稍后再试。\n（技术小贴士：{str(e)}）"
    except Exception as e:
        return f"✨ 今天星星们放假了，请稍后再来～"


# ============ 路由 ============
@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/horoscope', methods=['POST'])
def horoscope_api():
    """运势生成 API（含每日次数限制）"""

    # ===== 新增：次数限制检查 =====
    user_id = get_user_id()
    limits = load_rate_limits()
    today_str = date.today().isoformat()

    # 初始化或重置用户记录
    if user_id not in limits:
        limits[user_id] = {"date": today_str, "count": 0}
    elif limits[user_id]["date"] != today_str:
        # 新的一天，重置次数
        limits[user_id] = {"date": today_str, "count": 0}

    # 检查是否达到限制
    if limits[user_id]["count"] >= DAILY_LIMIT:
        return jsonify({
            'error': f'今日免费次数已用完（每天 {DAILY_LIMIT} 次），请明天再来～',
            'limit_reached': True
        }), 429  # 429 表示 Too Many Requests

    # ===== 原有代码开始 =====
    data = request.get_json()
    birth_date_str = data.get('birth_date', '').strip()

    if not birth_date_str:
        return jsonify({'error': '请输入出生日期'}), 400

    try:
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')
        month, day = birth_date.month, birth_date.day
    except ValueError:
        return jsonify({'error': '日期格式错误，请使用 YYYY-MM-DD 格式'}), 400

    zodiac = get_zodiac_sign(month, day)
    today = datetime.now().strftime('%Y年%m月%d日')

    # 调用 AI
    horoscope_text = generate_horoscope(zodiac, today, birth_date)

    # ===== 新增：调用成功后更新计数 =====
    limits[user_id]["count"] += 1
    save_rate_limits(limits)

    return jsonify({
        'zodiac': zodiac,
        'date': today,
        'horoscope': horoscope_text,
        'timestamp': datetime.now().isoformat(),
        'remaining': DAILY_LIMIT - limits[user_id]["count"]  # 返回剩余次数
    })


@app.route('/api/tarot', methods=['POST'])
def tarot_api():
    """塔罗抽牌（彩蛋功能）"""
    data = request.get_json()
    question = data.get('question', '你最近的状态如何？')

    if not DEEPSEEK_API_KEY:
        return jsonify({'error': '请先设置 DeepSeek API Key'}), 500

    # 塔罗牌列表
    tarot_cards = [
        "愚者", "魔术师", "女祭司", "女皇", "皇帝", "教皇", "恋人", "战车",
        "力量", "隐士", "命运之轮", "正义", "倒吊人", "死神", "节制", "恶魔",
        "高塔", "星星", "月亮", "太阳", "审判", "世界"
    ]

    import random
    card = random.choice(tarot_cards)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    prompt = f"""
    你是一位经验丰富的塔罗解读师。用户抽到了「{card}」这张牌。
    用户的问题是：「{question}」

    请为这张牌写一段温柔的解读（150字左右），包含：
    1. 这张牌的核心含义
    2. 针对用户问题的具体指引
    3. 一句鼓励的话

    语言温暖、有共鸣，不要说这是AI生成的。
    """

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是温柔专业的塔罗解读师，你的解读给人力量和安慰。"},
            {"role": "user", "content": prompt}  # ← 补上 "role": "user"
        ],
        "temperature": 0.9,
        "max_tokens": 400
    }

    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return jsonify({
            'card': card,
            'interpretation': result["choices"][0]["message"]["content"]
        })
    except Exception as e:
        return jsonify({'error': f'抽牌失败，请稍后再试：{str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)