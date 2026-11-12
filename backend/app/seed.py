"""演示数据：首次启动时写入 8 位用户 / 14 篇帖子 / 12 条评论。

演示账号：linxiaoman / 123456（管理员），其余账号密码相同。
"""
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Comment, Post, PostLike, User
from .security import hash_password

DEMO_PASSWORD = "123456"

_now = datetime.utcnow()


def _ago(hours: int) -> datetime:
    return _now - timedelta(hours=hours)


USERS = [
    {
        "username": "linxiaoman", "nickname": "林小满", "avatar": "🌿", "color": "#6366f1",
        "major": "计算机科学与技术", "grade": "大三",
        "bio": "在准备 408 和数学一，喜欢用咖啡续命。周末常泡图书馆五楼，欢迎一起自习。",
        "tags": ["考研", "算法", "咖啡", "摄影"], "is_admin": True, "created_at": _ago(24 * 40),
    },
    {
        "username": "zhouyihang", "nickname": "周亦航", "avatar": "🎸", "color": "#ec4899",
        "major": "软件工程", "grade": "大二",
        "bio": "吉他社副社长，正在学前端。每周三晚在大学生活动中心排练，缺一个键盘手。",
        "tags": ["篮球", "吉他", "前端", "社团"], "created_at": _ago(24 * 36),
    },
    {
        "username": "suwanqing", "nickname": "苏晚晴", "avatar": "📖", "color": "#10b981",
        "major": "汉语言文学", "grade": "大一",
        "bio": "喜欢在旧书摊淘书，也写一点随笔。想找一起晨读、做志愿的朋友。",
        "tags": ["读书", "写作", "志愿服务", "摄影"], "created_at": _ago(24 * 30),
    },
    {
        "username": "chenmo", "nickname": "陈默", "avatar": "🔧", "color": "#f59e0b",
        "major": "电子信息工程", "grade": "研一",
        "bio": "实验室常驻，做嵌入式方向。晚上会去操场跑五公里，欢迎组队。",
        "tags": ["嵌入式", "跑步", "考研", "实验室"], "created_at": _ago(24 * 26),
    },
    {
        "username": "guxingye", "nickname": "顾星野", "avatar": "🎨", "color": "#8b5cf6",
        "major": "数字媒体艺术", "grade": "大三",
        "bio": "视觉设计在读，接一点校园约拍。喜欢有光的地方和安静的咖啡馆。",
        "tags": ["设计", "摄影", "咖啡", "插画"], "created_at": _ago(24 * 22),
    },
    {
        "username": "heyinuo", "nickname": "何一诺", "avatar": "🏸", "color": "#14b8a6",
        "major": "会计学", "grade": "大二",
        "bio": "羽毛球校队替补，最近在备考初级会计。周末会做一点小饼干分给室友。",
        "tags": ["羽毛球", "自习", "考研", "烘焙"], "created_at": _ago(24 * 18),
    },
    {
        "username": "shenzhiyao", "nickname": "沈知遥", "avatar": "🚴", "color": "#0ea5e9",
        "major": "英语", "grade": "大四",
        "bio": "翻译方向，正在准备 MTI。喜欢骑车绕城，也帮同学改简历和文书。",
        "tags": ["翻译", "读书", "骑行", "考研"], "created_at": _ago(24 * 14),
    },
    {
        "username": "jiangyuan", "nickname": "江予安", "avatar": "🎮", "color": "#ef4444",
        "major": "人工智能", "grade": "大二",
        "bio": "算法竞赛退役选手，现在做一点小游戏。想找队友打蓝桥杯和组队赛。",
        "tags": ["算法", "竞赛", "篮球", "游戏"], "created_at": _ago(24 * 10),
    },
]

POSTS = [
    (0, "study", "找一起冲 408 的研友，图书馆五楼长期自习",
     "目前复习到数据结构第二轮，想找一位节奏相近的研友互相监督。\n\n"
     "时间：周一到周五 18:30–22:00，周末全天。\n地点：图书馆五楼靠窗的位置。\n\n"
     "我可以分享整理好的笔记和真题分类，希望你能坚持打卡，不要三天打鱼两天晒网。",
     ["考研", "408", "自习"], 2, 186),
    (7, "study", "蓝桥杯组队，缺一个会写图论的队友",
     "今年报了蓝桥杯 Java B 组，目前两个人，一个写 DP 一个写数据结构，还差一个图论和搜索比较稳的同学。\n\n"
     "每周六下午在信息楼 402 集训，有往年题可以一起刷。目标省一，冲国赛。",
     ["竞赛", "蓝桥杯", "算法"], 5, 243),
    (1, "club", "吉他社秋季招新｜零基础也欢迎",
     "吉他社招新啦！本周四、周五 18:00 在大学生活动中心一楼摆摊。\n\n"
     "不需要会弹，我们有每周一次的免费教学课。社团有木吉他、电吉他、键盘和鼓，"
     "缺一个键盘手，会一点钢琴就行～\n\n欢迎来玩，现场有小型演出。",
     ["社团", "吉他", "招新"], 9, 512),
    (4, "market", "出二手显示器 24 寸 2K，九成新",
     "去年双十一买的 AOC 24 寸 2K 显示器，因为换了带鱼屏所以出掉。\n\n"
     "无坏点，无划痕，配件和原箱都在。原价 1099，现 520 出，可小刀。\n\n西区宿舍楼下自提，可以先看再决定。",
     ["二手", "显示器", "闲置"], 13, 328),
    (2, "lost", "在南门捡到一张校园卡，姓名是李**",
     "今天中午在南门快递驿站门口捡到一张校园卡，卡号后四位 3721，姓李。\n\n"
     "已经交到保卫处了，失主可以带学生证去行政楼 1 楼认领。\n\n如果认识这位同学，麻烦帮忙转告一下。",
     ["失物招领", "校园卡"], 20, 96),
    (5, "life", "二食堂新出的番茄牛腩饭值得一试",
     "二食堂二楼新开的窗口，番茄牛腩饭 16 块，牛腩给得挺多，汤泡饭很香。\n\n"
     "缺点是 12 点以后要排很久，建议 11:30 之前去。\n\n另外他们家的酸梅汤是免费续的，夏天很舒服。",
     ["食堂", "美食", "推荐"], 26, 671),
    (6, "study", "免费帮同学改英文简历 / 留学文书",
     "刚结束申请季，手上比较空。可以帮大家看看英文简历、个人陈述的语法和表达。\n\n"
     "不是代写，只做修改建议，一次 20 分钟左右。\n\n有需要的同学可以评论，我私信你约时间。",
     ["英语", "简历", "留学"], 30, 402),
    (3, "life", "晚上操场跑步搭子，配速 6 分左右",
     "最近在准备半马，一个人跑容易放弃。\n\n"
     "时间：每周二、四、日 20:30，操场东侧集合。配速 6:00–6:30，跑 5–8 公里。\n\n"
     "新手也可以来，我带你慢慢加量。",
     ["跑步", "运动", "搭子"], 34, 219),
    (7, "market", "求购一本《算法导论》第三版，中文版",
     "最好是中文版，有笔记也没关系，价格好商量。信息楼附近可以自取。",
     ["二手", "求购", "教材"], 40, 74),
    (0, "life", "图书馆五楼空调太冷了，有人有同感吗",
     "靠窗那排座位正对出风口，坐两个小时手都僵了。\n\n建议去自习的同学带件外套，或者选中间的位置。\n\n"
     "已经在小程序上给后勤提了建议，希望有用。",
     ["图书馆", "吐槽", "自习"], 46, 288),
    (2, "club", "周末去市图书馆做志愿者，还差 2 人",
     "本周六 9:00–16:00，市图书馆少儿区需要志愿者帮忙整理书籍、引导小朋友。\n\n"
     "有志愿工时，包午饭，地铁往返报销。\n\n感兴趣的评论集合～",
     ["志愿", "公益", "周末"], 52, 157),
    (4, "life", "校园约拍｜秋日光影计划",
     "最近在拍一组校园秋日人像，想找几位同学当模特。\n\n免费，成片精修 5 张，可以选风格。\n\n"
     "时间在周末下午，地点在老教学楼和梧桐道。",
     ["摄影", "约拍", "校园"], 58, 634),
    (5, "study", "求推荐安静的自习教室，晚上开放到 11 点",
     "图书馆闭馆太早，想找一个晚上能自习到 11 点的地方。\n\n最好能充电、有热水、人不太多。\n\n有推荐的同学吗？",
     ["自习", "教室", "推荐"], 66, 341),
    (1, "lost", "宿舍楼下有人掉了一把黑伞，放在门卫室了",
     "今天下午在 6 号宿舍楼下捡到一把黑色长柄伞，已经交给门卫大叔。失主去门卫室拿就好。",
     ["失物招领", "雨伞"], 72, 61),
]

COMMENTS = [
    (0, 5, "我我我！我也在图书馆五楼，晚上一般坐中间那排。", 1),
    (0, 3, "408 第二轮的话建议先刷真题，选择题比大题提分快。", 1),
    (1, 0, "图论的话我可以，不过我是 C++，跨语言可以吗？", 4),
    (2, 2, "键盘手是钢琴还是电子琴呀？我会一点钢琴。", 8),
    (2, 1, "都可以！周四来摊位聊～", 7),
    (3, 7, "还在吗？能小刀到 480 吗，今晚就能自提。", 11),
    (3, 4, "在的，480 可以，你几点过来？", 10),
    (5, 3, "昨天去吃了，牛腩确实多，但有点咸。", 24),
    (6, 0, "太需要了！我的 CV 一直感觉怪怪的，求指点。", 28),
    (11, 2, "报名！想拍一组在梧桐道的。", 56),
    (12, 6, "信息楼 402 晚上开放到 11 点，有插座，人也不多。", 64),
    (7, 5, "六分半配速可以跟上吗？我刚开始跑。", 33),
]

LIKES = {
    0: [3, 5, 6], 1: [0, 3, 4, 5], 2: [2, 4, 5, 6, 7], 3: [7], 4: [0, 1],
    5: [0, 3, 6, 7], 6: [0, 2, 4], 7: [0, 5], 8: [], 9: [2, 5],
    10: [1, 2], 11: [0, 1, 2, 5, 6], 12: [0, 5], 13: [],
}


def seed_if_empty(db: Session) -> bool:
    """数据库为空时写入演示数据，返回是否写入。"""
    count = db.scalar(select(func.count()).select_from(User)) or 0
    if count > 0:
        return False

    users: list[User] = []
    for item in USERS:
        user = User(
            username=item["username"],
            password_hash=hash_password(DEMO_PASSWORD),
            nickname=item["nickname"],
            avatar=item["avatar"],
            color=item["color"],
            major=item["major"],
            grade=item["grade"],
            bio=item["bio"],
            tags=item["tags"],
            is_admin=item.get("is_admin", False),
            created_at=item["created_at"],
        )
        db.add(user)
        users.append(user)
    db.flush()

    posts: list[Post] = []
    for author_index, category, title, content, tags, hours, views in POSTS:
        post = Post(
            author_id=users[author_index].id,
            category=category,
            title=title,
            content=content,
            tags=tags,
            views=views,
            created_at=_ago(hours),
        )
        db.add(post)
        posts.append(post)
    db.flush()

    for post_index, author_index, content, hours in COMMENTS:
        db.add(
            Comment(
                post_id=posts[post_index].id,
                author_id=users[author_index].id,
                content=content,
                created_at=_ago(hours),
            )
        )

    for post_index, user_indexes in LIKES.items():
        for user_index in user_indexes:
            db.add(PostLike(post_id=posts[post_index].id, user_id=users[user_index].id))

    db.commit()
    return True
