from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy import select
from org_api.models import Item

def test_create_item():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        item = Item(name="Test", description="Desc")
        session.add(item)
        session.commit()
        result = session.exec(select(Item)).first()
        assert result.name == "Test"
