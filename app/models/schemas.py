"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field


class CalculationRequest(BaseModel):
    """Request model for calculation operations."""

    a: float = Field(..., description="First number", example=10.0)
    b: float = Field(..., description="Second number", example=5.0)


class CalculationResponse(BaseModel):
    """Response model for calculation operations."""

    operation: str = Field(..., description="The operation performed", example="add")
    a: float = Field(..., description="First number", example=10.0)
    b: float = Field(..., description="Second number", example=5.0)
    result: float = Field(..., description="Result of the calculation", example=15.0)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "operation": "add",
                "a": 10.0,
                "b": 5.0,
                "result": 15.0,
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Health status", example="healthy")
    service: str = Field(..., description="Service name", example="calculator-api")
