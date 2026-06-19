"""
数据模型模块初始化
存放 Pydantic 数据模型定义
"""
from .output_schema import (
    SalesResponse,
    InventoryInfo,
    PricingInfo,
    CaseInfo,
    ProposalInfo,
    ReflectionField,
    ReflectionReport,
    TaskLog,
    TaskPlan,
    ErrorResponse,
    CustomerProfile,
    FollowUpRecord
)

__all__ = [
    "SalesResponse",
    "InventoryInfo",
    "PricingInfo",
    "CaseInfo",
    "ProposalInfo",
    "ReflectionField",
    "ReflectionReport",
    "TaskLog",
    "TaskPlan",
    "ErrorResponse",
    "CustomerProfile",
    "FollowUpRecord"
]