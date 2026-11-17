"""Pure quiz validation tests without model, network or native packages."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from learning_assistant.quiz import validate_quiz


class QuizTests(unittest.TestCase):
    def setUp(self):
        self.sources = [{"label": "course.pdf · 1쪽", "text": "RAG는 검색한 문서를 근거로 답변을 생성합니다."}]
        self.payload = {
            "supported": True, "question": "RAG는 무엇을 근거로 답하나요?",
            "options": ["검색한 문서", "무작위 숫자", "현재 시간", "사용자 이름"],
            "correct_index": 0, "explanation": "문서는 RAG가 검색한 문서를 근거로 답한다고 설명합니다.",
            "evidence": [{"source_index": 1, "quote": "RAG는 검색한 문서를 근거로 답변을 생성합니다."}],
        }

    def test_accepts_four_choices_and_verified_evidence(self):
        result = validate_quiz(self.payload, self.sources)
        self.assertEqual(result["correct_index"], 0)
        self.assertEqual(len(result["options"]), 4)
        self.assertEqual(result["sources"][0]["label"], "course.pdf · 1쪽")

    def test_rejects_missing_grounding(self):
        self.payload["supported"] = False
        with self.assertRaisesRegex(ValueError, "충분한 근거"):
            validate_quiz(self.payload, self.sources)

    def test_rejects_invented_quote_and_source(self):
        for evidence in [
            [{"source_index": 1, "quote": "원문에는 존재하지 않는 만들어 낸 인용입니다."}],
            [{"source_index": 2, "quote": self.sources[0]["text"]}],
            [],
        ]:
            payload = deepcopy(self.payload)
            payload["evidence"] = evidence
            with self.assertRaises(ValueError):
                validate_quiz(payload, self.sources)

    def test_rejects_duplicate_or_missing_choices_and_bad_answer(self):
        for change in [{"options": ["A", "A", "B", "C"]},
                       {"options": ["A", "B", "C"]}, {"correct_index": 4},
                       {"correct_index": True}, {"explanation": ""}]:
            payload = {**self.payload, **change}
            with self.assertRaises(ValueError):
                validate_quiz(payload, self.sources)


if __name__ == "__main__":
    unittest.main()
