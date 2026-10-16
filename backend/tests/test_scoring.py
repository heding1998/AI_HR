from app.llm import DeepSeekClient, LLMNotConfiguredError
from app.schemas import ScoringStandardAIn, ScoringStandardBIn
from app.scoring import (
    build_scoring_prompt,
    compute_resume_score,
    is_pass,
    normalize_match_weights,
    tier_for_score,
)


def _a_row(category: str, subcategory: str, subcategory_score: float) -> ScoringStandardAIn:
    return ScoringStandardAIn(
        category=category,
        subcategory=subcategory,
        category_score=subcategory_score,
        subcategory_score=subcategory_score,
    )


SEED_A = [
    _a_row("学历", "学历", 2),
    _a_row("工作经验", "工作经验", 3),
    _a_row("项目经验", "项目经验", 3),
    _a_row("个人技能", "个人技能", 2),
]


def test_compute_resume_score_full_match_is_10():
    weights = {"学历": 10, "工作经验": 10, "项目经验": 10, "个人技能": 10}

    assert compute_resume_score(SEED_A, weights) == 10.0


def test_compute_resume_score_partial_match():
    weights = {"学历": 8, "工作经验": 8, "项目经验": 10, "个人技能": 8}

    # 学历 1.6 + 工作经验 2.4 + 项目经验 3.0 + 个人技能 1.6 = 8.6
    assert compute_resume_score(SEED_A, weights) == 8.6


def test_compute_resume_score_missing_weight_is_zero():
    assert compute_resume_score(SEED_A, {}) == 0.0


def test_compute_resume_score_caps_at_10():
    a_rows = [
        _a_row("A", "A1", 10),
        _a_row("B", "B1", 10),
    ]
    weights = {"A1": 10, "B1": 10}

    assert compute_resume_score(a_rows, weights) == 10.0


def test_normalize_match_weights_clamps_and_drops_non_numeric():
    raw = {"学历": "8", "工作经验": 12, "项目经验": -1, "个人技能": "abc"}

    assert normalize_match_weights(raw) == {
        "学历": 8.0,
        "工作经验": 10.0,
        "项目经验": 0.0,
    }


def test_normalize_match_weights_skips_non_finite():
    raw = {"学历": float("nan"), "工作经验": float("inf"), "项目经验": 8}

    assert normalize_match_weights(raw) == {"项目经验": 8.0}


def test_build_scoring_prompt_contains_standard():
    a_rows = [_a_row("学历", "学历", 2)]
    b_rows = [
        ScoringStandardBIn(
            category="学历",
            subcategory="学历",
            level1_indicator="最高学历",
            level2_indicator="硕士及以上",
            weight=10,
        )
    ]

    prompt = build_scoring_prompt(a_rows, b_rows)

    assert "学历" in prompt
    assert "满分 2" in prompt
    assert "硕士及以上" in prompt


def test_deepseek_score_unconfigured_raises():
    client = DeepSeekClient(api_key="")

    try:
        client.score_resume({}, [], [])
    except LLMNotConfiguredError as exc:
        assert "DEEPSEEK_API_KEY" in str(exc)
    else:
        raise AssertionError("应抛出 LLMNotConfiguredError")


def test_is_pass_threshold():
    assert is_pass(7.0) is True
    assert is_pass(6.9) is False
    assert is_pass(10.0) is True


def test_tier_for_score_boundaries():
    assert tier_for_score(7.0) == "一般优秀"
    assert tier_for_score(7.9) == "一般优秀"
    assert tier_for_score(8.0) == "中等优秀"
    assert tier_for_score(8.9) == "中等优秀"
    assert tier_for_score(9.0) == "特别优秀"
    assert tier_for_score(9.5) == "特别优秀"
