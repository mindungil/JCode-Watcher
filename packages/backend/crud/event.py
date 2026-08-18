from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session


def insert_event_once(db: Session, model, values: dict) -> bool:
    bind = db.get_bind()
    if bind.dialect.name == "postgresql":
        statement = (
            postgresql_insert(model)
            .values(**values)
            .on_conflict_do_nothing(index_elements=["event_id"])
            .returning(model.id)
        )
        inserted = db.exec(statement).first() is not None
        db.commit()
        return inserted

    try:
        db.add(model(**values))
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False
