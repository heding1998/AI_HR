"""评分标准相关的纯逻辑：A表/B表配置校验，以及（T07 起）评分计算。"""

from .schemas import ScoringStandardAIn, ScoringStandardBIn

TOTAL_SCORE = 10.0
MIN_WEIGHT = 2
MAX_WEIGHT = 10


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
    for row in rows:
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
