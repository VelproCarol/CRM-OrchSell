"""
企业微信消息通知工具
用于向企业微信用户发送消息通知
"""
import json
import httpx
from typing import Dict, Any, Optional, List
from loguru import logger

from config.settings import settings
from tools.base_tool import BaseTool, ToolResult


class WechatNotifyTool(BaseTool):
    """
    企业微信消息通知工具
    """
    
    def __init__(self):
        """初始化企业微信通知工具"""
        super().__init__(
            tool_name="wechat_notify",
            tool_description="企业微信消息通知工具，用于向指定用户或部门发送消息通知"
        )
        self.access_token = None
        self.token_expire_time = 0
        logger.info("企业微信通知工具初始化完成")
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行企业微信消息通知
        
        Args:
            kwargs: 执行参数
                - message_type: 消息类型（text/textcard/news）
                - message: 消息内容
                - to_user: 接收用户ID（可选，与to_party二选一）
                - to_party: 接收部门ID（可选，与to_user二选一）
                - title: 消息标题（textcard/news类型必填）
                - description: 消息描述（textcard类型）
                - url: 跳转链接（textcard/news类型）
                - articles: 图文消息列表（news类型）
                
        Returns:
            ToolResult: 执行结果
        """
        try:
            # 获取参数
            message_type = kwargs.get("message_type", "text")
            message = kwargs.get("message", "")
            to_user = kwargs.get("to_user", "")
            to_party = kwargs.get("to_party", "")
            title = kwargs.get("title", "")
            description = kwargs.get("description", "")
            url = kwargs.get("url", "")
            articles = kwargs.get("articles", [])
            
            # 验证参数
            if not settings.WECHAT_CORP_ID or not settings.WECHAT_APP_SECRET:
                return ToolResult(
                    success=False,
                    message="企业微信配置未完成，请配置 CORP_ID 和 APP_SECRET",
                    data={}
                )
            
            if not message and not articles:
                return ToolResult(
                    success=False,
                    message="消息内容不能为空",
                    data={}
                )
            
            if not to_user and not to_party:
                return ToolResult(
                    success=False,
                    message="必须指定接收用户或部门",
                    data={}
                )
            
            # 获取 access_token
            token = await self._get_access_token()
            if not token:
                return ToolResult(
                    success=False,
                    message="获取企业微信 access_token 失败",
                    data={}
                )
            
            # 构建消息
            msg_data = self._build_message(
                message_type=message_type,
                message=message,
                title=title,
                description=description,
                url=url,
                articles=articles
            )
            
            # 发送消息
            result = await self._send_message(
                access_token=token,
                to_user=to_user,
                to_party=to_party,
                msg_data=msg_data
            )
            
            if result.get("errcode") == 0:
                logger.info(f"企业微信消息发送成功，用户: {to_user}, 部门: {to_party}")
                return ToolResult(
                    success=True,
                    message="消息发送成功",
                    data={"result": result}
                )
            else:
                logger.error(f"企业微信消息发送失败: {result}")
                return ToolResult(
                    success=False,
                    message=f"消息发送失败: {result.get('errmsg', '未知错误')}",
                    data={"result": result}
                )
                
        except Exception as e:
            logger.error(f"企业微信消息通知执行失败: {str(e)}")
            return ToolResult(
                success=False,
                message=f"执行失败: {str(e)}",
                data={}
            )
    
    async def _get_access_token(self) -> Optional[str]:
        """
        获取企业微信 access_token
        
        Returns:
            access_token，如果失败返回 None
        """
        import time
        
        # 检查缓存的 token 是否过期
        if self.access_token and time.time() < self.token_expire_time:
            return self.access_token
        
        try:
            url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={settings.WECHAT_CORP_ID}&corpsecret={settings.WECHAT_APP_SECRET}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                result = response.json()
                
                if result.get("errcode") == 0:
                    self.access_token = result.get("access_token")
                    self.token_expire_time = time.time() + (result.get("expires_in", 7200) - 60)
                    return self.access_token
                else:
                    logger.error(f"获取 access_token 失败: {result}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取 access_token 异常: {str(e)}")
            return None
    
    def _build_message(
        self,
        message_type: str,
        message: str = "",
        title: str = "",
        description: str = "",
        url: str = "",
        articles: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        构建消息数据
        
        Args:
            message_type: 消息类型
            message: 消息内容
            title: 消息标题
            description: 消息描述
            url: 跳转链接
            articles: 图文消息列表
            
        Returns:
            消息数据字典
        """
        articles = articles or []
        
        if message_type == "textcard":
            return {
                "msgtype": "textcard",
                "textcard": {
                    "title": title,
                    "description": description,
                    "url": url,
                    "btntxt": "详情"
                }
            }
        elif message_type == "news":
            return {
                "msgtype": "news",
                "news": {
                    "articles": articles
                }
            }
        else:
            # 默认 text 类型
            return {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
    
    async def _send_message(
        self,
        access_token: str,
        to_user: str = "",
        to_party: str = "",
        msg_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        发送消息
        
        Args:
            access_token: 访问令牌
            to_user: 接收用户ID
            to_party: 接收部门ID
            msg_data: 消息数据
            
        Returns:
            发送结果
        """
        msg_data = msg_data or {}
        
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        
        data = {
            "agentid": settings.WECHAT_AGENT_ID,
            "msgtype": msg_data.get("msgtype", "text"),
        }
        
        if to_user:
            data["touser"] = to_user
        if to_party:
            data["toparty"] = to_party
        
        # 添加消息内容
        if "text" in msg_data:
            data["text"] = msg_data["text"]
        elif "textcard" in msg_data:
            data["textcard"] = msg_data["textcard"]
        elif "news" in msg_data:
            data["news"] = msg_data["news"]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=data,
                    timeout=10
                )
                return response.json()
        except Exception as e:
            logger.error(f"发送消息异常: {str(e)}")
            return {"errcode": -1, "errmsg": str(e)}
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """
        获取工具的 JSON Schema 定义
        
        Returns:
            工具的 JSON Schema
        """
        return {
            "type": "object",
            "properties": {
                "message_type": {
                    "type": "string",
                    "enum": ["text", "textcard", "news"],
                    "description": "消息类型"
                },
                "message": {
                    "type": "string",
                    "description": "消息内容（text类型必填）"
                },
                "to_user": {
                    "type": "string",
                    "description": "接收用户ID，多个用|分隔"
                },
                "to_party": {
                    "type": "string",
                    "description": "接收部门ID，多个用|分隔"
                },
                "title": {
                    "type": "string",
                    "description": "消息标题（textcard/news类型必填）"
                },
                "description": {
                    "type": "string",
                    "description": "消息描述（textcard类型）"
                },
                "url": {
                    "type": "string",
                    "description": "跳转链接（textcard/news类型）"
                },
                "articles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "url": {"type": "string"},
                            "picurl": {"type": "string"}
                        }
                    },
                    "description": "图文消息列表（news类型）"
                }
            },
            "required": ["message_type"]
        }
