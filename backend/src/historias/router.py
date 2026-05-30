from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException,
    status
)
from sqlalchemy import text

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import get_db

from src.auth.rbac import (
    RequireDoctor,
    RequirePatient
)

from src.historias.schemas import (
    MedicalAttentionRequest,
    MedicalSearchRequest
)

from src.historias.service import (
    get_patient_history,
    register_medical_attention,
    secure_medical_search
)

router = APIRouter()


# --------------------------------
# HISTORIA CLÍNICA PACIENTE
# --------------------------------
@router.get("/mis-historias")
async def my_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RequirePatient)
):

    result = await db.execute(
        text("""
            SELECT id
            FROM pacientes
            WHERE usuario_id = :usuario_id
            LIMIT 1
        """),
        {
            "usuario_id": int(current_user["sub"])
        }
    )

    paciente = result.fetchone()

    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )

    result = await get_patient_history(
        db=db,
        medico_id=paciente.id,
        paciente_id=paciente.id,
        ip_address=request.client.host
    )

    return {
        "historias": result
    }


# --------------------------------
# HISTORIA CLÍNICA MÉDICO
# --------------------------------
@router.get("/paciente/{paciente_id}")
async def patient_history(
    paciente_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RequireDoctor)
):

    result = await get_patient_history(
        db=db,
        medico_id=current_user["sub"],
        paciente_id=paciente_id,
        ip_address=request.client.host
    )

    return {
        "historias": result
    }


# --------------------------------
# REGISTRAR ATENCIÓN
# --------------------------------
@router.post("/atencion")
async def medical_attention(
    body: MedicalAttentionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RequireDoctor)
):

    await register_medical_attention(
        db=db,
        medico_id=current_user["sub"],
        paciente_id=body.paciente_id,
        motivo_consulta=body.motivo_consulta,
        examen_fisico=body.examen_fisico,
        diagnostico_principal=body.diagnostico_principal,
        codigo_cie10=body.codigo_cie10,
        plan_tratamiento=body.plan_tratamiento,
        ip_address=request.client.host
    )

    return {
        "message": "Atención médica registrada"
    }


# --------------------------------
# BÚSQUEDA SEGURA
# --------------------------------
@router.post("/busqueda")
async def medical_search(
    body: MedicalSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(RequireDoctor)
):

    result = await secure_medical_search(
        db=db,
        medico_id=current_user["sub"],
        termino=body.termino
    )

    return {
        "resultados": result
    }