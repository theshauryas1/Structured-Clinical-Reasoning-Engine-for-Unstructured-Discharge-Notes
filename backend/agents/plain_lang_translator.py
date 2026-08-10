from typing import Any, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.prompts import ChatPromptTemplate

from backend.agents.chat_agent import call_llm, formulate_report_context, LAYPERSON_DISCLAIMER


class DynamicTranslatorLLM(BaseChatModel):
    """
    LangChain BaseChatModel adapter for plain language translation that routes calls
    through call_llm(), enabling monkeypatch testing support and security gateway fallback.
    """

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        dict_msgs = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                dict_msgs.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                dict_msgs.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                dict_msgs.append({"role": "assistant", "content": msg.content})
            else:
                dict_msgs.append({"role": "user", "content": str(msg.content)})

        response_text = call_llm(dict_msgs)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=response_text))])

    @property
    def _llm_type(self) -> str:
        return "translator_agent_llm"


EXPLAIN_SYSTEM_PROMPT = f"""You are a patient advocate. Your job is to translate a highly technical clinical reasoning report into a simple, patient-friendly summary.

Explain the findings, timeline, and flagged contradictions in clear layperson terms.
- Use simple analogies to explain medical terms or diagnoses.
- Format the output in structured markdown sections:
  1. Patient-Friendly Summary
  2. Simplified Timeline of Events (explain what happened at Admission, Course, and Discharge)
  3. Explanations of any warnings or inconsistencies (contradictions) flagged by our auditors
  4. Diagnosis Breakdowns with clear analogies

You MUST begin your response with the following disclaimer text (on its own line, followed by a double line break):
{LAYPERSON_DISCLAIMER}
"""


def build_translator_chain():

    """
    Builds a LangChain LCEL Runnable chain for plain language translation.
    ChatPromptTemplate | BaseChatModel | StrOutputParser
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", EXPLAIN_SYSTEM_PROMPT),
        ("user", "Please translate and summarize the following patient report context:\n\n{context_str}"),
    ])
    return prompt | DynamicTranslatorLLM() | StrOutputParser()



def generate_plain_language_explanation(report_json: dict) -> str:
    context_str = formulate_report_context(report_json)
    translator_chain = build_translator_chain()
    raw_response = translator_chain.invoke({"context_str": context_str})

    # Enforce disclaimer presence
    if LAYPERSON_DISCLAIMER not in raw_response:
        raw_response = f"{LAYPERSON_DISCLAIMER}\n\n{raw_response}"

    return raw_response

