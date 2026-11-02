"""Guard against divergent heads breaking clean deployments."""
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_migrations_have_one_head_containing_both_feature_branches():
    root = Path(__file__).resolve().parents[2]
    scripts = ScriptDirectory.from_config(Config(str(root / "alembic.ini")))
    assert len(scripts.get_heads()) == 1
    revisions = {revision.revision for revision in scripts.walk_revisions()}
    assert {"b7c4e9a2f105", "c4d8e2f1a901"} <= revisions
    assert scripts.get_current_head() == "d2f6a8c9013b"
