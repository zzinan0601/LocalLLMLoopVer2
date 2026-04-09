import json
from graph.state import GraphState
from llm.ollama_client import llm
from prompts.templates import (
    DECOMPOSE_PROMPT,
    ANSWER_PROMPT,
    ANSWER_WITH_CONTEXT_PROMPT,
    ANSWER_IMPROVE_PROMPT,
    JUDGE_PROMPT,
    SYNTHESIZE_PROMPT,
)

MAX_LOOP = 3  # 서브질문 당 최대 loop 횟수


# ── 분해 노드 ──────────────────────────────────────────
def decompose_node(state: GraphState) -> GraphState:

    question = state["question"]
    print("\n[분해 노드] 질문을 서브질문으로 분해 중...")

    prompt   = DECOMPOSE_PROMPT.format(question=question)
    response = llm.invoke(prompt)

    # JSON 파싱
    try:
        raw = response.content.strip()
        # 혹시 ```json 블록으로 감싸진 경우 제거
        raw = raw.replace("```json", "").replace("```", "").strip()
        sub_questions = json.loads(raw)
    except Exception:
        # 파싱 실패 시 원본 질문 그대로 1개로 처리
        print("[분해 노드] 파싱 실패 → 원본 질문으로 진행")
        sub_questions = [question]

    print(f"[분해 노드] 서브질문 {len(sub_questions)}개 생성:")
    for i, q in enumerate(sub_questions, 1):
        print(f"  {i}. {q}")

    return {
        **state,
        "sub_questions"  : sub_questions,
        "current_index"  : 0,
        "answers"        : [],
        "context"        : "",
        "current_answer" : "",
        "loop_count"     : 0,
        "is_good"        : False,
    }


# ── 답변 노드 ──────────────────────────────────────────
def answer_node(state: GraphState) -> GraphState:

    sub_questions  = state["sub_questions"]
    current_index  = state["current_index"]
    current_answer = state.get("current_answer", "")
    context        = state.get("context", "")
    loop_count     = state.get("loop_count", 0)

    sub_question = sub_questions[current_index]

    print(f"\n[답변 노드] 서브질문 {current_index + 1}/{len(sub_questions)} | loop {loop_count + 1}회차")
    print(f"  질문: {sub_question}")

    # 프롬프트 선택
    if current_answer:
        # loop 재시도 (이전 답변 개선)
        prompt = ANSWER_IMPROVE_PROMPT.format(
            context        = context,
            sub_question   = sub_question,
            current_answer = current_answer,
        )
    elif context:
        # 이전 서브질문 결과 있음
        prompt = ANSWER_WITH_CONTEXT_PROMPT.format(
            context      = context,
            sub_question = sub_question,
        )
    else:
        # 첫 번째 서브질문, 첫 시도
        prompt = ANSWER_PROMPT.format(sub_question=sub_question)

    response = llm.invoke(prompt)

    return {
        **state,
        "current_answer" : response.content,
        "loop_count"     : loop_count + 1,
    }


# ── 판단 노드 ──────────────────────────────────────────
def judge_node(state: GraphState) -> GraphState:

    sub_questions  = state["sub_questions"]
    current_index  = state["current_index"]
    current_answer = state["current_answer"]
    loop_count     = state["loop_count"]

    sub_question = sub_questions[current_index]

    # 최대 횟수 도달 시 강제 통과
    if loop_count >= MAX_LOOP:
        print(f"[판단 노드] 최대 루프({MAX_LOOP}회) 도달 → 통과")
        return {**state, "is_good": True}

    prompt   = JUDGE_PROMPT.format(
        sub_question   = sub_question,
        current_answer = current_answer,
    )
    response = llm.invoke(prompt)
    result   = response.content.strip().upper()

    is_good = "GOOD" in result
    print(f"[판단 노드] 결과: {result} → {'다음으로' if is_good else 'loop 재시도'}")

    return {**state, "is_good": is_good}


# ── 다음 노드 (서브질문 이동) ──────────────────────────
def next_node(state: GraphState) -> GraphState:

    sub_questions  = state["sub_questions"]
    current_index  = state["current_index"]
    current_answer = state["current_answer"]
    answers        = state.get("answers", [])
    context        = state.get("context", "")

    # 현재 답변 누적
    answers = answers + [current_answer]

    # context 갱신 (다음 서브질문에서 참고)
    sub_question = sub_questions[current_index]
    context = context + f"\nQ{current_index + 1}. {sub_question}\nA{current_index + 1}. {current_answer}\n"

    next_index = current_index + 1
    print(f"\n[다음 노드] {current_index + 1}번 완료 → {next_index + 1 if next_index < len(sub_questions) else '합성 단계'}")

    return {
        **state,
        "answers"        : answers,
        "context"        : context,
        "current_index"  : next_index,
        "current_answer" : "",   # 다음 서브질문을 위해 초기화
        "loop_count"     : 0,    # loop 횟수 초기화
        "is_good"        : False,
    }


# ── 합성 노드 ──────────────────────────────────────────
def synthesize_node(state: GraphState) -> GraphState:

    question      = state["question"]
    sub_questions = state["sub_questions"]
    answers       = state["answers"]

    print("\n[합성 노드] 모든 답변을 하나로 합성 중...")

    # Q&A 쌍 구성
    qa_pairs = ""
    for i, (q, a) in enumerate(zip(sub_questions, answers), 1):
        qa_pairs += f"[서브질문 {i}] {q}\n[답변 {i}] {a}\n\n"

    prompt   = SYNTHESIZE_PROMPT.format(
        question = question,
        qa_pairs = qa_pairs,
    )
    response = llm.invoke(prompt)

    return {**state, "final_answer": response.content}


# ── 분기 함수들 ────────────────────────────────────────
def should_loop(state: GraphState) -> str:
    """판단 후 loop 할지 다음으로 갈지"""
    if state["is_good"]:
        return "next"
    return "answer"

def should_continue(state: GraphState) -> str:
    """다음 서브질문 있으면 계속, 없으면 합성"""
    if state["current_index"] < len(state["sub_questions"]):
        return "answer"
    return "synthesize"
