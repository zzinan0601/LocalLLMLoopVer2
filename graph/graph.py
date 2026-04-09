from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import (
    decompose_node,
    answer_node,
    judge_node,
    next_node,
    synthesize_node,
    should_loop,
    should_continue,
)


def build_graph():

    builder = StateGraph(GraphState)

    # 노드 등록
    builder.add_node("decompose",  decompose_node)
    builder.add_node("answer",     answer_node)
    builder.add_node("judge",      judge_node)
    builder.add_node("next",       next_node)
    builder.add_node("synthesize", synthesize_node)

    # 시작점
    builder.set_entry_point("decompose")

    # 고정 엣지
    builder.add_edge("decompose", "answer")   # 분해 → 첫 답변
    builder.add_edge("answer",    "judge")    # 답변 → 판단

    # 분기 1: 판단 후 → loop 재시도 or 다음 서브질문
    builder.add_conditional_edges(
        "judge",
        should_loop,
        {
            "answer" : "answer",  # BAD  → 답변 노드 (loop)
            "next"   : "next",    # GOOD → 다음 노드
        }
    )

    # 분기 2: 다음 서브질문 있나? → 계속 or 합성
    builder.add_conditional_edges(
        "next",
        should_continue,
        {
            "answer"    : "answer",     # 다음 서브질문 있음
            "synthesize": "synthesize", # 모두 완료 → 합성
        }
    )

    # 합성 → 종료
    builder.add_edge("synthesize", END)

    return builder.compile()
