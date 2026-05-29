from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def add_token_to_blacklist(
    db: AsyncSession,
    jti: str
):

    await db.execute(
        text("""
            INSERT INTO token_blacklist
            (
                jti,
                created_at
            )
            VALUES
            (
                :jti,
                NOW()
            )
            ON CONFLICT (jti)
            DO NOTHING
        """),
        {
            "jti": jti
        }
    )

    await db.commit()


async def is_blacklisted(
    db: AsyncSession,
    jti: str
):

    result = await db.execute(
        text("""
            SELECT jti
            FROM token_blacklist
            WHERE jti = :jti
            LIMIT 1
        """),
        {
            "jti": jti
        }
    )

    return result.fetchone() is not None