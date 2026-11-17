"""Validate generated quiz structure and exact supporting document excerpts."""


def validate_quiz(payload, sources):
    if payload.get("supported") is not True:
        raise ValueError("업로드한 문서에서 문제를 만들 충분한 근거를 확인할 수 없습니다. 주제를 바꿔 주세요.")
    question = payload.get("question", "").strip()
    explanation = payload.get("explanation", "").strip()
    options = payload.get("options", [])
    answer = payload.get("correct_index")
    if (not question or not explanation or not isinstance(options, list)
            or len(options) != 4 or any(not isinstance(o, str) or not o.strip() for o in options)
            or len({o.strip().casefold() for o in options}) != 4
            or type(answer) is not int or not 0 <= answer < 4):
        raise ValueError("올바른 4지선다 문제를 생성하지 못했습니다. 다시 생성해 주세요.")
    evidence = payload.get("evidence", [])
    if not evidence:
        raise ValueError("문제의 문서 근거를 확인하지 못했습니다. 다시 생성해 주세요.")
    verified = []
    for item in evidence:
        index = item.get("source_index")
        quote = item.get("quote", "")
        normalized = " ".join(quote.split())
        if (type(index) is not int or not 1 <= index <= len(sources)
                or len(normalized) < 12
                or normalized not in " ".join(sources[index - 1]["text"].split())):
            raise ValueError("생성된 문제의 인용 근거가 문서와 일치하지 않습니다. 다시 생성해 주세요.")
        verified.append({"label": sources[index - 1]["label"], "text": quote})
    return {"question": question, "options": [o.strip() for o in options],
            "correct_index": answer, "explanation": explanation, "sources": verified}
