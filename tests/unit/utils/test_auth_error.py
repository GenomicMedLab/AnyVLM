from anyvlm.utils.exceptions import AuthError, AuthErrorReason


def test_auth_error_contains_mappings_for_all_reasons() -> None:
    for reason in AuthErrorReason:
        assert reason in AuthError.reason_to_code_mapping
