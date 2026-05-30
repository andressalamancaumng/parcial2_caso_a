from fastapi import HTTPException, status

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.security.sanitizer import sanitize_text

from src.security.audit import (
    register_audit_event
)

from src.historias.validation import (
    validate_medical_assignment,
    validate_cie10_code
)


# --------------------------------
# OBTENER HISTORIA CLÍNICA
# --------------------------------
async def get_patient_history(
    db: AsyncSession,
    medico_id: int,
    paciente_id: int,
    ip_address: str
):

    # Paciente consultando su propia historia
    if medico_id != paciente_id:

        await validate_medical_assignment(
            db,
            medico_id,
            paciente_id
        )

    result = await db.execute(
        text("""
            SELECT
                hc.id,
                am.id AS atencion_id,
                am.fecha_atencion,
                am.motivo_consulta,
                am.examen_fisico,
                am.diagnostico_principal,
                am.codigo_cie10,
                am.plan_tratamiento
            FROM historias_clinicas hc
            INNER JOIN atenciones_medicas am
                ON am.historia_id = hc.id
            WHERE hc.paciente_id = :paciente_id
            ORDER BY am.fecha_atencion DESC
        """),
        {
            "paciente_id": paciente_id
        }
    )

    historias = result.fetchall()

    await register_audit_event(
        db=db,
        usuario_id=str(medico_id),
        action="VIEW_MEDICAL_HISTORY",
        result="SUCCESS",
        ip_address=ip_address
    )

    return historias


# --------------------------------
# REGISTRAR ATENCIÓN MÉDICA
# --------------------------------
async def register_medical_attention(
    db: AsyncSession,
    medico_id: int,
    paciente_id: int,
    motivo_consulta: str,
    examen_fisico: str,
    diagnostico_principal: str,
    codigo_cie10: str,
    plan_tratamiento: str,
    ip_address: str
):

    await validate_medical_assignment(
        db,
        medico_id,
        paciente_id
    )

    await validate_cie10_code(
        db,
        codigo_cie10
    )

    historia_result = await db.execute(
        text("""
            SELECT id
            FROM historias_clinicas
            WHERE paciente_id = :paciente_id
            LIMIT 1
        """),
        {
            "paciente_id": paciente_id
        }
    )

    historia = historia_result.fetchone()

    if not historia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Historia clínica no encontrada"
        )

    await db.execute(
        text("""
            INSERT INTO atenciones_medicas
            (
                historia_id,
                medico_id,
                fecha_atencion,
                motivo_consulta,
                examen_fisico,
                diagnostico_principal,
                codigo_cie10,
                plan_tratamiento,
                created_by,
                ip_origen,
                created_at
            )
            VALUES
            (
                :historia_id,
                :medico_id,
                NOW(),
                :motivo_consulta,
                :examen_fisico,
                :diagnostico_principal,
                :codigo_cie10,
                :plan_tratamiento,
                :created_by,
                :ip_origen,
                NOW()
            )
        """),
        {
            "historia_id": historia.id,
            "medico_id": medico_id,
            "motivo_consulta": sanitize_text(motivo_consulta),
            "examen_fisico": sanitize_text(examen_fisico),
            "diagnostico_principal": sanitize_text(diagnostico_principal),
            "codigo_cie10": codigo_cie10,
            "plan_tratamiento": sanitize_text(plan_tratamiento),
            "created_by": medico_id,
            "ip_origen": ip_address
        }
    )

    await db.commit()

    await register_audit_event(
        db=db,
        usuario_id=str(medico_id),
        action="CREATE_MEDICAL_ATTENTION",
        result="SUCCESS",
        ip_address=ip_address
    )


# --------------------------------
# BÚSQUEDA SEGURA
# --------------------------------
async def secure_medical_search(
    db: AsyncSession,
    medico_id: int,
    termino: str
):

    search_term = f"%{sanitize_text(termino)}%"

    result = await db.execute(
        text("""
            SELECT
                p.id,
                u.nombres,
                u.apellidos,
                p.numero_historia
            FROM pacientes p
            INNER JOIN usuarios u
                ON u.id = p.usuario_id
            INNER JOIN asignaciones_medicas am
                ON am.paciente_id = p.id
            WHERE am.medico_id = :medico_id
              AND am.activa = TRUE
              AND (
                    u.nombres ILIKE :search_term
                    OR u.apellidos ILIKE :search_term
                    OR p.numero_historia ILIKE :search_term
              )
            LIMIT 20
        """),
        {
            "medico_id": medico_id,
            "search_term": search_term
        }
    )

    return result.fetchall()