"""Unit tests for settings resolution (no external services).

Юнит-тесты резолва настроек (без внешних сервисов).
"""

import settings
from settings import _resolve_values


class TestResolveValues:
    def test_process_env_wins_over_files(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", "redis://:secret@real:6381/0")
        resolved = _resolve_values({"REDIS_URL": "redis://file:6379/0"})
        assert resolved["REDIS_URL"] == "redis://:secret@real:6381/0"

    def test_blank_env_value_is_ignored(self, monkeypatch):
        monkeypatch.setenv("REDIS_URL", "   ")
        resolved = _resolve_values({"REDIS_URL": "redis://file:6379/0"})
        assert resolved["REDIS_URL"] == "redis://file:6379/0"

    def test_unknown_env_keys_are_ignored(self, monkeypatch):
        monkeypatch.setenv("QUANT_SOME_RANDOM_KEY", "1")
        resolved = _resolve_values({})
        assert "QUANT_SOME_RANDOM_KEY" not in resolved

    def test_file_values_kept_without_env(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        resolved = _resolve_values({"REDIS_URL": "redis://file:6379/0"})
        assert resolved["REDIS_URL"] == "redis://file:6379/0"

    def test_resolve_uses_main_cfg_fields(self):
        assert set(settings.MainCFG.model_fields) >= {
            "REDIS_URL",
            "DB_TYPE",
            "DB_PATH",
        }


class TestLoadEnvValues:
    def test_local_env_overrides_test_env(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env.tests").write_text("REDIS_URL=redis://file-tests:6379/0\n")
        (tmp_path / ".env").write_text(
            "REDIS_URL=redis://:secret@file-local:6381/0\n"
        )
        values = settings._load_env_values()
        assert values["REDIS_URL"] == "redis://:secret@file-local:6381/0"

    def test_test_env_used_when_no_local_env(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env.tests").write_text("REDIS_URL=redis://file-tests:6379/0\n")
        values = settings._load_env_values()
        assert values["REDIS_URL"] == "redis://file-tests:6379/0"

    def test_missing_files_give_empty_dict(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert settings._load_env_values() == {}
