from typing import TypedDict

class GraphState(TypedDict):
    question       : str        # 원본 질문 (불변)
    sub_questions  : list[str]  # 분해된 서브질문 리스트
    current_index  : int        # 현재 처리 중인 서브질문 인덱스
    answers        : list[str]  # 완료된 서브질문 답변 누적
    context        : str        # 이전 답변들을 합친 문자열 (다음 질문에 전달)
    current_answer : str        # 현재 서브질문의 답변 (loop마다 갱신)
    loop_count     : int        # 현재 서브질문의 loop 횟수
    is_good        : bool       # 판단 결과
    final_answer   : str        # 최종 합성 답변
