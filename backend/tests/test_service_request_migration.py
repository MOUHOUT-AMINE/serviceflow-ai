from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def test_service_request_migration_downgrade_and_upgrade(test_engine: Engine) -> None:
    config = Config("alembic.ini")
    command.downgrade(config, "20260820_02")
    assert "service_requests" not in inspect(test_engine).get_table_names()

    command.upgrade(config, "head")
    inspector = inspect(test_engine)
    assert "service_requests" in inspector.get_table_names()
    foreign_keys = {
        tuple(foreign_key["constrained_columns"]): foreign_key["options"].get(
            "ondelete"
        )
        for foreign_key in inspector.get_foreign_keys("service_requests")
    }
    assert foreign_keys[("customer_id",)] == "RESTRICT"
    assert foreign_keys[("created_by_user_id",)] == "RESTRICT"
    assert foreign_keys[("assigned_agent_id",)] == "SET NULL"
