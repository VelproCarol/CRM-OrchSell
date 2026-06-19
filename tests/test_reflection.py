"""
反思验真测试模块
测试反思验真引擎的功能
"""
import pytest
from core.reflection_engine import ReflectionEngine
from core.output_schema import (
    SalesResponse,
    InventoryInfo,
    PricingInfo,
    CaseInfo,
    ReflectionReport
)
from config.settings import Constants


@pytest.mark.asyncio
class TestReflectionEngine:
    """
    反思验真引擎测试
    """
    
    async def test_verify_inventory(self):
        """
        测试库存信息验证
        """
        engine = ReflectionEngine()
        
        # 创建响应
        response = SalesResponse(
            status="success",
            inventory=InventoryInfo(
                product_name="工业风机",
                stock_quantity=120,
                available_quantity=50,
                lead_time="7天"
            )
        )
        
        # 创建上下文（真实数据）
        context = {
            Constants.TASK_INVENTORY_QUERY: {
                "product_name": "工业风机",
                "stock_quantity": 120,
                "available_quantity": 50
            }
        }
        
        # 执行验证
        report = await engine.verify(response, context)
        
        assert report.enabled is True
        assert report.overall_confidence > 0
        assert "stock_quantity" in report.verified_fields
    
    async def test_verify_pricing(self):
        """
        测试价格信息验证
        """
        engine = ReflectionEngine()
        
        # 创建响应
        response = SalesResponse(
            status="success",
            pricing=PricingInfo(
                unit_price=8500.0,
                total_price=425000.0,
                discount_rate=0.05,
                payment_terms="30天账期"
            )
        )
        
        # 创建上下文
        context = {
            Constants.TASK_PRICE_QUERY: {
                "unit_price": 8500.0,
                "discount_rate": 0.05
            }
        }
        
        # 执行验证
        report = await engine.verify(response, context)
        
        assert report.enabled is True
        assert "unit_price" in report.verified_fields
    
    async def test_verify_cases(self):
        """
        测试案例信息验证
        """
        engine = ReflectionEngine()
        
        # 创建响应
        response = SalesResponse(
            status="success",
            cases=[
                CaseInfo(
                    case_id="CASE-2024-001",
                    quantity=55,
                    deal_price=8200.0,
                    payment_terms="30天账期"
                )
            ]
        )
        
        # 创建上下文
        context = {
            Constants.TASK_CASE_RETRIEVAL: {
                "cases": [
                    {
                        "case_id": "CASE-2024-001",
                        "quantity": 55,
                        "deal_price": 8200.0
                    }
                ]
            }
        }
        
        # 执行验证
        report = await engine.verify(response, context)
        
        assert report.enabled is True
        assert len(report.verified_fields) > 0
    
    async def test_detect_hallucination(self):
        """
        测试幻觉检测
        """
        engine = ReflectionEngine()
        
        # 创建响应（包含错误数据）
        response = SalesResponse(
            status="success",
            inventory=InventoryInfo(
                product_name="工业风机",
                stock_quantity=999,  # 错误的库存数量
                available_quantity=50,
                lead_time="7天"
            )
        )
        
        # 创建上下文（真实数据）
        context = {
            Constants.TASK_INVENTORY_QUERY: {
                "product_name": "工业风机",
                "stock_quantity": 120,  # 真实库存
                "available_quantity": 50
            }
        }
        
        # 执行验证
        report = await engine.verify(response, context)
        
        assert report.enabled is True
        assert len(report.hallucinations_detected) > 0
        assert "stock_quantity" in report.unverified_fields
    
    async def test_disabled_reflection(self):
        """
        测试禁用反思验真
        """
        from config.settings import settings
        
        # 临时禁用反思验真
        original_enabled = settings.REFLECTION_ENABLED
        settings.REFLECTION_ENABLED = False
        
        engine = ReflectionEngine()
        
        response = SalesResponse(status="success")
        
        report = await engine.verify(response)
        
        assert report.enabled is False
        
        # 恢复设置
        settings.REFLECTION_ENABLED = original_enabled
    
    async def test_missing_context(self):
        """
        测试缺少上下文数据
        """
        engine = ReflectionEngine()
        
        # 创建响应
        response = SalesResponse(
            status="success",
            inventory=InventoryInfo(
                product_name="工业风机",
                stock_quantity=120,
                available_quantity=50,
                lead_time="7天"
            )
        )
        
        # 无上下文
        report = await engine.verify(response)
        
        assert report.enabled is True
        assert len(report.warnings) > 0
    
    async def test_confidence_threshold(self):
        """
        测试置信度阈值
        """
        engine = ReflectionEngine()
        
        # 创建响应（部分数据正确）
        response = SalesResponse(
            status="success",
            inventory=InventoryInfo(
                product_name="工业风机",
                stock_quantity=120,  # 正确
                available_quantity=50,  # 正确
                lead_time="7天"
            ),
            pricing=PricingInfo(
                unit_price=99999.0,  # 错误
                total_price=425000.0,
                discount_rate=0.05,
                payment_terms="30天账期"
            )
        )
        
        # 创建上下文
        context = {
            Constants.TASK_INVENTORY_QUERY: {
                "stock_quantity": 120,
                "available_quantity": 50
            },
            Constants.TASK_PRICE_QUERY: {
                "unit_price": 8500.0  # 真实价格
            }
        }
        
        # 执行验证
        report = await engine.verify(response, context)
        
        assert report.overall_confidence < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])