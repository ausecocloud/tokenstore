from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    Float,
    LargeBinary,
)

from .meta import Base


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    id = Column(Integer, primary_key=True)
    provider = Column(Text, index=True)
    token = Column(LargeBinary)
    expires_in = Column(Integer)
    expires_at = Column(Float)
    user_id = Column(Text, index=True)


# Index('refresh_tokens_provider_index', RefreshToken.provider, unique=True, mysql_length=255)
