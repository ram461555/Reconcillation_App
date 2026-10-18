"""SQLAlchemy engine/session setup for SQLite, with WAL mode and FK enforcement."""
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

db_path = settings.database_url.replace("sqlite:///", "")
Path(db_path).parent.mkdir(parents=True, exist_ok=True)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    """Enable foreign key enforcement and WAL mode for every new connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Columns added to already-existing tables after the initial release. Base.metadata.create_all()
# only creates missing *tables*, so any local SQLite file created before these fields existed needs
# them added manually instead of the whole database being wiped and re-created.
_NEW_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "txn": [("bank_label", "TEXT")],
    "reconciliation_session": [
        ("additional_bank_filenames", "TEXT"),
        ("ledger_source", "TEXT NOT NULL DEFAULT 'pdf'"),
    ],
}


def run_lightweight_migrations() -> None:
    """Add any new nullable/defaulted columns that don't exist yet on an existing SQLite file."""
    with engine.connect() as conn:
        for table, columns in _NEW_COLUMNS.items():
            existing = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()}
            for column_name, column_type in columns:
                if existing and column_name not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type}")
        conn.commit()
