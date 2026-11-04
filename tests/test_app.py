"""외부 API를 호출하지 않는 Streamlit UI 회귀 검사."""
import io
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


class AppTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.client = patch("openai.OpenAI")
        self.factory = self.client.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.client.stop)

    def app(self, with_key=False):
        app = AppTest.from_file(APP)
        app.secrets = {"OPENAI_API_KEY": "unit-test-only"} if with_key else {}
        app.run(timeout=20)
        self.assertFalse(app.exception)
        return app

    def button(self, app, label):
        return next(b for b in app.button if b.label == label)

    def test_dashboard_and_all_menus_without_key(self):
        app = self.app()
        self.assertIn("좋은 하루", app.title[0].value)
        html = "\n".join(m.value for m in app.markdown)
        for title in ["전체 업무", "완료 업무", "진행 중", "마감 임박", "오늘의 AI 업무 브리핑"]:
            self.assertIn(title, html)
        for menu in ["나의 업무", "일정 관리", "음성 비서", "회의록", "설정", "대시보드"]:
            app.sidebar.radio[0].set_value(menu).run()
            self.assertFalse(app.exception, menu)
        self.factory.assert_not_called()

    def test_quick_navigation_and_filter(self):
        app = self.app()
        for label, menu in [("전체 일정 보기 →", "일정 관리"), ("전체 업무 보기 →", "나의 업무"), ("🎙️ 음성 비서", "음성 비서"), ("📄 회의록 업로드", "회의록"), ("＋ 업무 추가", "나의 업무"), ("📅 일정 확인", "일정 관리")]:
            self.button(app, label).click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.sidebar.radio[0].value, menu)
            app.sidebar.radio[0].set_value("대시보드").run()
        app.sidebar.radio[0].set_value("나의 업무").run()
        app.selectbox[0].set_value("완료").run()
        self.assertEqual(len(app.dataframe[0].value), 3)
        self.assertTrue((app.dataframe[0].value["상태"] == "완료").all())

    def test_missing_key_disables_execution(self):
        app = self.app()
        app.sidebar.radio[0].set_value("음성 비서").run()
        self.assertTrue(self.button(app, "실행").disabled)
        self.assertIn("OPENAI_API_KEY", app.info[0].value)
        self.factory.assert_not_called()

    def test_no_audio_does_not_call_api(self):
        app = self.app(with_key=True)
        app.sidebar.radio[0].set_value("음성 비서").run()
        self.button(app, "실행").click().run()
        self.assertIn("녹음", app.warning[0].value)
        self.factory.assert_not_called()

    def test_mocked_voice_multiturn_and_tts_failure(self):
        client = self.factory.return_value.__enter__.return_value
        client.audio.transcriptions.create.return_value.text = "오늘 할 일 알려줘"
        client.responses.create.return_value.output_text = "기획안을 먼저 준비하세요."
        client.audio.speech.create.return_value.content = b"mock-audio"
        with patch("streamlit.audio_input", return_value=io.BytesIO(b"mock-wav")):
            app = self.app(with_key=True)
            app.sidebar.radio[0].set_value("음성 비서").run()
            self.factory.assert_not_called()
            self.button(app, "실행").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state.messages), 2)
            self.assertEqual(app.session_state.speech, b"mock-audio")
            client.audio.transcriptions.create.assert_called_once()
            self.assertEqual(client.responses.create.call_args.kwargs["model"], "gpt-4o-mini")
            for _ in range(5):
                self.button(app, "실행").click().run()
            self.assertEqual(len(app.session_state.messages), 10)
            sent = client.responses.create.call_args.kwargs["input"]
            self.assertEqual(sent[0]["role"], "system")
            self.assertGreater(len(sent), 2)
            client.audio.speech.create.side_effect = RuntimeError("private-error")
            self.button(app, "실행").click().run()
            self.assertFalse(app.exception)
            self.assertIsNone(app.session_state.speech)
            self.assertIn("텍스트", app.warning[0].value)
            self.assertEqual(app.session_state.messages[-1]["role"], "assistant")
            self.button(app, "대화 초기화").click().run()
            self.assertEqual(app.session_state.messages, [])

    def test_meeting_preview_and_invalid_encoding(self):
        with patch("streamlit.file_uploader", return_value=io.BytesIO("회의 내용".encode())):
            app = self.app()
            app.sidebar.radio[0].set_value("회의록").run()
            self.assertEqual(app.text_area[0].value, "회의 내용")
        with patch("streamlit.file_uploader", return_value=io.BytesIO(b"\xff")):
            app.run()
            self.assertFalse(app.exception)
            self.assertIn("UTF-8", app.error[0].value)
        self.factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
