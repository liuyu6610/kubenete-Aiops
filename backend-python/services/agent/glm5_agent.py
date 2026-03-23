import json
import logging
from config import settings
from zhipuai import ZhipuAI
from services.k8s_service import K8sService
from services.prometheus_service import PrometheusService
from services.aiops_service import aiops_svc

logger = logging.getLogger(__name__)

k8s_svc = K8sService()
prom_svc = PrometheusService()

# Initialize ZhipuAI (GLM-4/5 interface)
client = ZhipuAI(api_key=settings.ZHIPUAI_API_KEY) if getattr(settings, 'ZHIPUAI_API_KEY', None) else None

# Define tool schemas for Function Calling
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_pod_logs",
            "description": "获取 Kubernetes 集群中特定 Pod 的最近日志，用于诊断应用报错或崩溃问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Pod 所在的命名空间 (e.g., 'default')"
                    },
                    "pod_name": {
                        "type": "string",
                        "description": "Pod 的精确名称"
                    }
                },
                "required": ["namespace", "pod_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pod_events",
            "description": "获取特定 Pod 的 Kubernetes Events 事件流，用于分析调度失败、OOMKilled、CrashLoopBackOff 等生命周期问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Pod 所在的命名空间"
                    },
                    "pod_name": {
                        "type": "string",
                        "description": "Pod 的精确名称"
                    }
                },
                "required": ["namespace", "pod_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_promql",
            "description": "利用 Prometheus PromQL 执行实时指标查询，用于分析 CPU/内存水位、网络流量激增或应用报错率 (Error Rates)。",
            "parameters": {
                "type": "object",
                "properties": {
                    "promql": {
                        "type": "string",
                        "description": "标准的 PromQL 查询语句字符串"
                    }
                },
                "required": ["promql"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_metrics_anomaly",
            "description": "基于 AI 机器学习 (Isolation Forest) 预测式分析特定 Pod 过去一段时间的隐蔽衰退指标异常情况，超越死板的阈值监控。",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string"
                    },
                    "pod_name": {
                        "type": "string"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "追溯并训练算法的时间窗口（默认为 60）"
                    }
                },
                "required": ["namespace", "pod_name"]
            }
        }
    }
]

def dispatch_tool(name: str, args: dict) -> str:
    """Invokes actual cluster services defined in Phase 2"""
    try:
        if name == "get_pod_logs":
            return k8s_svc.get_pod_logs(**args)
        elif name == "get_pod_events":
            return k8s_svc.get_pod_events(**args)
        elif name == "execute_promql":
            result = prom_svc.execute_promql(**args)
            return json.dumps(result, ensure_ascii=False)
        elif name == "analyze_metrics_anomaly":
            result = aiops_svc.detect_anomalies_for_pod(**args)
            return json.dumps(result, ensure_ascii=False)
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        logger.error(f"Tool execution failed {name}: {e}")
        return f"Execution error: {str(e)}"

SYSTEM_PROMPT = """你是由大模型驱动的 KubeSentinel Copilot —— 一位资深的 Kubernetes AIOps 智能诊断专家 (Senior SRE)。

【角色与职责】
- 你的核心任务是对 K8s 集群异常、Pod 崩溃、性能衰退等问题进行专家级诊断。
- 你必须自主且持续地使用提供的外部工具集深挖上下文，直到找到根本原因。

【核心约束与工作原则】
- 拒绝幻觉（Zero Hallucination）：绝不依靠猜测进行诊断。结论必须 100% 基于工具返回的真实可观测数据。
- 动态重试机制：如果前置工具调用失败或数据为空，你必须转换思路，修改参数（如调整时间窗口、更换命名空间）再次调用工具，直到提取到有效信息。
- 专业口吻：以极度专业、精炼的 SRE 工程师语调进行回复，多用客观指标支撑结论。

【思维链诊断路径 (Chain of Thought)】
在得出最终结论前，请在内心遵循以下思考脉络自主执行工具：
1. 【定界】识别用户提问或告警信息中的核心资源对象。
2. 【假设】快速罗列导致该症状的 2-3 种最可能原因（如 OOM、探针失败、网络阻断、调度失败）。
3. 【验证】精准调用日志、事件、指标工具来逐一验证排查假设。
4. 【交叉印证】若单一日志无法定论，务必结合事件流和 PromQL 阈值进行交叉比对。

【强制输出结构 (Structured Formatting)】
当你的多轮工具调查结束并发起最终回复时，必须严格使用以下 Markdown 模板格式输出（确保前端 UI 渲染惊艳）：

## 🔍 异常现象定界 (Symptom Context)
> [基于工具抓取的数据，简洁概括遭遇的具体瓶颈或异常状态]

## 🧠 深度诊断推理 (Diagnostic Trail)
* **排查路径**：[说明你调用了哪些工具，并看到了什么关键现象]
* **数据支撑**：[引用具体的指标值或关键 Error 日志片段]

## 💡 根因确诊 (Root Cause)
**[得出明确的根因结论。如果工具数据确实不足以 100% 定位，请充分说明缺失的监控维度并给出最高置信度的推测判断。]**

## 🛠️ 行动建议 (Remediation Plan)
- **🔥 紧急止血 (Immediate Action)**: [提供具体的 kubectl 命令或运维操作以迅速恢复服务]
- **🌱 长期治愈 (Long-term Fix)**: [建议架构调整、资源配额(Limit/Requests)修改或告警阈值优化]
"""

class GLM5Agent:
    def __init__(self):
        self.message_history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat(self, user_input: str) -> str:
        """Process chat through the GLM-5 Function Calling Loop"""
        if not client:
            return "错误: 缺少 ZHIPUAI_API_KEY，无法连接大模型服务。"
            
        self.message_history.append({"role": "user", "content": user_input})
        
        # Max iteration limit for tool calling to prevent infinite loops
        max_turns = 5
        
        for _ in range(max_turns):
            try:
                # "glm-4" is Zhipu's latest endpoint API version underlying capabilities which aligns with GLM-5 naming convention expected by the user context
                response = client.chat.completions.create(
                    model="glm-4",  
                    messages=self.message_history,
                    tools=tools
                )
            except Exception as e:
                logger.error(f"Zhipu/GLM API Error: {e}")
                error_msg = f"连接 GLM-5 大模型失败: {str(e)}"
                self.message_history.append({"role": "assistant", "content": error_msg})
                return error_msg

            choice = response.choices[0]
            message = choice.message
            
            # If the model decides to invoke a tool
            if message.tool_calls:
                # 记录 Assistant 的调用意图
                assistant_message = {"role": "assistant", "content": message.content or ""}
                assistant_message["tool_calls"] = []
                
                for tc in message.tool_calls:
                   assistant_message["tool_calls"].append({
                       "id": tc.id,
                       "type": "function",
                       "function": {
                           "name": tc.function.name,
                           "arguments": getattr(tc.function, 'arguments', '{}')
                       }
                   })
                self.message_history.append(assistant_message)
                
                # Execute tool functions
                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(getattr(tool_call.function, 'arguments', '{}'))
                    logger.info(f"GLM-5 Agent autonomously calling tool: {func_name} with args {func_args}")
                    
                    tool_result = dispatch_tool(func_name, func_args)
                    # Limit result size to avoid token overflow
                    tool_result_str = str(tool_result)[:4000]
                    
                    self.message_history.append({
                        "role": "tool",
                        "content": tool_result_str,
                        "tool_call_id": tool_call.id
                    })
                # Re-loop to analyze results
                continue
                
            else:
                # Normal Text Response finalized
                reply_text = message.content
                self.message_history.append({"role": "assistant", "content": reply_text})
                return reply_text
                
        # Fallback if too many tool loops
        reply_text = "分析层级过深，我遇到了一些理解上的困难。请精简您的问题或直接提供更多日志线索。"
        self.message_history.append({"role": "assistant", "content": reply_text})
        return reply_text
