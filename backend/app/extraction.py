"""简历字段提取：提示词与 13 字段归一化。"""

import math
from typing import Any

RESUME_FIELDS = [
    "name",  # 姓名
    "gender",  # 性别
    "age",  # 年龄
    "highest_education",  # 最高学历
    "contact",  # 联系方式
    "work_years",  # 工作年限
    "job_intention",  # 求职意向
    "expected_salary",  # 期望薪资
    "expected_city",  # 期望城市
    "skills",  # 个人技能
    "work_experience",  # 工作经验
    "project_experience",  # 项目经验
    "self_evaluation",  # 自我评价
]

EXTRACTION_PROMPT = """\
你是一名专业的 HR 简历信息提取助手。请从给定的简历文本中提取以下 13 个字段，\
并只输出一个合法的 JSON 对象（不要包含任何额外说明或 Markdown 代码块）。

字段（JSON 键名固定如下）：
- name：姓名
- gender：性别
- age：年龄
- highest_education：最高学历
- contact：联系方式（电话 / 邮箱等）
- work_years：工作年限
- job_intention：求职意向
- expected_salary：期望薪资
- expected_city：期望城市
- skills：个人技能
- work_experience：工作经验
- project_experience：项目经验
- self_evaluation：自我评价

要求：
1. 字段值缺失或无法判断时，用 null 表示。
2. 多个值（如多个技能、多段经历）用字符串或数组表示，尽量保留原文信息。
3. 只输出 JSON，不要输出其它内容。
"""


def _sanitize(value: Any) -> Any:
    """递归清除 JSONB 无法存储的非法值（NaN/Infinity 置空）。"""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def normalize_resume_fields(raw: dict) -> dict:
    """将 LLM 返回的字段归一化为固定 13 键，缺失置空、丢弃多余键并清洗非法值。"""
    return {field: _sanitize(raw.get(field)) for field in RESUME_FIELDS}
