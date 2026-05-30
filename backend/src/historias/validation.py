from fastapi import HTTPException, status

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# --------------------------------
# VALIDAR ASIGNACIÓN MÉDICA
# --------------------------------
async def validate_medical_assignment(
    db: AsyncSession,
    medico_id: int,
    paciente_id: int
):

    result = await db.execute(
        text("""
            SELECT id
            FROM asignaciones_medicas
            WHERE medico_id = :medico_id
              AND paciente_id = :paciente_id
              AND activa = TRUE
            LIMIT 1
        """),
        {
            "medico_id": medico_id,
            "paciente_id": paciente_id
        }
    )

    assignment = result.fetchone()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El médico no tiene "
                "asignado este paciente"
            )
        )


# --------------------------------
# VALIDAR EXISTENCIA CIE10
# --------------------------------
async def validate_cie10_code(
    db: AsyncSession,
    codigo: str
):

    result = await db.execute(
        text("""
            SELECT codigo
            FROM catalogo_cie10
            WHERE codigo = :codigo
            LIMIT 1
        """),
        {
            "codigo": codigo
        }
    )

    cie10 = result.fetchone()

    if not cie10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código CIE10 inválido"
        )
