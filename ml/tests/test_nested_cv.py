from hepatwin_ml.nested_cv import GATNN_SEARCH_SPACE, RF_SEARCH_SPACE, _sample_trials


def test_sample_trials_returns_requested_count_without_duplicates():
    trials = _sample_trials(RF_SEARCH_SPACE, n_trials=5, seed=42)
    assert len(trials) == 5
    seen = {tuple(sorted(t.items())) for t in trials}
    assert len(seen) == 5, "budget trial tidak boleh duplikat"


def test_sample_trials_caps_at_search_space_size():
    # RF_SEARCH_SPACE = 3 n_estimators x 3 max_depth = 9 kombinasi total
    trials = _sample_trials(RF_SEARCH_SPACE, n_trials=100, seed=42)
    assert len(trials) == 9


def test_sample_trials_deterministic_given_same_seed():
    a = _sample_trials(GATNN_SEARCH_SPACE, n_trials=10, seed=7)
    b = _sample_trials(GATNN_SEARCH_SPACE, n_trials=10, seed=7)
    assert a == b


def test_sample_trials_values_come_from_search_space():
    trials = _sample_trials(GATNN_SEARCH_SPACE, n_trials=10, seed=1)
    for t in trials:
        assert t["lr"] in GATNN_SEARCH_SPACE["lr"]
        assert t["hidden"] in GATNN_SEARCH_SPACE["hidden"]
        assert t["dropout"] in GATNN_SEARCH_SPACE["dropout"]
