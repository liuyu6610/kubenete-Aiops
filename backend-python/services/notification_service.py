import logging
import requests
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Send notifications to Feishu (飞书) and DingTalk (钉钉) via Webhook."""

    def __init__(self):
        self.feishu_url = settings.FEISHU_WEBHOOK_URL
        self.dingtalk_url = settings.DINGTALK_WEBHOOK_URL

    def _send_feishu(self, title: str, content_lines: list[dict]) -> bool:
        """Send rich-text card to Feishu group bot."""
        if not self.feishu_url:
            logger.debug("Feishu webhook URL not configured, skipping.")
            return False

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"🛡️ KubeSentinel | {title}"},
                    "template": "blue",
                },
                "elements": [
                    {
                        "tag": "div",
                        "fields": content_lines,
                    }
                ],
            },
        }

        try:
            resp = requests.post(self.feishu_url, json=payload, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                logger.info("Feishu notification sent successfully.")
                return True
            else:
                logger.warning(f"Feishu API returned non-zero code: {result}")
                return False
        except Exception as e:
            logger.error(f"Failed to send Feishu notification: {e}")
            return False

    def _send_dingtalk(self, title: str, text: str) -> bool:
        """Send markdown message to DingTalk group bot."""
        if not self.dingtalk_url:
            logger.debug("DingTalk webhook URL not configured, skipping.")
            return False

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"KubeSentinel | {title}",
                "text": text,
            },
        }

        try:
            resp = requests.post(self.dingtalk_url, json=payload, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            if result.get("errcode") == 0:
                logger.info("DingTalk notification sent successfully.")
                return True
            else:
                logger.warning(f"DingTalk API returned error: {result}")
                return False
        except Exception as e:
            logger.error(f"Failed to send DingTalk notification: {e}")
            return False

    def notify_healing_action(
        self,
        alert_name: str,
        target: str,
        namespace: str,
        action: str,
        confidence: float,
        analysis: str,
        summary: str = "",
        status: str = "已自动执行",
    ):
        """
        Send a healing action notification to all configured channels.
        """
        title = f"自愈告警 - {alert_name}"

        # --- Feishu rich card ---
        feishu_fields = [
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**告警名称：**\n{alert_name}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**故障目标：**\n{target} ({namespace})"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**执行动作：**\n`{action}`"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**AI 置信度：**\n{confidence:.0%}"}},
            {"is_short": False, "text": {"tag": "lark_md", "content": f"**AI 分析：**\n{analysis[:200]}"}},
            {"is_short": False, "text": {"tag": "lark_md", "content": f"**当前状态：**\n{status}"}},
        ]
        self._send_feishu(title, feishu_fields)

        # --- DingTalk markdown ---
        dt_text = (
            f"### 🛡️ KubeSentinel 自愈通知\n\n"
            f"- **告警名称：** {alert_name}\n"
            f"- **故障目标：** {target} ({namespace})\n"
            f"- **执行动作：** `{action}`\n"
            f"- **AI 置信度：** {confidence:.0%}\n"
            f"- **当前状态：** {status}\n\n"
            f"> {analysis[:200]}\n"
        )
        self._send_dingtalk(title, dt_text)

    def notify_approval_needed(
        self,
        alert_name: str,
        target: str,
        namespace: str,
        action: str,
        confidence: float,
        analysis: str,
    ):
        """Send notification that human approval is required."""
        title = f"⚠️ 需要人工审批 - {alert_name}"

        feishu_fields = [
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**告警名称：**\n{alert_name}"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**故障目标：**\n{target} ({namespace})"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**建议动作：**\n`{action}`"}},
            {"is_short": True, "text": {"tag": "lark_md", "content": f"**AI 置信度：**\n{confidence:.0%} (低于阈值)"}},
            {"is_short": False, "text": {"tag": "lark_md", "content": f"**AI 分析：**\n{analysis[:200]}"}},
            {"is_short": False, "text": {"tag": "lark_md", "content": "**请登录 KubeSentinel 控制台进行审批操作**"}},
        ]
        self._send_feishu(title, feishu_fields)

        dt_text = (
            f"### ⚠️ KubeSentinel 需要人工审批\n\n"
            f"- **告警名称：** {alert_name}\n"
            f"- **故障目标：** {target} ({namespace})\n"
            f"- **建议动作：** `{action}`\n"
            f"- **AI 置信度：** {confidence:.0%} (低于阈值)\n\n"
            f"> {analysis[:200]}\n\n"
            f"🔗 请登录 KubeSentinel 控制台进行审批"
        )
        self._send_dingtalk(title, dt_text)
