"""API route handlers."""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import CalculationResponse, HealthResponse
from app.services.calculator import CalculatorService

router = APIRouter()
calculator_service = CalculatorService()


@router.get("/add", response_model=CalculationResponse)
async def api_add(a: float, b: float) -> CalculationResponse:
    """
    Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        CalculationResponse: Result of the addition operation
    """
    try:
        result = calculator_service.add(a, b)
        return CalculationResponse(operation="add", a=a, b=b, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subtract", response_model=CalculationResponse)
async def api_subtract(a: float, b: float) -> CalculationResponse:
    """
    Subtract two numbers.

    Args:
        a: First number (minuend)
        b: Second number (subtrahend)

    Returns:
        CalculationResponse: Result of the subtraction operation
    """
    try:
        result = calculator_service.subtract(a, b)
        return CalculationResponse(operation="subtract", a=a, b=b, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multiply", response_model=CalculationResponse)
async def api_multiply(a: float, b: float) -> CalculationResponse:
    """
    Multiply two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        CalculationResponse: Result of the multiplication operation
    """
    try:
        result = calculator_service.multiply(a, b)
        return CalculationResponse(operation="multiply", a=a, b=b, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/divide", response_model=CalculationResponse)
async def api_divide(a: float, b: float) -> CalculationResponse:
    """
    Divide two numbers.

    Args:
        a: First number (dividend)
        b: Second number (divisor)

    Returns:
        CalculationResponse: Result of the division operation

    Raises:
        HTTPException: If division by zero is attempted
    """
    try:
        result = calculator_service.divide(a, b)
        return CalculationResponse(operation="divide", a=a, b=b, result=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Service health status
    """
    return HealthResponse(status="healthy", service=settings.service_name)
