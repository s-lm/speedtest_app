from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text, Integer, Float, DateTime

db = SQLAlchemy()

class SpeedTest(db.Model):
    __tablename__ = "speedtest"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    server_id: Mapped[int] = mapped_column(Integer)
    sponsor: Mapped[str] = mapped_column(Text)
    server_name: Mapped[str] = mapped_column(Text)
    server_host: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index = True)
    distance: Mapped[float] = mapped_column(Float)
    ping: Mapped[float] = mapped_column(Float)
    download: Mapped[float] = mapped_column(Float)
    upload: Mapped[float] = mapped_column(Float)
    share: Mapped[str] = mapped_column(Text, nullable=True)
    client_ip: Mapped[str] = mapped_column(Text)
    client_isp: Mapped[str] = mapped_column(Text)
    client_country: Mapped[str] = mapped_column(Text)

