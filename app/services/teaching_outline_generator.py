#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
教学大纲生成器
使用AI自动生成教学大纲的各个部分
"""

import json
import requests
from datetime import datetime
from loguru import logger


def generate_teaching_outline(course_name, write_date=None, assessment_method=None, 
                            exclude_items=None, system_prompt=None, user_prompt=None,
                            llm_provider=None, llm_api_key=None, llm_model=None,
                            positioning_length=100, objectives_length=80, module_content_length=60):
    """
    生成完整的教学大纲内容
    
    Args:
        course_name: 课程名称
        write_date: 编写日期
        assessment_method: 考核方式及成绩评定办法
        focus_modules: 重点功能模块
        exclude_items: 排除项
        llm_provider: 大模型提供商
        llm_api_key: API密钥
        llm_model: 模型名称
    
    Returns:
        dict: 包含所有模板变量的字典
    """
    
    # 设置默认值
    if not write_date:
        write_date = datetime.now().strftime("%Y年%m月")
    
    if not assessment_method:
        assessment_method = "平时成绩30% + 期中考试30% + 期末考试40%"
    
    # 构建基础数据
    outline_data = {
        '课程名称': course_name,
        '编写日期': write_date,
        '考核方式及成绩评定办法': assessment_method,
    }
    
    # 如果有AI配置，使用AI生成内容
    if llm_provider and llm_api_key:
        try:
            ai_generated = generate_with_ai(
                course_name, exclude_items,
                system_prompt, user_prompt,
                llm_provider, llm_api_key, llm_model,
                positioning_length, objectives_length, module_content_length
            )
            outline_data.update(ai_generated)
        except Exception as e:
            logger.error(f"AI生成失败: {e}")
            # 如果AI生成失败，使用默认模板
            outline_data.update(generate_default_content(course_name))
    else:
        # 使用默认模板生成
        outline_data.update(generate_default_content(course_name))
    
    return outline_data


def generate_with_ai(course_name, exclude_items,
                    system_prompt, user_prompt, 
                    llm_provider, llm_api_key, llm_model,
                    positioning_length=100, objectives_length=80, module_content_length=60):
    """
    使用AI生成教学大纲内容
    """
    
    # 构建提示词
    prompt = build_prompt(course_name, exclude_items, 
                         system_prompt, user_prompt,
                         positioning_length, objectives_length, module_content_length)
    
    # 根据不同的模型提供商调用API
    if llm_provider.lower() == 'deepseek':
        response = call_deepseek_api(prompt, llm_api_key, llm_model or 'deepseek-chat')
    elif llm_provider.lower() == 'openai':
        response = call_openai_api(prompt, llm_api_key, llm_model or 'gpt-4o-mini')
    else:
        raise ValueError(f"不支持的模型提供商: {llm_provider}")
    
    # 解析AI响应
    return parse_ai_response(response)


def build_prompt(course_name, exclude_items=None,
                system_prompt=None, user_prompt=None, 
                positioning_length=100, objectives_length=80, module_content_length=60):
    """
    构建AI生成的提示词
    """
    
    # 解析重点模块，确保AI真正关注用户输入
    focus_requirements = ""
    if focus_modules and focus_modules.strip():
        focus_list = [m.strip() for m in focus_modules.replace('，', ',').split(',') if m.strip()]
        if focus_list:
            focus_requirements = f"""
【❗️最高优先级】重点功能模块强制要求：
用户明确指定了以下重点模块：{', '.join(focus_list)}

🔥严格强制要求：
1. 在8个教学模块中，必须至少有{min(len(focus_list), 6)}个模块直接体现这些重点内容
2. 教学模块名称必须包含重点模块的关键词，不能是“基础理论”等通用词
3. 教学内容必须紧密围绕重点模块设计，不能使用模糊描述
4. 禁止使用通用模板，必须针对具体课程和重点模块定制化生成

🌆具体示例：如果重点模块是“数据库设计”，则：
- 教学模块名称应为“数据库设计与实现”或“关系数据库设计”
- 教学内容必须包含：ER图设计、表结构设计、索引优化等具体技术
- 重点和难点：数据库范式化、查询优化、数据一致性等具体难点
"""
    
    exclude_requirements = ""
    if exclude_items and exclude_items.strip():
        exclude_requirements = f"""
🚫排除内容：{exclude_items}
（在所有内容中严格避免或减少这些内容）
"""
    
    # 处理系统提示词（基调、规则和重点模块）
    system_requirements = ""
    if system_prompt and system_prompt.strip():
        # 从系统提示词中提取重点模块
        focus_modules_from_system = ""
        import re
        # 查找重点模块相关关键词
        if '重点' in system_prompt or '模块' in system_prompt:
            # 提取重点模块信息
            focus_match = re.search(r'重点[^\n]*[:]（\])*([^\n]+)', system_prompt)
            if focus_match:
                focus_content = focus_match.group(1).strip()
                focus_list = [m.strip() for m in focus_content.replace('，', ',').split(',') if m.strip()]
                if focus_list:
                    focus_modules_from_system = f"""

【❗️最高优先级】重点功能模块强制要求：
用户在系统提示词中明确指定了以下重点模块：{', '.join(focus_list)}

🔥严格强制要求：
1. 在8个教学模块中，必须至少有{min(len(focus_list), 6)}个模块直接体现这些重点内容
2. 教学模块名称必须包含重点模块的关键词，不能是“基础理论”等通用词
3. 教学内容必须紧密围绕重点模块设计，不能使用模糊描述
4. 禁止使用通用模板，必须针对具体课程和重点模块定制化生成
"""
        
        system_requirements = f"""
⚙️ 系统基调和规则：
{system_prompt}
{focus_modules_from_system}

【强制要求】在生成所有内容时，必须严格遵循以上系统基调和规则。
"""
    
    # 处理用户提示词（重点突出方向）
    user_requirements = ""
    if user_prompt and user_prompt.strip():
        user_requirements = f"""
💡 特别强调和突出方向：
{user_prompt}

在遵循系统基调的前提下，请特别强调和突出以上方面。
"""
    
    prompt = f"""
你是一位资深的课程设计专家，请为《{course_name}》课程生成高质量、个性化的教学大纲内容。

{system_requirements}

🎯 课程特色化强制要求：
根据课程名称《{course_name}》，所有生成内容必须与该课程高度相关：
- 教学模块名称必须包含{course_name}的关键技术词汇，禁止使用“基础理论”等通用词
- 教学内容必须体现{course_name}的具体技术点和应用场景
- 每个模块的重点难点必须针对{course_name}的具体技术难点

{exclude_requirements}

{user_requirements}

内容长度控制要求：
- 课程定位：约{positioning_length}字
- 知识目标、技能目标、素质目标：每项约{objectives_length}字
- 教学内容及重点、难点：每项约{module_content_length}字
- 其他字段：根据实际需要适当控制长度

生成要求：
1. 内容必须专业、准确，符合高等教育教学大纲规范
2. 教学模块要体现课程特色，不能使用通用模板
3. 必须根据课程名称定制化生成相关内容
4. 8个教学模块应循序渐进，课时安排合理（总计64-72学时）
5. 严格按照JSON格式返回，确保字段完整

请返回以下完整的JSON格式：
{{
    "课程定位": "约{positioning_length}字，描述课程在专业培养中的地位和作用",
    "知识目标": "约{objectives_length}字，学生应掌握的理论知识和概念",
    "技能目标": "约{objectives_length}字，学生应具备的实践技能和操作能力",
    "素质目标": "约{objectives_length}字，学生应培养的职业素养和综合能力",
    "教学方式、方法与手段建议": "具体的教学方法和手段",
    "教学及参考资料": "推荐的教材和参考书目",
    "课程编码": "课程代码",
    "学时": "总学时数",
    "学分": "学分数",
    "课程类别": "课程类型",
    "适用专业": "适用的专业名称",
    "modules": [
        {{
            "模块编号": 1,
            "教学模块": "必须包含《{course_name}》的关键词，不能是通用名称",
            "教学内容及重点、难点": "约{module_content_length}字，必须是《{course_name}》的具体技术内容，不能是模糊描述",
            "职业技能要求": "针对《{course_name}》的具体技能要求",
            "课时": "课时安排",
            "教学方法建议": "针对性教学方法"
        }},
        {{
            "模块编号": 2,
            "教学模块": "第二个教学模块名称",
            "教学内容及重点、难点": "约{module_content_length}字，详细内容、重点和难点",
            "职业技能要求": "技能要求",
            "课时": "课时安排",
            "教学方法建议": "教学方法"
        }},
        {{
            "模块编号": 3,
            "教学模块": "第三个教学模块名称",
            "教学内容及重点、难点": "约{module_content_length}字，详细内容、重点和难点",
            "职业技能要求": "技能要求",
            "课时": "课时安排",
            "教学方法建议": "教学方法"
        }},
        {{
            "模块编号": 4,
            "教学模块": "第四个教学模块名称",
            "教学内容及重点、难点": "约{module_content_length}字，详细内容、重点和难点",
            "职业技能要求": "技能要求",
            "课时": "课时安排",
            "教学方法建议": "教学方法"
        }},
        {{
            "模块编号": 5,
            "教学模块": "第五个教学模块名称",
            "教学内容及重点、难点": "约{module_content_length}字，详细内容、重点和难点",
            "职业技能要求": "技能要求",
            "课时": "课时安排",
            "教学方法建议": "教学方法"
        }},
        {{
            "模块编号": 6,
            "教学模块": "第六个教学模块名称",
            "教学内容及重点、难点": "约{module_content_length}字，详细内容、重点和难点",
            "职业技能要求": "技能要求",
            "课时": "课时安排",
            "教学方法建议": "教学方法"
        }},
        {{
            "模块编号": 7,
            "教学模块": "第七个教学模块名称",
            "教学内容及重点、难点": "约{module_content_length}字，详细内容、重点和难点",
            "职业技能要求": "技能要求",
            "课时": "课时安排",
            "教学方法建议": "教学方法"
        }},
        {{
            "模块编号": 8,
            "教学模块": "第八个教学模块名称",
            "教学内容及重点、难点": "约{module_content_length}字，详细内容、重点和难点",
            "职业技能要求": "技能要求",
            "课时": "课时安排",
            "教学方法建议": "教学方法"
        }}
    ],
    "总课时": "所有模块的总课时"
}}

【关键提醒】：
1. 必须严格按照上述JSON格式返回完整内容
2. modules数组必须包含8个完整的模块对象
3. 如果用户指定了重点模块，必须在相应的教学模块中体现
4. 内容不能是通用模板，必须根据具体课程定制化生成
5. 确保字数控制在指定范围内
"""

    return prompt


def call_deepseek_api(prompt, api_key, model):
    """
    调用DeepSeek API
    """
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 4000
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    return result['choices'][0]['message']['content']


def call_openai_api(prompt, api_key, model):
    """
    调用OpenAI API
    """
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9,
        "max_tokens": 4000
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    return result['choices'][0]['message']['content']


def parse_ai_response(response_text):
    """
    解析AI返回的JSON响应
    """
    try:
        # 尝试直接解析JSON
        data = json.loads(response_text)
        
        # 处理新的modules数组格式，将其展开为扁平结构
        if 'modules' in data and isinstance(data['modules'], list):
            modules_data = data.pop('modules')  # 移除modules数组
            
            # 将modules数组中的每个模块展开为原来的扁平字段格式
            for module in modules_data:
                if isinstance(module, dict) and '模块编号' in module:
                    module_num = module['模块编号']
                    
                    # 将模块数据映射到原来的字段名
                    if '教学模块' in module:
                        data[f'教学模块{module_num}'] = module['教学模块']
                    if '教学内容及重点、难点' in module:
                        data[f'教学内容及重点、难点{module_num}'] = module['教学内容及重点、难点']
                    if '职业技能要求' in module:
                        data[f'职业技能要求{module_num}'] = module['职业技能要求']
                    if '课时' in module:
                        data[f'课时{module_num}'] = module['课时']
                    if '教学方法建议' in module:
                        data[f'教学方法建议{module_num}'] = module['教学方法建议']
        
        return data
        
    except json.JSONDecodeError:
        # 如果不是纯JSON，尝试提取JSON部分
        try:
            # 查找JSON代码块
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                data = json.loads(json_str)
                
                # 处理modules数组格式
                if 'modules' in data and isinstance(data['modules'], list):
                    modules_data = data.pop('modules')
                    for module in modules_data:
                        if isinstance(module, dict) and '模块编号' in module:
                            module_num = module['模块编号']
                            if '教学模块' in module:
                                data[f'教学模块{module_num}'] = module['教学模块']
                            if '教学内容及重点、难点' in module:
                                data[f'教学内容及重点、难点{module_num}'] = module['教学内容及重点、难点']
                            if '职业技能要求' in module:
                                data[f'职业技能要求{module_num}'] = module['职业技能要求']
                            if '课时' in module:
                                data[f'课时{module_num}'] = module['课时']
                            if '教学方法建议' in module:
                                data[f'教学方法建议{module_num}'] = module['教学方法建议']
                
                return data
            
            # 查找大括号包围的JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                # 处理modules数组格式
                if 'modules' in data and isinstance(data['modules'], list):
                    modules_data = data.pop('modules')
                    for module in modules_data:
                        if isinstance(module, dict) and '模块编号' in module:
                            module_num = module['模块编号']
                            if '教学模块' in module:
                                data[f'教学模块{module_num}'] = module['教学模块']
                            if '教学内容及重点、难点' in module:
                                data[f'教学内容及重点、难点{module_num}'] = module['教学内容及重点、难点']
                            if '职业技能要求' in module:
                                data[f'职业技能要求{module_num}'] = module['职业技能要求']
                            if '课时' in module:
                                data[f'课时{module_num}'] = module['课时']
                            if '教学方法建议' in module:
                                data[f'教学方法建议{module_num}'] = module['教学方法建议']
                
                return data
                
        except json.JSONDecodeError:
            pass
    
    # 如果解析失败，返回默认内容
    logger.error(f"无法解析AI响应: {response_text}")
    return {}


def generate_default_content(course_name):
    """
    生成默认的教学大纲内容模板
    """
    return {
        '课程定位': f'{course_name}是专业核心课程，旨在培养学生的专业技能和实践能力，在专业课程体系中起到承上启下的重要作用。',
        '知识目标': f'1. 掌握{course_name}的基本理论、核心概念和基础知识\n2. 理解相关技术原理和发展趋势\n3. 熟悉行业标准和规范要求',
        '技能目标': f'1. 具备{course_name}相关的实践操作能力和问题解决能力\n2. 掌握专业工具和软件的使用方法\n3. 能够独立完成相关项目和任务',
        '素质目标': '1. 培养良好的职业道德和职业素养\n2. 增强团队协作精神和沟通能力\n3. 培养创新意识和持续学习能力',
        '教学方式、方法与手段建议': '采用理论讲授、案例分析、实践操作、小组讨论、项目驱动等多种教学方法，结合线上线下混合式教学，运用现代信息技术手段提升教学效果。',
        '教学及参考资料': f'1. 《{course_name}》权威教材，高等教育出版社\n2. 相关技术文档和行业标准\n3. 在线学习资源和视频教程\n4. 实际项目案例和企业实践资料',
        '课程编码': 'CS001',
        '学时': '72',
        '学分': '4',
        '课程类别': '专业核心课',
        '适用专业': '计算机类专业',
        # 完整的8个教学模块
        '教学模块1': '基础理论与概念',
        '教学内容及重点、难点1': f'重点：{course_name}基本概念、理论基础、核心原理；难点：理论与实践的结合，概念的深入理解。',
        '职业技能要求1': '理解和掌握基础理论知识',
        '课时1': '8学时',
        '教学方法建议1': '理论讲授结合案例分析',
        
        '教学模块2': '核心技术与方法',
        '教学内容及重点、难点2': f'重点：{course_name}核心技术、主要方法、技术路线；难点：技术原理的掌握和灵活运用。',
        '职业技能要求2': '熟练掌握核心技术和方法',
        '课时2': '10学时',
        '教学方法建议2': '技术演示结合实践操作',
        
        '教学模块3': '实践应用与操作',
        '教学内容及重点、难点3': f'重点：{course_name}实际应用、操作技能、实践环节；难点：理论知识向实践技能的转化。',
        '职业技能要求3': '具备独立操作和应用能力',
        '课时3': '10学时',
        '教学方法建议3': '实践操作结合指导训练',
        
        '教学模块4': '项目开发与设计',
        '教学内容及重点、难点4': f'重点：{course_name}项目设计方法、开发流程、设计原则；难点：综合运用知识进行项目设计。',
        '职业技能要求4': '具备项目设计和开发能力',
        '课时4': '10学时',
        '教学方法建议4': '项目驱动教学法',
        
        '教学模块5': '案例分析与研究',
        '教学内容及重点、难点5': f'重点：{course_name}典型案例分析、问题研究方法；难点：案例分析能力和批判性思维的培养。',
        '职业技能要求5': '具备案例分析和研究能力',
        '课时5': '8学时',
        '教学方法建议5': '案例教学法结合小组讨论',
        
        '教学模块6': '综合实训与考核',
        '教学内容及重点、难点6': f'重点：{course_name}综合实训项目、技能考核标准；难点：综合技能的整合和应用。',
        '职业技能要求6': '达到综合应用技能标准',
        '课时6': '10学时',
        '教学方法建议6': '综合实训结合技能考核',
        
        '教学模块7': '前沿技术与发展',
        '教学内容及重点、难点7': f'重点：{course_name}前沿技术发展、新技术应用、行业趋势；难点：新技术的理解和应用前景分析。',
        '职业技能要求7': '了解行业发展和新技术趋势',
        '课时7': '8学时',
        '教学方法建议7': '专题讲座结合技术调研',
        
        '教学模块8': '总结提升与拓展',
        '教学内容及重点、难点8': f'重点：{course_name}知识体系总结、能力提升路径、学习拓展方向；难点：知识整合和能力提升规划。',
        '职业技能要求8': '形成完整的知识技能体系',
        '课时8': '8学时',
        '教学方法建议8': '总结交流结合学习规划',
        
        '总课时': '72学时'
    }