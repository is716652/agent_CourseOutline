import re
import json
from typing import List, Dict, Any
from loguru import logger

try:
    import requests  # 用于在线大模型接口
except Exception:
    requests = None  # 离线模式或未安装requests时回退


def _to_int(text: str, default: int | None = None) -> int | None:
    if text is None:
        return default
    m = re.search(r"\d+", str(text))
    if not m:
        return default
    try:
        return int(m.group())
    except Exception:
        return default


def _split_list(text: str) -> List[str]:
    if not text:
        return []
    items = [x.strip() for x in str(text).replace("\r", "").replace("\n", ",").split(",")]
    return [x for x in items if x]


def _gen_objectives(course_name: str, focus_points: str, exclude_points: str) -> str:
    focuses = _split_list(focus_points)
    bullets = [
        f"理解{course_name}的核心概念与应用场景",
        "掌握典型问题的建模思路与实现流程",
        "具备查阅资料、复现案例与迭代优化的能力",
    ]
    if focuses:
        bullets.insert(1, f"围绕重点专题：{'、'.join(focuses)}，形成系统化理解")
    if exclude_points:
        bullets.append(f"不展开/排除：{exclude_points}")
    return "\n".join([f"- {b}" for b in bullets])


def _gen_contents(course_name: str, focus_points: str) -> str:
    focuses = _split_list(focus_points)
    modules = [
        "课程导论与学习路径",
        "基础概念与工具准备",
        "核心技术与关键方法",
    ]
    # 将重点项作为独立模块插入
    for fp in focuses:
        modules.append(f"重点专题：{fp}")
    modules += [
        "模型评估与调优",
        "工程化与团队协作",
        "综合项目与报告撰写",
    ]
    return "\n".join([f"- {m}" for m in modules])


def _gen_teaching_methods() -> str:
    methods = [
        "讲授 + 板书/白板推演",
        "代码演示与分步实验",
        "课堂小测与即时反馈",
        "分组讨论与汇报",
        "阶段作业与项目驱动学习",
    ]
    return "\n".join([f"- {m}" for m in methods])


def _detail_for_module(module: str) -> List[str]:
    # 讲授要点（列表）
    if "重点专题" in module:
        topic = module.split("：", 1)[-1]
        return ["原理与框架", "典型模型与结构", f"{topic}案例实战"]
    if "导论" in module:
        return ["课程目标", "环境与工具", "案例全景"]
    if "基础" in module or "概念" in module:
        return ["关键概念", "数据与特征", "评估指标"]
    if "核心方法" in module:
        return ["算法原理", "超参数", "适用场景"]
    if "评估" in module or "调优" in module:
        return ["误差分析", "调参流程", "对比实验"]
    if "工程化" in module:
        return ["代码规范", "版本管理", "协作流程"]
    if "综合项目" in module:
        return ["题目解析", "任务分解", "里程碑与验收"]
    if "部署" in module:
        return ["导出与推理", "接口与服务", "监控与回滚"]
    if "汇报" in module or "选题" in module:
        return ["选题建议", "调研报告", "展示要点"]
    return ["知识点讲解", "示例拆解", "注意事项"]


essential_practice_default = ["课堂实验/练习"]


def _practice_for_module(module: str) -> List[str]:
    # 实验/实践（列表）
    if "重点专题" in module:
        topic = module.split("：", 1)[-1]
        return [f"实现{topic}基础流程", "完成训练与验证"]
    if "导论" in module:
        return ["环境搭建", "第一个Hello World"]
    if "基础" in module or "概念" in module:
        return ["数据读取/预处理", "可视化"]
    if "核心方法" in module:
        return ["基线模型训练", "效果对比"]
    if "评估" in module or "调优" in module:
        return ["调参实验", "误差分析"]
    if "工程化" in module:
        return ["项目结构化", "单元测试"]
    if "综合项目" in module:
        return ["项目关键模块实现"]
    if "部署" in module:
        return ["导出模型", "构建推理服务"]
    return essential_practice_default


def _homework_for_module(module: str) -> List[str]:
    # 作业（列表）
    if "重点专题" in module:
        topic = module.split("：", 1)[-1]
        return [f"撰写{topic}学习小结", "整理关键超参数"]
    if "导论" in module:
        return ["安装环境并提交截图"]
    if "基础" in module or "概念" in module:
        return ["完成数据处理脚本并说明"]
    if "核心方法" in module:
        return ["对比两种方法的效果并报告"]
    if "评估" in module or "调优" in module:
        return ["提交调参日志", "对比表"]
    if "工程化" in module:
        return ["整理代码规范检查清单"]
    if "综合项目" in module:
        return ["提交阶段报告", "下一步计划"]
    if "部署" in module:
        return ["部署方案设计", "风控说明"]
    return ["阅读/小测/代码补全"]


def _gen_schedule(course_name: str, total_hours: int | None, num_weeks: int,
                   focus_points: str, exclude_points: str) -> List[Dict[str, Any]]:
    # 内容周 = 总周数 - 1，最后一周固定复习与答疑
    weeks = max(2, int(num_weeks or 18))
    content_weeks = weeks - 1

    # 估算每周学时
    if total_hours and total_hours > 0:
        avg = max(2, round(total_hours / weeks))
    else:
        avg = 4

    focuses = _split_list(focus_points)

    # 重点项自动分配策略：优先覆盖第3~8周（若周数不足，覆盖到内容周末尾）
    prefer_start = 3
    prefer_end = min(8, content_weeks)

    modules: List[str] = []
    # 固定前两周
    modules.append("课程导论、环境与工具")
    if content_weeks >= 2:
        modules.append("基础概念与数据预处理")

    placed_core = False
    tail_pool = [
        "核心方法概览",
        "模型评估与调优",
        "工程化与团队协作",
        "综合项目实践 I",
        "综合项目实践 II",
        "部署与测试",
        "阶段汇报与反馈",
    ]

    # 在优先周间段尽量放置重点专题
    focus_idx = 0
    current_week = len(modules) + 1
    while current_week <= prefer_end and len(modules) < content_weeks:
        if current_week < prefer_start:
            # 填充到第3周前的空位（极少出现）
            if tail_pool:
                mod = tail_pool.pop(0)
                if mod == "核心方法概览":
                    placed_core = True
                modules.append(mod)
            else:
                modules.append(f"专题学习 {current_week}")
        else:
            if focus_idx < len(focuses):
                modules.append(f"重点专题：{focuses[focus_idx]}")
                focus_idx += 1
            elif not placed_core:
                modules.append("核心方法概览")
                placed_core = True
            elif tail_pool:
                modules.append(tail_pool.pop(0))
            else:
                modules.append(f"专题学习 {current_week}")
        current_week += 1

    # 剩余周：先放未用完的重点专题，其次尾部模块，最后占位专题
    while len(modules) < content_weeks and focus_idx < len(focuses):
        modules.append(f"重点专题：{focuses[focus_idx]}")
        focus_idx += 1
    while len(modules) < content_weeks and tail_pool:
        mod = tail_pool.pop(0)
        if mod == "核心方法概览" and placed_core:
            continue
        if mod == "核心方法概览":
            placed_core = True
        modules.append(mod)
    idx = 1
    while len(modules) < content_weeks:
        modules.append(f"专题学习 {idx}")
        idx += 1

    rows: List[Dict[str, Any]] = []
    for i in range(1, content_weeks + 1):
        module = modules[i - 1]
        detail = _detail_for_module(module)
        practice = _practice_for_module(module)
        homework = _homework_for_module(module)
        rows.append({
            "周次": i,
            "教学内容": module,
            "学时": avg,
            "讲授": detail,
            "实验/实践": practice,
            "作业": homework,
        })

    # 最后一周固定复习与答疑
    rows.append({
        "周次": weeks,
        "教学内容": "复习与答疑",
        "学时": avg,
        "讲授": ["整体回顾", "错题分析", "易混淆点梳理"],
        "实验/实践": ["综合练习", "模拟测试"],
        "作业": ["期末复习", "项目收尾"],
    })
    return rows


def generate_syllabus_content(
    course_name: str,
    course_code: str | None = None,
    credit: str | None = None,
    hours: str | None = None,
    prerequisites_text: str | None = None,
    num_weeks: int = 18,
    focus_points: str = "",
    exclude_points: str = "",
    # 新增：LLM 配置（可选）
    llm_provider: str | None = None,
    llm_api_key: str | None = None,
    llm_model: str | None = None,
) -> Dict[str, Any]:
    """
    生成教学大纲中由 AI 填充的字段。
    - 当提供 llm_provider + llm_api_key + llm_model 时，优先走在线 LLM；否则使用离线启发式生成。
    返回 keys：objectives, contents, teaching_methods, schedule_table
    """
    total_hours = _to_int(hours, None)

    # 优先尝试在线 LLM
    if llm_provider and llm_api_key and llm_model and requests is not None:
        try:
            llm_result = _gen_with_llm(
                provider=llm_provider,
                api_key=llm_api_key,
                model=llm_model,
                course_name=course_name or "本课程",
                num_weeks=int(num_weeks or 18),
                total_hours=total_hours,
                focus_points=focus_points or "",
                exclude_points=exclude_points or "",
            )
            if llm_result:
                logger.info("LLM生成内容完成(provider={})", llm_provider)
                return llm_result
        except Exception as e:
            logger.error("LLM 生成失败，回退离线：{}", str(e))

    # 离线启发式
    objectives = _gen_objectives(course_name or "本课程", focus_points, exclude_points)
    contents = _gen_contents(course_name or "本课程", focus_points)
    teaching_methods = _gen_teaching_methods()
    schedule_table = _gen_schedule(course_name or "本课程", total_hours, int(num_weeks or 18), focus_points, exclude_points)

    result = {
        "objectives": objectives,
        "contents": contents,
        "teaching_methods": teaching_methods,
        "schedule_table": schedule_table,
    }

    logger.info("AI生成内容完成(offline mode)，weeks={} (含最后一周复习)，hours={}", int(num_weeks or 18), total_hours)
    return result


def _gen_with_llm(provider: str, api_key: str, model: str, course_name: str, num_weeks: int, total_hours: int | None, focus_points: str, exclude_points: str) -> Dict[str, Any] | None:
    """使用在线大模型生成：目前支持 provider in {openai, deepseek}，统一走 Chat Completions 风格接口。
    预期返回与离线版本一致的数据结构。
    """
    provider = (provider or '').lower()
    if provider not in ("openai", "deepseek"):
        raise ValueError("Unsupported provider: " + provider)

    # 目标端点
    if provider == 'openai':
        base_url = 'https://api.openai.com/v1/chat/completions'
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    else:  # deepseek
        base_url = 'https://api.deepseek.com/chat/completions'
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # 统一提示词，要求JSON输出
    sys_prompt = (
        "你是一名教务专家，请根据课程信息生成教学大纲的四个部分：\n"
        "1) 课程目标（要点列表或分条文本）；\n"
        "2) 课程内容（模块清单，以列表/分条文本）；\n"
        "3) 教学方法（分条文本）；\n"
        "4) 教学进度安排（表格数组，字段：周次、教学内容、学时、讲授、实验/实践、作业；其中'讲授/实验/实践/作业'应为列表）。\n"
        "注意：总周数=输入周数；最后一周固定为复习与答疑；前(总周数-1)周为教学内容。\n"
        "仅返回JSON对象，键必须为 objectives, contents, teaching_methods, schedule_table。\n"
        "schedule_table 为长度=周数的数组；最后一行是复习与答疑；其他行根据重点项优先分配到第3~8周。"
    )

    user_prompt = {
        "course_name": course_name,
        "num_weeks": num_weeks,
        "total_hours": total_hours,
        "focus_points": focus_points,
        "exclude_points": exclude_points,
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)}
        ],
        "temperature": 0.3,
    }

    resp = requests.post(base_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # 解析 choices[0].message.content
    content = None
    try:
        content = data.get('choices', [{}])[0].get('message', {}).get('content')
    except Exception:
        content = None

    if not content:
        # deepseek 可能也有相同字段结构；若没有，直接回退
        return None

    # 期望content是JSON字符串
    try:
        obj = json.loads(content)
    except Exception:
        # 尝试从 Markdown 代码块中提取
        import re as _re
        m = _re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if m:
            try:
                obj = json.loads(m.group(1))
            except Exception:
                return None
        else:
            return None

    # 规范化 schedule_table：确保每行列表字段为数组
    rows = obj.get('schedule_table') or []
    norm_rows: List[Dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        r = {
            '周次': row.get('周次') or (i + 1),
            '教学内容': row.get('教学内容') or '',
            '学时': row.get('学时') or 4,
            '讲授': row.get('讲授') if isinstance(row.get('讲授'), list) else [],
            '实验/实践': row.get('实验/实践') if isinstance(row.get('实验/实践'), list) else [],
            '作业': row.get('作业') if isinstance(row.get('作业'), list) else [],
        }
        norm_rows.append(r)

    # 保底：长度修正与末周追加
    if not norm_rows or len(norm_rows) < num_weeks:
        # 以离线策略补齐
        if len(norm_rows) == 0:
            norm_rows = _gen_schedule(course_name, total_hours, num_weeks, focus_points, exclude_points)
        else:
            # 截断为 num_weeks-1 并确保最后一周为复习与答疑
            norm_rows = norm_rows[: max(0, num_weeks - 1)]
            norm_rows.append({
                '周次': num_weeks,
                '教学内容': '复习与答疑',
                '学时': 4,
                '讲授': ['整体回顾', '错题分析', '易混淆点梳理'],
                '实验/实践': ['综合练习', '模拟测试'],
                '作业': ['期末复习', '项目收尾'],
            })
    else:
        # 截断为 num_weeks
        norm_rows = norm_rows[:num_weeks]

    result = {
        'objectives': obj.get('objectives') or _gen_objectives(course_name, focus_points, exclude_points),
        'contents': obj.get('contents') or _gen_contents(course_name, focus_points),
        'teaching_methods': obj.get('teaching_methods') or _gen_teaching_methods(),
        'schedule_table': norm_rows if norm_rows else _gen_schedule(course_name, total_hours, num_weeks, focus_points, exclude_points)
    }
    return result