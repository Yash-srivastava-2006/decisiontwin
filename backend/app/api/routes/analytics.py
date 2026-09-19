"""Analytics routes for dataset profiling and insights."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.analytics import (
    AnalyticsCollectionResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/datasets", tags=["analytics"])


def get_analytics_service(session: Session = Depends(get_db)) -> AnalyticsService:
    """Return the analytics service for the current request."""
    return AnalyticsService(session)


@router.get(
    "/{dataset_id}/profile",
    response_model=AnalyticsCollectionResponse,
    summary="Generate dataset profile",
    description="Loads the stored CSV and returns high-level profiling metrics for the dataset.",
)
def get_dataset_profile(
    dataset_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsCollectionResponse:
    profile = service.profile_dataset(dataset_id)[2]
    return AnalyticsCollectionResponse(
        message="Dataset profile generated.",
        data=profile,
    )


@router.get(
    "/{dataset_id}/columns",
    response_model=AnalyticsCollectionResponse,
    summary="Profile dataset columns",
    description="Returns inferred metadata for every column in the dataset.",
)
def get_dataset_columns(
    dataset_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsCollectionResponse:
    columns = service.columns_profile(dataset_id)
    return AnalyticsCollectionResponse(
        message="Column profile generated.",
        data=columns,
    )


@router.get(
    "/{dataset_id}/statistics/numeric",
    response_model=AnalyticsCollectionResponse,
    summary="Get numeric statistics",
    description="Calculates descriptive statistics for each numeric column.",
)
def get_numeric_statistics(
    dataset_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsCollectionResponse:
    data = service.numeric_statistics(dataset_id)
    return AnalyticsCollectionResponse(
        message="Numeric statistics generated.",
        data=data,
    )


@router.get(
    "/{dataset_id}/statistics/categorical",
    response_model=AnalyticsCollectionResponse,
    summary="Get categorical statistics",
    description="Calculates frequency-based statistics for each categorical column.",
)
def get_categorical_statistics(
    dataset_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsCollectionResponse:
    data = service.categorical_statistics(dataset_id)
    return AnalyticsCollectionResponse(
        message="Categorical statistics generated.",
        data=data,
    )


@router.get(
    "/{dataset_id}/correlation",
    response_model=AnalyticsCollectionResponse,
    summary="Generate correlation matrix",
    description="Calculates Pearson correlation for numeric columns only.",
)
def get_correlation(
    dataset_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsCollectionResponse:
    data = service.correlation(dataset_id)
    return AnalyticsCollectionResponse(
        message=data.message or "Correlation matrix generated.",
        data=data,
    )


@router.get(
    "/{dataset_id}/quality-warnings",
    response_model=AnalyticsCollectionResponse,
    summary="Get data quality warnings",
    description="Returns deterministic warnings about potential dataset quality issues.",
)
def get_quality_warnings(
    dataset_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsCollectionResponse:
    data = service.data_quality_warnings(dataset_id)
    return AnalyticsCollectionResponse(
        message="Quality warnings generated.",
        data=data,
    )


@router.get(
    "/{dataset_id}/kpis",
    response_model=AnalyticsCollectionResponse,
    summary="Extract business KPIs",
    description="Infers likely business metric columns and derives simple KPIs from them.",
)
def get_kpis(
    dataset_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsCollectionResponse:
    data = service.kpis(dataset_id)
    return AnalyticsCollectionResponse(
        message="Business KPIs generated.",
        data=data,
    )


@router.get(
    "/{dataset_id}/insights",
    response_model=AnalyticsCollectionResponse,
    summary="Generate rule-based insights",
    description="Produces deterministic insights from the dataset without using an LLM.",
)
def get_insights(
    dataset_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsCollectionResponse:
    data = service.insights(dataset_id)
    return AnalyticsCollectionResponse(
        message="Rule-based insights generated.",
        data=data,
    )


@router.get(
    "/{dataset_id}/analytics",
    response_model=AnalyticsCollectionResponse,
    summary="Get unified dataset analytics",
    description="Returns a frontend-friendly payload containing the complete analytics bundle for one dataset.",
)
def get_analytics(
    dataset_id: UUID,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsCollectionResponse:
    data = service.analytics(dataset_id)
    return AnalyticsCollectionResponse(
        message="Dataset analytics generated.",
        data=data,
    )

@router.get('/{dataset_id}/distributions', response_model=AnalyticsCollectionResponse, summary='Get numeric distributions')
def get_distributions(dataset_id: UUID, service: AnalyticsService = Depends(get_analytics_service)) -> AnalyticsCollectionResponse:
    return AnalyticsCollectionResponse(message='Distribution analysis generated.', data=service.distributions(dataset_id))

@router.get('/{dataset_id}/outliers', response_model=AnalyticsCollectionResponse, summary='Detect numeric outliers')
def get_outliers(dataset_id: UUID, service: AnalyticsService = Depends(get_analytics_service)) -> AnalyticsCollectionResponse:
    return AnalyticsCollectionResponse(message='Outlier analysis generated.', data=service.outliers(dataset_id))

@router.get('/{dataset_id}/category-performance', response_model=AnalyticsCollectionResponse, summary='Get category performance')
def get_category_performance(dataset_id: UUID, category_column: str | None = None, metric_column: str | None = None, service: AnalyticsService = Depends(get_analytics_service)) -> AnalyticsCollectionResponse:
    return AnalyticsCollectionResponse(message='Category performance generated.', data=service.category_performance(dataset_id, category_column, metric_column))

@router.get('/{dataset_id}/trends', response_model=AnalyticsCollectionResponse, summary='Get time trend')
def get_trends(dataset_id: UUID, granularity: str = 'monthly', metric_column: str | None = None, service: AnalyticsService = Depends(get_analytics_service)) -> AnalyticsCollectionResponse:
    return AnalyticsCollectionResponse(message='Trend analysis generated.', data=service.trends(dataset_id, granularity, metric_column))

@router.get('/{dataset_id}/rankings', response_model=AnalyticsCollectionResponse, summary='Get category rankings')
def get_rankings(dataset_id: UUID, top_n: int = 10, direction: str = 'top', category_column: str | None = None, metric_column: str | None = None, service: AnalyticsService = Depends(get_analytics_service)) -> AnalyticsCollectionResponse:
    return AnalyticsCollectionResponse(message='Rankings generated.', data=service.rankings(dataset_id, top_n, direction, category_column, metric_column))

@router.get('/{dataset_id}/correlation-pairs', response_model=AnalyticsCollectionResponse, summary='Get ranked correlation pairs')
def get_correlation_pairs(dataset_id: UUID, service: AnalyticsService = Depends(get_analytics_service)) -> AnalyticsCollectionResponse:
    return AnalyticsCollectionResponse(message='Correlation pairs generated.', data=service.correlation_pairs(dataset_id))
