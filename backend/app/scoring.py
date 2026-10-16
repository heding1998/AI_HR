"""评分标准相关的纯逻辑：A表/B表配置校验，以及（T07 起）评分计算。"""

import math
from collections.abc import Mapping, Sequence
from typing import Any

from .schemas import ScoringStandardAIn, ScoringStandardBIn

TOTAL_SCORE = 10.0
MIN_WEIGHT = 2
MAX_WEIGHT = 10

PASS_THRESHOLD = 7.0  # 初筛通过 / 进入人才库的分数阈值
TIER_NORMAL = "一般优秀"  # 7 <= score < 8
TIER_GOOD = "中等优秀"  # 8 <= score < 9
TIER_EXCELLENT = "特别优秀"  # score >= 9


def validate_a_table(rows: list[ScoringStandardAIn]) -> str | None:
    """校验 A 表，合法返回 None，否则返回错误消息。

    规则：
    - 单个大类分数与小类分数都须在 [0, 10]；
    - 同一大类各行的大类分数必须一致；
    - 各大类分数之和等于总分 10；
    - 每个大类下的小类分数之和等于该大类分数。
    """
    category_scores: dict[str, float] = {}
    subcategory_sums: dict[str, float] = {}
    seen_subcategories: set[str] = set()
    for row in rows:
        if row.subcategory in seen_subcategories:
            return f"小类「{row.subcategory}」重复，岗位内小类名须唯一"
        seen_subcategories.add(row.subcategory)

        if not (0 <= row.category_score <= TOTAL_SCORE):
            return f"大类分数须在 0~{TOTAL_SCORE} 之间，当前为 {row.category_score}"
        if not (0 <= row.subcategory_score <= TOTAL_SCORE):
            return f"小类分数须在 0~{TOTAL_SCORE} 之间，当前为 {row.subcategory_score}"

        if row.category in category_scores:
            if abs(category_scores[row.category] - row.category_score) > 0.01:
                return (
                    f"大类「{row.category}」的大类分数不一致："
                    f"{category_scores[row.category]} 与 {row.category_score}"
                )
        else:
            category_scores[row.category] = row.category_score

        subcategory_sums[row.category] = (
            subcategory_sums.get(row.category, 0.0) + row.subcategory_score
        )

    total = sum(category_scores.values())
    if abs(total - TOTAL_SCORE) > 0.01:
        return f"A 表大类分数合计应为 {TOTAL_SCORE} 分，当前为 {total} 分"

    for category, score in category_scores.items():
        sub_sum = subcategory_sums[category]
        if abs(sub_sum - score) > 0.01:
            return f"大类「{category}」的小类分数合计应为 {score} 分，当前为 {sub_sum} 分"

    return None


def validate_b_table(rows: list[ScoringStandardBIn]) -> str | None:
    """校验 B 表，合法返回 None，否则返回错误消息。权重须在 [2, 10]。"""
    for row in rows:
        if not (MIN_WEIGHT <= row.weight <= MAX_WEIGHT):
            return f"权重需在 {MIN_WEIGHT}~{MAX_WEIGHT} 之间，当前为 {row.weight}"
    return None


def compute_resume_score(
    a_rows: Sequence[ScoringStandardAIn],
    match_weights: Mapping[str, float],
) -> float:
    """由 A 表与各小类匹配权重计算 0~10 总分。

    小类得分 = 匹配权重 / 最高权重(10) × 小类分数；
    大类得分 = 该大类下各小类得分之和；
    总分 = 各大类得分之和（上限 10）。
    """
    category_sums: dict[str, float] = {}
    for row in a_rows:
        weight = match_weights.get(row.subcategory, 0.0)
        sub_score = (weight / MAX_WEIGHT) * row.subcategory_score
        category_sums[row.category] = category_sums.get(row.category, 0.0) + sub_score
    total = sum(category_sums.values())
    return round(min(total, TOTAL_SCORE), 2)


def normalize_match_weights(raw: Mapping[str, Any]) -> dict[str, float]:
    """把 LLM 返回的匹配权重规整为 {小类名: 0~10 的 float}，丢弃非法/非有限值。"""
    weights: dict[str, float] = {}
    for key, value in raw.items():
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(number):
            continue
        weights[str(key)] = min(max(number, 0.0), MAX_WEIGHT)
    return weights


def build_scoring_prompt(
    a_rows: Sequence[ScoringStandardAIn],
    b_rows: Sequence[ScoringStandardBIn],
) -> str:
    """根据 A/B 表构建评分提示词（简历内容由调用方作为用户消息传入）。"""
    a_lines = "\n".join(
        f"- {row.subcategory}：满分 {row.subcategory_score}" for row in a_rows
    )

    by_subcategory: dict[str, list[ScoringStandardBIn]] = {}
    for row in b_rows:
        by_subcategory.setdefault(row.subcategory, []).append(row)
    b_parts = []
    for sub, rows in by_subcategory.items():
        first = rows[0]
        options = "；".join(f"{r.level2_indicator}（权重 {r.weight}）" for r in rows)
        b_parts.append(f"- {first.category} / {sub}（{first.level1_indicator}）：{options}")
    b_lines = "\n".join(b_parts)

    return f"""\
你是一名专业的 HR 简历评分助手。请依据评分标准，对简历内容与各小类指标进行匹配打分。

评分标准（A 表：小类及其满分）：
{a_lines}

评分标准（B 表：各小类的匹配指标及权重）：
{b_lines}

请对每个小类，选择最匹配简历内容的一项指标，返回其权重（0~10 的数字）。\
只输出一个 JSON 对象，键为小类名，值为匹配权重；无法判断时权重为 0。"""


def is_pass(score: float) -> bool:
    """分数是否达到初筛通过阈值（≥7）。"""
    return score >= PASS_THRESHOLD


def tier_for_score(score: float) -> str:
    """把 ≥7 的分数映射为人才库分级。"""
    if score >= 9.0:
        return TIER_EXCELLENT
    if score >= 8.0:
        return TIER_GOOD
    return TIER_NORMAL

