from sqlalchemy import Column, Integer, String, Float
from backend.database import Base

class PartModel(Base):
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    part_name = Column(String, index=True)
    material = Column(String)
    size = Column(String)
    base_price = Column(Float)
    seller_name = Column(String)