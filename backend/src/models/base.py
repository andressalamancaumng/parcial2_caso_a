from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
