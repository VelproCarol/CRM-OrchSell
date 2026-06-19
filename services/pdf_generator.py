"""
PDF 生成服务模块
用于生成销售报价单 PDF 文件
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from loguru import logger

from config.settings import settings
from schemas.output_schema import SalesResponse, InventoryInfo, PricingInfo, CustomerProfile


class PdfGenerator:
    """
    PDF 生成器类
    使用 jinja2 + weasyprint 生成报价单 PDF
    """
    
    def __init__(self):
        """初始化 PDF 生成器"""
        try:
            from jinja2 import Environment, FileSystemLoader
            from weasyprint import HTML, CSS
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(Path(__file__).parent.parent / "templates")),
                autoescape=True
            )
            self.HTML = HTML
            self.CSS = CSS
            self._init_templates()
            logger.info("PDF 生成器初始化完成")
        except ImportError as e:
            logger.warning(f"PDF 生成依赖未安装: {e}")
            self.jinja_env = None
    
    def _init_templates(self):
        """初始化模板目录"""
        template_dir = Path(__file__).parent.parent / "templates"
        template_dir.mkdir(exist_ok=True)
        
        # 创建默认模板
        default_template = template_dir / "quote_template.html"
        if not default_template.exists():
            self._create_default_template(default_template)
    
    def _create_default_template(self, template_path: Path):
        """创建默认报价单模板"""
        template_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>销售报价单</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
            @top-center {
                content: "销售报价单";
                font-size: 12px;
                color: #666;
            }
            @bottom-center {
                content: "第 " counter(page) " 页 / 共 " counter(pages) " 页";
                font-size: 10px;
                color: #999;
            }
        }
        
        body {
            font-family: "Microsoft YaHei", "SimHei", sans-serif;
            font-size: 12px;
            line-height: 1.6;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .company-info {
            text-align: right;
            margin-bottom: 20px;
            font-size: 11px;
            color: #666;
        }
        
        .title {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .subtitle {
            font-size: 14px;
            color: #666;
        }
        
        .info-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        .info-table td {
            padding: 8px 12px;
            border: 1px solid #ddd;
            vertical-align: top;
        }
        
        .info-table .label {
            background-color: #f5f5f5;
            font-weight: bold;
            width: 25%;
        }
        
        .product-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        
        .product-table th,
        .product-table td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: center;
        }
        
        .product-table th {
            background-color: #4a90d9;
            color: white;
            font-weight: bold;
        }
        
        .product-table .total-row {
            background-color: #f9f9f9;
            font-weight: bold;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 11px;
            color: #666;
        }
        
        .signature-section {
            display: flex;
            justify-content: space-between;
            margin-top: 60px;
        }
        
        .signature-box {
            width: 45%;
            text-align: center;
            border-top: 1px solid #ddd;
            padding-top: 30px;
        }
        
        .highlight {
            color: #e74c3c;
            font-weight: bold;
        }
        
        .valid-date {
            color: #3498db;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <!-- 公司信息 -->
    <div class="company-info">
        <p>公司名称：{{ company_name }}</p>
        <p>地址：{{ company_address }}</p>
        <p>电话：{{ company_phone }} | 邮箱：{{ company_email }}</p>
    </div>
    
    <!-- 标题 -->
    <div class="header">
        <div class="title">销售报价单</div>
        <div class="subtitle">SALES QUOTATION</div>
    </div>
    
    <!-- 基本信息表格 -->
    <table class="info-table">
        <tr>
            <td class="label">报价单号</td>
            <td>{{ quote_number }}</td>
            <td class="label">报价日期</td>
            <td>{{ quote_date }}</td>
        </tr>
        <tr>
            <td class="label">客户名称</td>
            <td>{{ customer_name }}</td>
            <td class="label">客户ID</td>
            <td>{{ customer_id }}</td>
        </tr>
        <tr>
            <td class="label">联系人</td>
            <td>{{ contact_person }}</td>
            <td class="label">联系电话</td>
            <td>{{ contact_phone }}</td>
        </tr>
        <tr>
            <td class="label">客户等级</td>
            <td>{{ customer_level }}</td>
            <td class="label">信用评级</td>
            <td>{{ credit_rating }}</td>
        </tr>
    </table>
    
    <!-- 产品信息表格 -->
    <table class="product-table">
        <thead>
            <tr>
                <th>产品名称</th>
                <th>产品SKU</th>
                <th>采购数量</th>
                <th>单价（元）</th>
                <th>折扣率</th>
                <th>金额（元）</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>{{ product_name }}</td>
                <td>{{ product_sku }}</td>
                <td>{{ quantity }}</td>
                <td>{{ unit_price }}</td>
                <td>{{ discount_rate }}%</td>
                <td>{{ total_price }}</td>
            </tr>
            <tr class="total-row">
                <td colspan="5">合计金额</td>
                <td class="highlight">{{ total_price }}</td>
            </tr>
        </tbody>
    </table>
    
    <!-- 库存信息 -->
    <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
        <strong>库存保障：</strong>
        <p>当前库存总量：{{ stock_quantity }} 台，可用库存：{{ available_quantity }} 台</p>
        <p>备货周期：{{ lead_time }}</p>
    </div>
    
    <!-- 付款条件 -->
    <div style="margin-top: 20px;">
        <strong>付款条件：</strong> {{ payment_terms }}
    </div>
    
    <!-- 有效期 -->
    <div style="margin-top: 10px;">
        <strong>报价有效期：</strong> <span class="valid-date">{{ valid_until }}</span>
    </div>
    
    <!-- 备注 -->
    <div style="margin-top: 20px;">
        <strong>备注：</strong>
        <p>1. 本报价单仅在有效期内有效</p>
        <p>2. 最终价格以双方签订的合同为准</p>
        <p>3. 如有疑问，请联系销售代表</p>
    </div>
    
    <!-- 签名区域 -->
    <div class="signature-section">
        <div class="signature-box">
            <p>客户签字：_______________</p>
            <p>日期：___________</p>
        </div>
        <div class="signature-box">
            <p>销售代表：_______________</p>
            <p>日期：___________</p>
        </div>
    </div>
    
    <!-- 页脚 -->
    <div class="footer">
        <p style="text-align: center;">感谢您的信任与支持！</p>
    </div>
</body>
</html>
        """
        template_path.write_text(template_content, encoding="utf-8")
    
    def generate_quote_pdf(
        self,
        response: SalesResponse,
        quantity: int = 1,
        quote_number: Optional[str] = None
    ) -> Optional[bytes]:
        """
        生成报价单 PDF
        
        Args:
            response: 销售响应数据
            quantity: 采购数量
            quote_number: 报价单号（可选，自动生成）
            
        Returns:
            PDF 文件字节流，如果生成失败返回 None
        """
        if not self.jinja_env:
            logger.error("PDF 生成依赖未安装")
            return None
        
        try:
            # 生成报价单号
            if not quote_number:
                quote_number = f"QUO-{datetime.now().strftime('%Y%m%d')}-{hash(response.customer_id or '') % 10000:04d}"
            
            # 获取数据
            inventory = response.inventory or InventoryInfo(
                product_name="未知产品",
                stock_quantity=0,
                available_quantity=0,
                lead_time="未知"
            )
            pricing = response.pricing or PricingInfo(
                unit_price=0.0,
                total_price=0.0,
                payment_terms="款到发货"
            )
            customer = response.customer_profile or CustomerProfile(customer_id="")
            
            # 计算总价
            total_price = pricing.unit_price * quantity * (1 - pricing.discount_rate)
            
            # 准备模板数据
            template_data = {
                "company_name": settings.COMPANY_NAME,
                "company_address": settings.COMPANY_ADDRESS,
                "company_phone": settings.COMPANY_PHONE,
                "company_email": settings.COMPANY_EMAIL,
                "quote_number": quote_number,
                "quote_date": datetime.now().strftime("%Y年%m月%d日"),
                "customer_id": customer.customer_id or "未提供",
                "customer_name": customer.customer_name or "未提供",
                "contact_person": customer.contact_person or "未提供",
                "contact_phone": customer.contact_phone or "未提供",
                "customer_level": customer.customer_level or "未评级",
                "credit_rating": customer.credit_rating or "未评级",
                "product_name": inventory.product_name,
                "product_sku": inventory.product_sku or "N/A",
                "quantity": quantity,
                "unit_price": f"{pricing.unit_price:,.2f}",
                "discount_rate": f"{pricing.discount_rate * 100:.1f}",
                "total_price": f"{total_price:,.2f}",
                "stock_quantity": inventory.stock_quantity,
                "available_quantity": inventory.available_quantity,
                "lead_time": inventory.lead_time,
                "payment_terms": pricing.payment_terms,
                "valid_until": pricing.valid_until or (datetime.now().replace(day=1).month % 12 + 1) and datetime.now().strftime("%Y年%m月%d日")
            }
            
            # 渲染模板
            template = self.jinja_env.get_template("quote_template.html")
            html_content = template.render(template_data)
            
            # 生成 PDF
            pdf_bytes = self.HTML(string=html_content).write_pdf()
            
            logger.info(f"报价单 PDF 生成成功: {quote_number}")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"生成报价单 PDF 失败: {str(e)}")
            return None
    
    def save_quote_pdf(
        self,
        response: SalesResponse,
        quantity: int = 1,
        quote_number: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        保存报价单 PDF 到文件
        
        Args:
            response: 销售响应数据
            quantity: 采购数量
            quote_number: 报价单号
            output_path: 输出路径（可选）
            
        Returns:
            保存的文件路径，如果失败返回 None
        """
        pdf_bytes = self.generate_quote_pdf(response, quantity, quote_number)
        
        if not pdf_bytes:
            return None
        
        try:
            if not output_path:
                output_dir = Path(settings.OUTPUT_DIR) / "quotes"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"quote_{quote_number or 'unknown'}.pdf")
            
            Path(output_path).write_bytes(pdf_bytes)
            logger.info(f"报价单已保存: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"保存报价单失败: {str(e)}")
            return None


# 全局 PDF 生成器实例
pdf_generator = PdfGenerator()


def get_pdf_generator() -> PdfGenerator:
    """
    获取 PDF 生成器实例
    
    Returns:
        PDF 生成器实例
    """
    return pdf_generator
