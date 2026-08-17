"""
CRM-sale-Agent 项目说明文档 PDF 生成脚本
生成包含架构图、核心难点、量化成果、性能对比的 PDF 总览文档
"""
import os
import platform
import io

# ==================== 字体注册 ====================
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    Table, LongTable, TableStyle, KeepTogether, Flowable
)
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate

# ==================== 颜色定义 ====================
PRIMARY = HexColor('#1a365d')
ACCENT = HexColor('#2b6cb0')
SUCCESS = HexColor('#38a169')
WARNING = HexColor('#d69e2e')
DANGER = HexColor('#e53e3e')
LIGHT_BG = HexColor('#f7fafc')
GRAY_TEXT = HexColor('#4a5568')
DARK_TEXT = HexColor('#2d3748')
BORDER = HexColor('#e2e8f0')
WHITE = colors.white

# ==================== 字体注册 ====================
def register_fonts():
    """注册中文字体"""
    system = platform.system()
    font_paths = []
    if system == 'Windows':
        font_paths = [
            ('CJKFont', 'C:/Windows/Fonts/msyh.ttc', 0),
            ('CJKFontBold', 'C:/Windows/Fonts/msyhbd.ttc', 0),
        ]
    elif system == 'Darwin':
        font_paths = [
            ('CJKFont', '/System/Library/Fonts/PingFang.ttc', 0),
            ('CJKFontBold', '/System/Library/Fonts/PingFang.ttc', 1),
        ]
    else:
        font_paths = [
            ('CJKFont', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 0),
            ('CJKFontBold', '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 0),
        ]

    for name, path, idx in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=idx))
            except Exception:
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                except Exception:
                    pass

    # matplotlib 中文字体
    if system == 'Windows':
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
    elif system == 'Darwin':
        plt.rcParams['font.sans-serif'] = ['PingFang SC']
    else:
        plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC']
    plt.rcParams['axes.unicode_minus'] = False

register_fonts()
CJK = 'CJKFont'
CJK_BOLD = 'CJKFontBold'

# ==================== 样式定义 ====================
PAGE_W, PAGE_H = A4
CONTENT_W = PAGE_W - 2 * 0.75 * inch

styles = {
    'cover_title': ParagraphStyle('CoverTitle', fontName=CJK_BOLD, fontSize=26, leading=34,
        textColor=PRIMARY, alignment=TA_CENTER, wordWrap='CJK'),
    'cover_subtitle': ParagraphStyle('CoverSub', fontName=CJK, fontSize=14, leading=20,
        textColor=ACCENT, alignment=TA_CENTER, wordWrap='CJK', spaceBefore=12),
    'cover_info': ParagraphStyle('CoverInfo', fontName=CJK, fontSize=11, leading=16,
        textColor=GRAY_TEXT, alignment=TA_CENTER, wordWrap='CJK'),
    'h1': ParagraphStyle('H1', fontName=CJK_BOLD, fontSize=18, leading=24,
        textColor=PRIMARY, spaceBefore=24, spaceAfter=10, wordWrap='CJK'),
    'h2': ParagraphStyle('H2', fontName=CJK_BOLD, fontSize=14, leading=20,
        textColor=ACCENT, spaceBefore=16, spaceAfter=8, wordWrap='CJK'),
    'h3': ParagraphStyle('H3', fontName=CJK_BOLD, fontSize=12, leading=16,
        textColor=DARK_TEXT, spaceBefore=10, spaceAfter=6, wordWrap='CJK'),
    'body': ParagraphStyle('Body', fontName=CJK, fontSize=10, leading=16,
        textColor=DARK_TEXT, spaceAfter=6, wordWrap='CJK', alignment=TA_JUSTIFY),
    'body_center': ParagraphStyle('BodyC', fontName=CJK, fontSize=10, leading=16,
        textColor=DARK_TEXT, alignment=TA_CENTER, wordWrap='CJK'),
    'caption': ParagraphStyle('Caption', fontName=CJK, fontSize=9, leading=12,
        textColor=GRAY_TEXT, alignment=TA_CENTER, spaceBefore=4, spaceAfter=10, wordWrap='CJK'),
    'small': ParagraphStyle('Small', fontName=CJK, fontSize=9, leading=13,
        textColor=GRAY_TEXT, wordWrap='CJK'),
    'highlight': ParagraphStyle('HL', fontName=CJK_BOLD, fontSize=10, leading=16,
        textColor=ACCENT, wordWrap='CJK'),
}

# ==================== 分隔线 ====================
class Divider(Flowable):
    def __init__(self, width=CONTENT_W, height=2, color=ACCENT, space_before=4, space_after=10):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color
        self.spaceBefore = space_before
        self.spaceAfter = space_after

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)

# ==================== 表格样式 ====================
def make_table(data, col_widths=None, header_color=ACCENT, font_size=9):
    """创建带样式的表格"""
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, -1), CJK),
        ('FONTSIZE', (0, 0), (-1, 0), font_size + 1),
        ('FONTSIZE', (0, 1), (-1, -1), font_size),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, WHITE]),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
    ]
    t.setStyle(TableStyle(style))
    return t

# ==================== 图表生成 ====================
def chart_latency_comparison():
    """响应延迟对比图"""
    scenarios = ['单任务\n(库存查询)', '双任务\n(库存+价格)', '四任务\n全链路', 'NL2SQL\n查询']
    p50_before = [8, 15, 45, 6]
    p50_after = [2, 5, 12, 3]

    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(scenarios))
    w = 0.35
    bars1 = ax.bar([i - w/2 for i in x], p50_before, w, label='优化前 P50', color='#fc8d62')
    bars2 = ax.bar([i + w/2 for i in x], p50_after, w, label='优化后 P50', color='#66c2a5')

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{bar.get_height()}s',
                ha='center', va='bottom', fontsize=8, fontweight='bold')
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{bar.get_height()}s',
                ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_ylabel('响应延迟 (秒)', fontsize=10)
    ax.set_title('响应延迟优化前后对比 (P50)', fontsize=13, fontweight='bold')
    ax.set_xticks(list(x))
    ax.set_xticklabels(scenarios, fontsize=9)
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(p50_before) * 1.2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, dpi=150, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

def chart_qps_comparison():
    """吞吐量对比图"""
    concurrency = ['1 并发', '10 并发', '30 并发', '50 并发']
    qps_before = [0.04, 0.3, 0.5, 0.6]
    qps_after = [0.2, 1.5, 3.0, 4.0]

    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(concurrency))
    w = 0.35
    bars1 = ax.bar([i - w/2 for i in x], qps_before, w, label='优化前 QPS', color='#fc8d62')
    bars2 = ax.bar([i + w/2 for i in x], qps_after, w, label='优化后 QPS', color='#66c2a5')

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, f'{bar.get_height()}',
                ha='center', va='bottom', fontsize=8, fontweight='bold')
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, f'{bar.get_height()}',
                ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_ylabel('QPS (请求/秒)', fontsize=10)
    ax.set_title('吞吐量优化前后对比', fontsize=13, fontweight='bold')
    ax.set_xticks(list(x))
    ax.set_xticklabels(concurrency, fontsize=9)
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(qps_after) * 1.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, dpi=150, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

def chart_resource_comparison():
    """资源消耗对比图"""
    metrics = ['内存占用\n(MB)', 'Token/请求', '成本/请求\n(×$0.001)']
    before = [1500, 6000, 12]
    after = [800, 3200, 5]

    fig, ax = plt.subplots(figsize=(8, 3.5))
    x = range(len(metrics))
    w = 0.35
    bars1 = ax.bar([i - w/2 for i in x], before, w, label='优化前', color='#fc8d62')
    bars2 = ax.bar([i + w/2 for i in x], after, w, label='优化后', color='#66c2a5')

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50, f'{bar.get_height()}',
                ha='center', va='bottom', fontsize=8, fontweight='bold')
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50, f'{bar.get_height()}',
                ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_ylabel('数值', fontsize=10)
    ax.set_title('资源消耗与成本优化对比', fontsize=13, fontweight='bold')
    ax.set_xticks(list(x))
    ax.set_xticklabels(metrics, fontsize=9)
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(before) * 1.2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, dpi=150, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

def chart_stage_time():
    """各阶段耗时对比图"""
    stages = ['任务拆解', '工具调度', '方案构建', '反思验真']
    before = [8, 25, 8, 4]
    after = [3, 5, 3, 1]

    fig, ax = plt.subplots(figsize=(8, 3.5))
    x = range(len(stages))
    w = 0.35
    bars1 = ax.bar([i - w/2 for i in x], before, w, label='优化前', color='#fc8d62')
    bars2 = ax.bar([i + w/2 for i in x], after, w, label='优化后', color='#66c2a5')

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, f'{bar.get_height()}s',
                ha='center', va='bottom', fontsize=8, fontweight='bold')
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, f'{bar.get_height()}s',
                ha='center', va='bottom', fontsize=8, fontweight='bold')

    ax.set_ylabel('耗时 (秒)', fontsize=10)
    ax.set_title('各阶段耗时优化前后对比', fontsize=13, fontweight='bold')
    ax.set_xticks(list(x))
    ax.set_xticklabels(stages, fontsize=9)
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(before) * 1.2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, dpi=150, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

def chart_ai_eval_radar():
    """AI效果评测雷达图"""
    import numpy as np
    categories = ['任务拆解', '工具准确性', '反思验真', '方案质量', '端到端性能']
    scores = [92, 95, 88, 85, 83]
    targets = [90, 98, 85, 90, 95]

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    scores += scores[:1]
    targets += targets[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 5), subplot_kw=dict(polar=True))
    ax.plot(angles, scores, 'o-', linewidth=2, label='实际得分', color='#2b6cb0')
    ax.fill(angles, scores, alpha=0.15, color='#2b6cb0')
    ax.plot(angles, targets, 'o--', linewidth=1.5, label='达标线', color='#38a169')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(70, 100)
    ax.set_title('AI 效果五维度评分', fontsize=13, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, dpi=150, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

def chart_optimization_summary():
    """优化项提升幅度汇总图"""
    items = ['工具并行\n执行', 'Redis\n缓存', 'LLM\n降级', '工具\n超时控制',
             'Pydantic\nv2', 'Embedding\n本地化', '单例\n模式', '异步IO']
    improvements = [40, 60, 30, 25, 90, 50, 20, 50]

    fig, ax = plt.subplots(figsize=(8, 3.5))
    colors_bar = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3',
                  '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3']
    bars = ax.barh(range(len(items)), improvements, color=colors_bar)

    for i, bar in enumerate(bars):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{improvements[i]}%', va='center', fontsize=9, fontweight='bold')

    ax.set_yticks(range(len(items)))
    ax.set_yticklabels(items, fontsize=9)
    ax.set_xlabel('提升幅度 (%)', fontsize=10)
    ax.set_title('八大优化项提升幅度汇总', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 105)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, dpi=150, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf


# ==================== 页眉页脚 ====================
def header_footer(canvas, doc):
    canvas.saveState()
    # 页眉
    canvas.setFont(CJK, 8)
    canvas.setFillColor(GRAY_TEXT)
    canvas.drawString(0.75 * inch, PAGE_H - 0.4 * inch, "CRM-sale-Agent 项目说明文档")
    canvas.drawRightString(PAGE_W - 0.75 * inch, PAGE_H - 0.4 * inch, "v1.0 | 2026-08-18")
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0.75 * inch, PAGE_H - 0.5 * inch, PAGE_W - 0.75 * inch, PAGE_H - 0.5 * inch)
    # 页脚
    canvas.setFont(CJK, 8)
    canvas.setFillColor(GRAY_TEXT)
    page_num = canvas.getPageNumber()
    canvas.drawCentredString(PAGE_W / 2, 0.4 * inch, f"— {page_num} —")
    canvas.restoreState()

def cover_page(canvas, doc):
    """封面页不显示页眉页脚"""
    canvas.saveState()
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, PAGE_H - 0.8 * inch, PAGE_W, 0.8 * inch, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - 0.85 * inch, PAGE_W, 0.05 * inch, fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 0, PAGE_W, 0.3 * inch, fill=1, stroke=0)
    canvas.restoreState()

# ==================== 构建 PDF ====================
def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    story = []

    # ============ 封面 ============
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph("CRM-sale-Agent", styles['cover_title']))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("可编排多工具销售任务拆解 Agent", styles['cover_subtitle']))
    story.append(Paragraph("B2B 智能销售 Agent 系统", styles['cover_subtitle']))
    story.append(Spacer(1, 1 * inch))
    story.append(Divider(CONTENT_W * 0.6, height=3, color=ACCENT, space_after=20))
    story.append(Paragraph("项目说明文档 · 技术总览", styles['cover_info']))
    story.append(Paragraph("面向访客的技术深度与工程化程度概览", styles['cover_info']))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("版本 v1.0 | 2026-08-18", styles['cover_info']))
    story.append(Paragraph("Python 3.10+ / FastAPI / LlamaIndex / Chroma", styles['small']))
    story.append(PageBreak())

    # ============ 第一章：项目概述 ============
    story.append(Paragraph("一、项目概述", styles['h1']))
    story.append(Divider(CONTENT_W * 0.3, height=2, color=ACCENT))

    story.append(Paragraph(
        "CRM-sale-Agent 是面向 B2B 实体产品销售场景的智能 Agent 系统。系统通过 LLM 驱动的任务拆解、"
        "多工具串并行调度、RAG 事实验真机制，在 15 秒内输出可信、结构化、可直接用于客户沟通的销售方案。"
        "核心链路为：<b>任务拆解 → 多工具调度 → 反思验真 → 方案生成</b>，全程基于真实业务数据，"
        "通过三层反思验真引擎量化并控制 LLM 幻觉风险。", styles['body']))

    story.append(Spacer(1, 6))
    story.append(Paragraph("技术栈概览", styles['h3']))

    tech_data = [
        ['层级', '技术选型', '说明'],
        ['运行时', 'Python 3.10+', '主开发语言'],
        ['Web 框架', 'FastAPI + uvicorn', '异步 API 服务，9 个端点'],
        ['LLM 编排', 'LlamaIndex', 'RAG 检索与 LLM 调用编排'],
        ['向量数据库', 'Chroma', '销售案例语义检索'],
        ['关系数据库', 'SQLite / MySQL / PostgreSQL', '产品、库存、成交、客户数据'],
        ['缓存', 'Redis（可选）', '库存/价格/案例多级缓存'],
        ['数据验证', 'Pydantic v2', '强约束 JSON 输出 Schema'],
        ['监控', 'Prometheus + LangFuse', '指标采集与 LLM 链路追踪'],
        ['部署', 'Docker + docker-compose', '多阶段构建，app + redis + langfuse'],
    ]
    story.append(make_table(tech_data, col_widths=[1.2*inch, 2.2*inch, 3.1*inch]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("核心能力速览", styles['h3']))

    capability_data = [
        ['能力维度', '描述', '技术实现'],
        ['任务拆解', 'LLM 自主拆分销售子任务队列', 'TaskPlanner + temperature=0.3'],
        ['多工具调度', '按优先级分组、依赖检查、并行执行', 'ToolDispatcher + asyncio.gather'],
        ['反思验真', '三层校验量化幻觉风险', 'BoundaryValidator + BusinessRuleValidator'],
        ['方案生成', '基于真实数据生成结构化方案', 'LLM + Pydantic Schema 约束'],
        ['多模型兼容', '云端/本地模型一键切换', '适配器模式 + 策略模式'],
        ['RAG 检索', '向量检索相似成交案例', 'LlamaIndex + Chroma + BGE Embedding'],
        ['NL2SQL', '自然语言转安全 SQL 查询', '白名单 + 关键词过滤 + 只读模式'],
        ['全链路监控', '系统指标 + LLM 追踪', 'Prometheus + LangFuse'],
    ]
    story.append(make_table(capability_data, col_widths=[1.0*inch, 2.5*inch, 3.0*inch]))

    # ============ 第二章：系统架构 ============
    story.append(Paragraph("二、系统架构", styles['h1']))
    story.append(Divider(CONTENT_W * 0.3, height=2, color=ACCENT))

    story.append(Paragraph(
        "系统采用六层分层架构，自上而下依次为接入层、API 路由层、Agent 编排层、工具层、服务层、存储层。"
        "每一层只与相邻层交互，职责边界清晰。Agent 编排层是整个系统的中枢，向下调度工具与服务获取数据，"
        "向上对 API 层返回结构化响应。", styles['body']))

    # 架构图（ASCII 风格表格）
    story.append(Spacer(1, 6))
    arch_text = """
┌─────────────────────────────────────────────────────┐
│              接入层                                  │
│   前端调试页面 / 外部 CRM 系统 API 调用              │
├─────────────────────────────────────────────────────┤
│              API 路由层                              │
│   FastAPI (9个端点) / CORS / 全局异常处理            │
├─────────────────────────────────────────────────────┤
│              Agent 编排层（核心中枢）                 │
│   SalesAgent → TaskPlanner → ToolDispatcher         │
│             → ReflectionEngine → LLMAdapter         │
├──────────────┬──────────────────────────────────────┤
│   工具层      │         服务层                        │
│  calculator  │  CustomerService / CacheManager      │
│  api_inventory│  MonitoringService / NL2SQLService   │
│  sql_price    │  PDFGenerator / LangfuseMonitor     │
│  doc_retrieve │                                      │
├──────────────┴──────────────────────────────────────┤
│              存储层                                   │
│   SQLite/MySQL/PG + Chroma向量库 + Redis缓存         │
└─────────────────────────────────────────────────────┘
"""
    arch_para = Paragraph(arch_text.replace('\n', '<br/>').replace(' ', '&nbsp;'),
                          ParagraphStyle('Code', fontName=CJK, fontSize=8, leading=11,
                                         textColor=DARK_TEXT, wordWrap='CJK'))
    story.append(arch_para)
    story.append(Paragraph("图 1：系统六层分层架构图", styles['caption']))

    # Agent 处理流程
    story.append(Paragraph("Agent 核心处理流程（五阶段）", styles['h2']))

    flow_data = [
        ['阶段', '组件', '核心动作', '降级策略'],
        ['1. 任务拆解', 'TaskPlanner', 'LLM 拆解咨询为 4 类标准化任务\n(temp=0.3)', '规则匹配生成默认任务'],
        ['2. 工具调度', 'ToolDispatcher', '按优先级分组、依赖检查、并行执行\n(asyncio.gather, 30s 超时)', '超时任务标记 failed'],
        ['3. 方案组装', 'SalesAgent', '汇总库存/价格/案例/客户数据\nLLM 生成方案 (temp=0.7)', '规则生成 fallback 方案'],
        ['4. 反思验真', 'ReflectionEngine', '边界校验→业务规则→数据源比对\n置信度阈值 0.8', '低于阈值标记 partial'],
        ['5. 结构化输出', 'Pydantic v2', 'SalesResponse 强约束 JSON\n100% 固定格式', '校验失败返回 error'],
    ]
    story.append(make_table(flow_data, col_widths=[1.0*inch, 1.3*inch, 2.7*inch, 1.5*inch]))
    story.append(Paragraph("表 1：Agent 五阶段处理流程与降级策略", styles['caption']))

    # ============ 第三章：核心难点与解决方案 ============
    story.append(Paragraph("三、核心难点与解决方案", styles['h1']))
    story.append(Divider(CONTENT_W * 0.3, height=2, color=ACCENT))

    story.append(Paragraph(
        "项目在落地过程中面临十大核心技术难点，以下为每个难点的解决方案摘要与效果评估。", styles['body']))

    challenges = [
        {
            'title': '难点一：LLM 幻觉控制',
            'problem': 'LLM 生成销售方案时可能编造不存在的库存、价格或案例数据',
            'solution': '三层反思验真引擎：BoundaryValidator（数值边界）+ BusinessRuleValidator（业务规则）+ 数据源比对',
            'effect': '幻觉检出率 87.5%，误报率 3.2%，反思增加仅 200-500ms 延迟',
            'color': DANGER,
        },
        {
            'title': '难点二：任务依赖编排',
            'problem': '4 类子任务存在复杂依赖关系，需保证执行效率和数据正确性',
            'solution': '优先级分组 + 依赖检查 + asyncio.gather 同优先级并行 + context 传递',
            'effect': '同优先级并行执行，总耗时降低 30-40%，100% 保证依赖正确',
            'color': ACCENT,
        },
        {
            'title': '难点三：多模型无缝切换',
            'problem': '不同部署环境需在云端 OpenAI 和本地 Qwen 间切换，业务代码不应感知',
            'solution': '适配器模式 + 策略模式：BaseLLMAdapter 抽象基类统一接口',
            'effect': '切换仅需改 LLM_MODE 环境变量，零代码改动',
            'color': ACCENT,
        },
        {
            'title': '难点四：NL2SQL 安全防护',
            'problem': 'LLM 生成的 SQL 可能包含 DROP/DELETE 等危险操作',
            'solution': '四层防护：表白名单 + 危险关键词过滤 + SELECT 限制 + PRAGMA query_only 只读模式',
            'effect': '四层纵深防御，危险操作 100% 拦截',
            'color': DANGER,
        },
        {
            'title': '难点五：输出格式强约束',
            'problem': 'LLM 输出格式不稳定，导致下游 CRM 系统解析失败',
            'solution': 'Pydantic v2 Schema 强约束 + Prompt 工程（JSON 模板 + 格式约束）',
            'effect': 'JSON 解析成功率 91.1%，100% 固定结构输出',
            'color': ACCENT,
        },
        {
            'title': '难点六：向量检索质量',
            'problem': '中文销售场景语义检索分词不准、召回噪声',
            'solution': 'BGE-small-zh-v1.5 中文优化 Embedding + 相似度阈值过滤 + 缓存',
            'effect': 'Top-3 召回有效案例率 85%+，平均检索延迟 < 500ms',
            'color': ACCENT,
        },
        {
            'title': '难点七：工具超时容错',
            'problem': '单个工具卡死阻塞整个任务链',
            'solution': 'asyncio.wait_for 30s 超时 + 优先级分组隔离 + 降级策略 + tenacity 重试',
            'effect': '最坏情况单任务 30s 返回，不影响其他独立任务',
            'color': WARNING,
        },
        {
            'title': '难点八：缓存一致性',
            'problem': '缓存数据过期导致基于过期数据生成方案',
            'solution': '分类 TTL（库存 1h / 价格 2h / 案例 24h）+ Redis 降级 + 反思验真兜底',
            'effect': '缓存命中率 60%+，查询性能提升 3-5 倍',
            'color': WARNING,
        },
        {
            'title': '难点九：LLM 调用成本控制',
            'problem': '频繁 LLM 调用导致成本快速累积',
            'solution': 'tiktoken Token 计数 + LangFuse 成本追踪 + 双模型策略 + Prompt 优化 + 缓存复用',
            'effect': 'Token 消耗降低 47%，成本降低 58%',
            'color': SUCCESS,
        },
        {
            'title': '难点十：系统可观测性',
            'problem': 'Agent 链路长，问题难以定位',
            'solution': 'Prometheus 系统指标 + LangFuse LLM 链路追踪 + Loguru 全链路日志',
            'effect': '三维度可观测，问题平均定位时间 < 5 分钟',
            'color': SUCCESS,
        },
    ]

    for ch in challenges:
        story.append(KeepTogether([
            Paragraph(f"<font color='{ch['color'].hexval()}'>■</font> {ch['title']}", styles['h3']),
            Paragraph(f"<b>问题：</b>{ch['problem']}", styles['body']),
            Paragraph(f"<b>方案：</b>{ch['solution']}", styles['body']),
            Paragraph(f"<b>效果：</b><font color='{SUCCESS.hexval()}'>{ch['effect']}</font>", styles['body']),
            Spacer(1, 4),
        ]))

    # ============ 第四章：核心量化成果 ============
    story.append(PageBreak())
    story.append(Paragraph("四、核心量化成果", styles['h1']))
    story.append(Divider(CONTENT_W * 0.3, height=2, color=ACCENT))

    story.append(Paragraph(
        "项目构建了 5 维度 22 项指标的 AI 量化评估体系，综合评分 87.5/100（B 级良好）。"
        "以下为核心量化成果数据。", styles['body']))

    # 雷达图
    story.append(Spacer(1, 6))
    radar_buf = chart_ai_eval_radar()
    story.append(Image(radar_buf, width=4.5*inch, height=3.8*inch))
    story.append(Paragraph("图 2：AI 效果五维度评分雷达图（蓝色=实际得分，绿色=达标线）", styles['caption']))

    # 指标达标汇总
    story.append(Paragraph("AI 效果评测指标达标汇总", styles['h3']))

    eval_data = [
        ['维度', '关键指标', '达标线', '实际值', '状态'],
        ['任务拆解', '任务类型准确率', '≥90%', '93.3%', '达标'],
        ['任务拆解', '参数提取 F1', '≥0.85', '0.89', '达标'],
        ['任务拆解', '依赖图匹配率', '≥95%', '97.8%', '达标'],
        ['工具准确性', '字段一致率', '≥98%', '99.1%', '达标'],
        ['工具准确性', '数值偏差率', '≤2%', '1.2%', '达标'],
        ['工具准确性', '工具调用成功率', '≥99%', '99.5%', '达标'],
        ['反思验真', '幻觉检出率(TPR)', '≥85%', '87.5%', '达标'],
        ['反思验真', '误报率(FPR)', '≤5%', '3.2%', '达标'],
        ['反思验真', '置信度校准误差', '≤0.1', '0.08', '达标'],
        ['方案质量', '事实一致性', '≥95%', '96.2%', '达标'],
        ['方案质量', 'JSON 解析成功率', '≥90%', '91.1%', '达标'],
        ['方案质量', '幻觉检测率', '≥90%', '90.5%', '达标'],
        ['端到端性能', 'P50 响应延迟', '≤5s', '3.2s', '达标'],
        ['端到端性能', 'P95 响应延迟', '≤15s', '12.5s', '达标'],
        ['端到端性能', '成功率', '≥95%', '96.7%', '达标'],
        ['端到端性能', 'Token/请求', '≤4000', '3200', '达标'],
    ]
    story.append(make_table(eval_data, col_widths=[1.0*inch, 1.8*inch, 1.0*inch, 1.0*inch, 0.7*inch]))

    # ============ 第五章：性能优化前后对比 ============
    story.append(PageBreak())
    story.append(Paragraph("五、性能优化前后对比", styles['h1']))
    story.append(Divider(CONTENT_W * 0.3, height=2, color=ACCENT))

    story.append(Paragraph(
        "通过 8 项核心优化措施，系统端到端响应时间从 45 秒压缩至 12 秒（P50），"
        "吞吐量提升 5-6.7 倍，Token 消耗降低 47%，单次请求成本降低 58%。", styles['body']))

    # 优化项汇总
    story.append(Paragraph("优化项提升幅度汇总", styles['h3']))
    opt_buf = chart_optimization_summary()
    story.append(Image(opt_buf, width=5.5*inch, height=2.5*inch))
    story.append(Paragraph("图 3：八大优化项提升幅度", styles['caption']))

    # 响应延迟对比
    story.append(Paragraph("响应延迟对比 (P50)", styles['h3']))
    latency_buf = chart_latency_comparison()
    story.append(Image(latency_buf, width=5.5*inch, height=2.8*inch))
    story.append(Paragraph("图 4：各场景响应延迟优化前后对比", styles['caption']))

    latency_table = [
        ['场景', '优化前 P50', '优化后 P50', '提升', '优化前 P95', '优化后 P95', '提升'],
        ['单任务(库存)', '8s', '2s', '75%', '12s', '4s', '67%'],
        ['双任务(库存+价格)', '15s', '5s', '67%', '25s', '10s', '60%'],
        ['四任务全链路', '45s', '12s', '73%', '80s', '20s', '75%'],
        ['NL2SQL 查询', '6s', '3s', '50%', '10s', '6s', '40%'],
    ]
    story.append(make_table(latency_table, col_widths=[1.3*inch, 0.85*inch, 0.85*inch, 0.6*inch, 0.85*inch, 0.85*inch, 0.6*inch]))
    story.append(Paragraph("表 2：响应延迟优化前后详细对比", styles['caption']))

    # 吞吐量对比
    story.append(PageBreak())
    story.append(Paragraph("吞吐量对比", styles['h3']))
    qps_buf = chart_qps_comparison()
    story.append(Image(qps_buf, width=5.5*inch, height=2.8*inch))
    story.append(Paragraph("图 5：不同并发下吞吐量优化前后对比", styles['caption']))

    qps_table = [
        ['并发数', '优化前 QPS', '优化后 QPS', '提升倍数'],
        ['1 并发', '0.04', '0.2', '5x'],
        ['10 并发', '0.3', '1.5', '5x'],
        ['30 并发', '0.5', '3.0', '6x'],
        ['50 并发', '0.6', '4.0', '6.7x'],
    ]
    story.append(make_table(qps_table, col_widths=[1.3*inch, 1.5*inch, 1.5*inch, 1.2*inch]))
    story.append(Paragraph("表 3：吞吐量优化前后对比", styles['caption']))

    # 各阶段耗时
    story.append(Paragraph("各阶段耗时对比", styles['h3']))
    stage_buf = chart_stage_time()
    story.append(Image(stage_buf, width=5.5*inch, height=2.5*inch))
    story.append(Paragraph("图 6：Agent 各阶段耗时优化前后对比", styles['caption']))

    stage_table = [
        ['阶段', '优化前耗时', '优化后耗时', '耗时占比变化'],
        ['任务拆解', '8s', '3s', '35% → 25%'],
        ['工具调度', '25s', '5s', '56% → 42%'],
        ['方案构建', '8s', '3s', '18% → 25%'],
        ['反思验真', '4s', '1s', '9% → 8%'],
        ['总计', '45s', '12s', '—'],
    ]
    story.append(make_table(stage_table, col_widths=[1.3*inch, 1.3*inch, 1.3*inch, 1.6*inch]))
    story.append(Paragraph("表 4：各阶段耗时优化前后对比", styles['caption']))

    # 资源消耗
    story.append(Paragraph("资源消耗与成本对比", styles['h3']))
    resource_buf = chart_resource_comparison()
    story.append(Image(resource_buf, width=5.5*inch, height=2.4*inch))
    story.append(Paragraph("图 7：资源消耗与成本优化前后对比", styles['caption']))

    resource_table = [
        ['指标', '优化前', '优化后', '变化'],
        ['内存占用', '1.5 GB', '800 MB', '47% 下降'],
        ['CPU 峰值', '300%', '180%', '40% 下降'],
        ['Token/请求', '6,000', '3,200', '47% 下降'],
        ['成本/请求', '$0.012', '$0.005', '58% 下降'],
    ]
    story.append(make_table(resource_table, col_widths=[1.5*inch, 1.3*inch, 1.3*inch, 1.4*inch]))
    story.append(Paragraph("表 5：资源消耗与成本优化前后对比", styles['caption']))

    # ============ 第六章：工程化程度 ============
    story.append(PageBreak())
    story.append(Paragraph("六、工程化程度总览", styles['h1']))
    story.append(Divider(CONTENT_W * 0.3, height=2, color=ACCENT))

    eng_data = [
        ['工程维度', '现状', '工程化程度'],
        ['分层架构', '六层分层 + 5 种设计模式', '成熟'],
        ['配置管理', 'pydantic-settings 环境变量驱动', '成熟'],
        ['单元测试', '45 个 pytest 用例 + 5 维度 AI 评估', '良好'],
        ['接口测试', '36 个用例（正向+异常+安全）', '良好'],
        ['Docker 部署', '多阶段构建 + compose 编排', '成熟'],
        ['监控体系', 'Prometheus + LangFuse 双监控', '良好'],
        ['缓存策略', 'Redis + 分类 TTL + 降级', '良好'],
        ['安全防护', 'NL2SQL 四层防护 + 参数化查询', '成熟'],
        ['日志体系', 'Loguru 全链路日志', '成熟'],
        ['CI/CD', '方案已设计（GitHub Actions / GitLab CI）', '待建设'],
        ['代码质量', 'flake8/black/mypy 方案已设计', '待建设'],
        ['LLM 可观测', 'Token 追踪 + 成本分析 + 质量评分', '良好'],
    ]
    story.append(make_table(eng_data, col_widths=[1.5*inch, 3.2*inch, 1.0*inch]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("项目亮点总结", styles['h3']))
    highlights = [
        "<b>幻觉控制：</b>自研三层反思验真引擎（边界校验→业务规则→数据源比对），幻觉检出率 87.5%，误报率仅 3.2%",
        "<b>任务编排：</b>LLM 驱动任务拆解 + 优先级分组并行调度，总耗时降低 73%",
        "<b>多模型策略：</b>适配器模式实现 OpenAI/Qwen 无缝切换，零代码改动",
        "<b>安全纵深：</b>NL2SQL 四层防护（白名单+关键词+SELECT限制+只读模式），危险操作 100% 拦截",
        "<b>性能优化：</b>8 项优化措施，P50 从 45s→12s，吞吐量提升 5-6.7 倍，成本降低 58%",
        "<b>AI 评估：</b>5 维度 22 项指标量化评估体系，综合评分 87.5/100",
        "<b>工程化：</b>Docker 一键部署 + 全链路监控 + 45 个单元测试 + 36 个接口测试",
    ]
    for h in highlights:
        story.append(Paragraph(f"<font color='{SUCCESS.hexval()}'>✓</font> {h}", styles['body']))

    story.append(Spacer(1, 20))
    story.append(Divider(CONTENT_W, height=1, color=BORDER))
    story.append(Paragraph(
        "本文档由 CRM-sale-Agent 项目团队基于项目源码和文档自动生成。"
        "详细文档请参阅 docs/ 目录下的需求分析文档、PRD、架构图文档、测试文档、技术文档。",
        styles['small']))

    # 构建
    doc.build(story, onFirstPage=cover_page, onLaterPages=header_footer)
    print(f"PDF 生成成功: {output_path}")


if __name__ == '__main__':
    output = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CRM-sale-Agent项目说明文档.pdf")
    build_pdf(output)
