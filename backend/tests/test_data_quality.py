
from app.validation.data_quality import run_validation


def test_database_data_quality():
    report = run_validation()

    assert report["passed"] is True
    assert report["primary_key_issues"] == []
    assert report["foreign_key_violations"] == []
    assert report["timestamp_issues"] == []
    assert report["allowed_value_issues"] == []
    assert report["business_rule_issues"] == []
