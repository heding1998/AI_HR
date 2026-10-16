from app.extraction import RESUME_FIELDS, normalize_resume_fields
from app.llm import DeepSeekClient, LLMNotConfiguredError


def test_normalize_resume_fields_fills_missing_with_none():
    result = normalize_resume_fields({"name": "张三", "contact": "13800000000"})

    assert set(result.keys()) == set(RESUME_FIELDS)
    assert result["name"] == "张三"
    assert result["contact"] == "13800000000"
    assert result["gender"] is None


def test_normalize_resume_fields_drops_extra_keys():
    result = normalize_resume_fields({"name": "张三", "unknown": "x"})

    assert "unknown" not in result
    assert len(result) == len(RESUME_FIELDS)


def test_normalize_resume_fields_sanitizes_non_finite_numbers():
    result = normalize_resume_fields(
        {
            "name": "张三",
            "age": float("nan"),
            "expected_salary": float("inf"),
            "skills": [float("nan"), "Python"],
        }
    )

    assert result["name"] == "张三"
    assert result["age"] is None
    assert result["expected_salary"] is None
    assert result["skills"] == [None, "Python"]


def test_deepseek_client_unconfigured_raises():
    client = DeepSeekClient(api_key="")

    try:
        client.extract_resume_fields("任意文本")
    except LLMNotConfiguredError as exc:
        assert "DEEPSEEK_API_KEY" in str(exc)
    else:
        raise AssertionError("应抛出 LLMNotConfiguredError")
