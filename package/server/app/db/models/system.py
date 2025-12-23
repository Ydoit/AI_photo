from sqlalchemy import Column, String, Text
from app.db.base import Base

class SystemState(Base):
    __tablename__ = "system_state"

    key = Column(String, primary_key=True, index=True)
    value = Column(Text) # JSON string
