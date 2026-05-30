from pydantic import BaseModel, Field


class MedicalAttentionRequest(BaseModel):

    paciente_id: int

    motivo_consulta: str = Field(
        min_length=5,
        max_length=3000
    )

    examen_fisico: str = Field(
        min_length=5,
        max_length=3000
    )

    diagnostico_principal: str = Field(
        min_length=3,
        max_length=3000
    )

    codigo_cie10: str = Field(
        min_length=3,
        max_length=20
    )

    plan_tratamiento: str = Field(
        min_length=5,
        max_length=3000
    )


class MedicalSearchRequest(BaseModel):

    termino: str = Field(
        min_length=2,
        max_length=100
    )