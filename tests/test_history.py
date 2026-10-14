import json

from core import history


def test_history_round_trip_keeps_only_the_last_50(tmp_path):
    path = tmp_path / "hist.json"
    items = [{"title": f"v{i}"} for i in range(60)]
    history.save_hist(items, path)
    loaded = history.load_hist(path, legacy=tmp_path / "nao-existe.json")
    assert len(loaded) == 50
    assert loaded[0]["title"] == "v10" and loaded[-1]["title"] == "v59"


def test_people_who_used_the_old_name_keep_their_history(tmp_path):
    legacy = tmp_path / "old.json"
    legacy.write_text(json.dumps([{"title": "antigo"}]), "utf-8")
    assert history.load_hist(tmp_path / "novo.json", legacy=legacy) == [{"title": "antigo"}]


def test_a_broken_file_does_not_crash_the_app(tmp_path):
    path = tmp_path / "hist.json"
    path.write_text("{ não é json", "utf-8")
    assert history.load_hist(path, legacy=tmp_path / "x.json") == []
