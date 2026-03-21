import logging
from typing import Dict, Any, List
from uuid import UUID
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.prebuilt import create_react_agent
from sqlalchemy.orm import Session

from app.core.config_manager import config_manager
from app.db.session import SessionLocal
from app.service.agent.tools import get_agent_tools
from app.crud.agent import get_messages_by_session, create_message
from app.schemas.agent import AgentMessageCreate

logger = logging.getLogger(__name__)

def get_session_history(db: Session, session_id: str) -> List[BaseMessage]:
    db_messages = get_messages_by_session(db, session_id, limit=100)
    messages = []
    for msg in db_messages:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))
        elif msg.role == "system":
            messages.append(SystemMessage(content=msg.content))
    return messages


def get_agent_executor(user_id: str, session_id: str, db: Session):
    """
    完全适配 langgraph==1.1.3 的 Agent 初始化
    """
    user_config = config_manager.get_user_config(user_id, db)

    llm_settings = user_config.ai.llm_settings

    if not llm_settings.api_key or not llm_settings.model_name:
        raise ValueError("请先在「设置 -> 基础设置 -> 语言大模型配置」中配置 API Key 和 Model Name。")

    # 初始化 LLM
    llm = ChatOpenAI(
        model=llm_settings.model_name,
        api_key=llm_settings.api_key,
        base_url=llm_settings.base_url if llm_settings.base_url else None,
        temperature=0.7
    )

    # 加载工具列表
    tools = get_agent_tools(user_id)

    # 获取当前时间
    import datetime
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    # 系统提示：通过 PromptTemplate 注入
    system_prompt = f"""你是一个名为 TrailSnap 的智能相册与旅行足迹助手。
今天是 {current_date}。
你的目标是帮助用户回忆他们的旅行、检索相册中的照片，并为他们提供有趣的内容（例如发朋友圈的文案）。
你可以使用提供的工具来搜索照片和出行记录（火车/飞机）。

【重要指令】：如果你需要展示照片给用户，请必须使用 Markdown 图片语法，并且 URL 格式必须为：
`![照片描述](/api/medias/照片ID/thumbnail)`
例如：
`![美丽的风景](/api/medias/123e4567-e89b-12d3-a456-426614174000/thumbnail)`

当你为用户准备了九宫格照片时，请在回答中直接用上述 Markdown 格式输出这 9 张照片。
当用户问“发生了什么事情”或“玩了哪些景点”时，你可以结合照片的描述(description)和一句话旁白(narrative)来丰富你的回答。
请使用友好、自然、有温度的中文与用户交流。
"""

    # 并通过手动构建 prompt 状态传入
    agent = create_react_agent(llm, tools)

    return agent, system_prompt


def chat_with_agent(user_id: str, session_id: str, user_input: str, db: Session) -> str:
    """
    与 Agent 对话，维护上下文历史
    """
    agent, system_prompt = get_agent_executor(user_id, session_id, db)
    messages = get_session_history(db, session_id)
    
    # 将 system_prompt 作为第一条消息传入，如果它不在历史中
    if not messages or not isinstance(messages[0], SystemMessage):
        messages.insert(0, SystemMessage(content=system_prompt))
        
    messages.append(HumanMessage(content=user_input))
    
    # Save user message to DB
    create_message(db, AgentMessageCreate(
        session_id=UUID(session_id),
        role="user",
        content=user_input,
    ))
    
    try:
        response = agent.invoke({"messages": messages})
        
        # 获取大模型的回复
        ai_message = response["messages"][-1].content

        # Save AI message to DB
        create_message(db, AgentMessageCreate(
            session_id=UUID(session_id),
            role="assistant",
            content=ai_message,
        ))

        return ai_message
    except Exception as e:
        logger.error(f"Agent 对话失败：{str(e)}", exc_info=True)
        return f"抱歉，处理你的请求时出错了：{str(e)}，请稍后重试。"
