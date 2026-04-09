from graph.graph import build_graph

def main():
    graph = build_graph()

    question = input("질문을 입력하세요: ")

    initial_state = {
        "question"       : question,
        "sub_questions"  : [],
        "current_index"  : 0,
        "answers"        : [],
        "context"        : "",
        "current_answer" : "",
        "loop_count"     : 0,
        "is_good"        : False,
        "final_answer"   : "",
    }

    print("\n" + "="*50)

    # 답변 노드와 합성 노드 토큰만 실시간 출력
    current_node = None

    for token, metadata in graph.stream(initial_state, stream_mode="messages"):

        node = metadata.get("langgraph_node")

        # 노드 전환 시 헤더 출력
        if node != current_node:
            current_node = node
            if node == "answer":
                print(f"\n[답변 생성 중...]\n")
            elif node == "synthesize":
                print(f"\n[최종 합성 중...]\n")

        # 답변/합성 노드 토큰 실시간 출력
        if node in ("answer", "synthesize"):
            print(token.content, end="", flush=True)

    print("\n" + "="*50)
    print("\n✅ 완료")


if __name__ == "__main__":
    main()
