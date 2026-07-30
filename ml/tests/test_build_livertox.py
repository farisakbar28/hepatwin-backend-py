from hepatwin_ml.data.build_livertox import clean_likelihood_score, harmonize_livertox_score


def test_clean_likelihood_score_strips_hd_suffix_variants():
    assert clean_likelihood_score("A [HD]") == "a"
    assert clean_likelihood_score("C[HD]") == "c"
    assert clean_likelihood_score("E*") == "e*"
    assert clean_likelihood_score("B") == "b"


def test_harmonize_livertox_score_binarizes_correctly():
    assert harmonize_livertox_score("A") == 1
    assert harmonize_livertox_score("A [HD]") == 1
    assert harmonize_livertox_score("B") == 1
    assert harmonize_livertox_score("E") == 0
    assert harmonize_livertox_score("E*") == 0
    assert harmonize_livertox_score("C") is None
    assert harmonize_livertox_score("D") is None
    assert harmonize_livertox_score("X") is None


def test_harmonize_livertox_score_handles_missing_and_junk():
    assert harmonize_livertox_score(None) is None
    assert harmonize_livertox_score(float("nan")) is None
    assert harmonize_livertox_score("Likelihood Score") is None
