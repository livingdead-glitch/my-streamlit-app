"""Offline lifecycle checks; no OpenAI calls or changes to the existing app."""
import io
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from learning_assistant.uploads import document_signature, temporary_pdfs


class UploadTests(unittest.TestCase):
    def test_identity_tracks_content_and_ignores_upload_order(self):
        files = [("a.pdf", b"%PDF-a"), ("b.pdf", b"%PDF-b")]
        self.assertEqual(document_signature(files), document_signature(files[::-1]))
        self.assertNotEqual(document_signature(files), document_signature([("a.pdf", b"%PDF-new")]))
        self.assertIsNone(document_signature([]))

    def test_temporary_paths_exist_only_during_processing(self):
        with temporary_pdfs([("../../same.pdf", b"%PDF-test"), ("same.pdf", b"%PDF-other")]) as paths:
            first, second = [path for _, path in paths]
            self.assertTrue(first.is_file())
            self.assertEqual(first.read_bytes(), b"%PDF-test")
            self.assertNotEqual(first, second)
            self.assertEqual(first.parent, second.parent)
        self.assertFalse(first.exists())

    def test_temporary_paths_removed_on_pipeline_error(self):
        with self.assertRaisesRegex(RuntimeError, "loader failed"):
            with temporary_pdfs([("a.pdf", b"%PDF-test")]) as paths:
                path = paths[0][1]
                raise RuntimeError("loader failed")
        self.assertFalse(path.exists())

    def test_invalid_pdf_rejected(self):
        with self.assertRaises(ValueError):
            with temporary_pdfs([("a.pdf", b"not a pdf")]):
                self.fail("Invalid PDF was accepted")

    def test_total_upload_limit(self):
        with self.assertRaises(ValueError):
            with temporary_pdfs([("large.pdf", b"%PDF-" + b"x" * (30 * 1024 * 1024))]):
                self.fail("Oversized upload was accepted")


class AppLifecycleTests(unittest.TestCase):
    def setUp(self):
        from streamlit.testing.v1 import AppTest
        # Mock the RAG boundary so UI lifecycle checks do not require native DLLs.
        rag = types.ModuleType("learning_assistant.rag")
        rag.build_index = MagicMock()
        rag.build_rag_chain = MagicMock()
        rag.rag_pipeline = MagicMock()
        self.enterContext(patch.dict(sys.modules, {"learning_assistant.rag": rag}))

        self.files = []
        self.stores = []
        self.paths = []
        self.app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30)
        self.enterContext(patch.dict(os.environ, {"OPENAI_API_KEY": ""}))
        self.secrets = {"OPENAI_API_KEY": "offline-test-placeholder"}
        self.enterContext(patch("streamlit.secrets", self.secrets))
        # Streamlit's real streaming renderer also imports native libraries;
        # keep state transitions testable when Windows blocks those DLLs.
        self.render = self.enterContext(patch("streamlit.write_stream", side_effect=lambda stream: "".join(stream)))
        self.enterContext(patch("streamlit.file_uploader", side_effect=lambda *a, **kw: self.files))

        def index(paths, **kwargs):
            self.assertTrue(all(path.is_file() for _, path in paths))
            self.paths.extend(path for _, path in paths)
            store = MagicMock()
            self.stores.append(store)
            return store, 2

        self.index = self.enterContext(patch.object(rag, "build_index", side_effect=index))
        self.chain = self.enterContext(patch.object(rag, "build_rag_chain", side_effect=lambda *a, **kw: (MagicMock(), MagicMock())))
        self.answer = self.enterContext(patch.object(rag, "rag_pipeline", side_effect=lambda *a, **kw: (iter(["Offline answer"]), [])))

    def upload(self, content=b"%PDF-first"):
        upload = io.BytesIO(content)
        upload.name = "lesson.pdf"
        self.files = [upload]

    def run_app(self):
        self.app.run(timeout=20)
        self.assertFalse(self.app.exception)

    def test_questions_reuse_chain_and_replacement_resets_history(self):
        self.upload()
        self.run_app()
        retriever = self.app.session_state.retriever
        chain = self.app.session_state.chain
        self.assertEqual(self.index.call_args.kwargs["api_key"], "offline-test-placeholder")
        self.assertTrue(all(not path.exists() for path in self.paths))
        for question in ["first question", "follow-up"]:
            self.app.chat_input[0].set_value(question).run()
            self.assertFalse(self.app.exception)
        self.assertEqual(self.index.call_count, 1)
        self.assertEqual(self.chain.call_count, 1)
        self.assertEqual(self.answer.call_count, 2)
        for call in self.answer.call_args_list:
            self.assertIs(call.args[0], retriever)
            self.assertIs(call.args[1], chain)
        self.assertEqual(len(self.app.session_state.messages), 4)
        self.upload(b"%PDF-replacement")
        self.run_app()
        self.stores[0].delete_collection.assert_called_once()
        self.assertEqual(self.app.session_state.messages, [])
        self.assertEqual(self.index.call_count, 2)
        self.assertIsNot(self.app.session_state.chain, chain)
        self.files = []
        self.run_app()
        self.assertIsNone(self.app.session_state.chain)
        self.assertIsNone(self.app.session_state.store)
        self.assertTrue(self.app.chat_input[0].disabled)

    def test_failed_replacement_cannot_use_previous_documents(self):
        self.upload()
        self.run_app()
        self.app.chat_input[0].set_value("first").run()
        self.upload(b"invalid")
        self.run_app()
        self.assertIsNone(self.app.session_state.chain)
        self.assertIsNone(self.app.session_state.store)
        self.assertEqual(self.app.session_state.messages, [])
        self.assertTrue(self.app.chat_input[0].disabled)
        self.assertEqual(self.index.call_count, 1)

    def test_missing_key_does_not_build_index(self):
        self.secrets.clear()
        self.upload()
        self.run_app()
        self.index.assert_not_called()
        self.chain.assert_not_called()
        self.assertTrue(self.app.chat_input[0].disabled)

    def test_environment_key_has_priority_over_secrets(self):
        self.upload()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "offline-env-placeholder"}):
            self.run_app()
        self.assertEqual(self.index.call_args.kwargs["api_key"], "offline-env-placeholder")

    def test_clearing_history_keeps_existing_chain(self):
        self.upload()
        self.run_app()
        chain = self.app.session_state.chain
        self.app.chat_input[0].set_value("first").run()
        next(button for button in self.app.button if "대화 기록 삭제" in button.label).click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.session_state.messages, [])
        self.assertIs(self.app.session_state.chain, chain)
        self.assertEqual(self.index.call_count, 1)

    def test_failed_processing_requires_explicit_retry(self):
        self.upload()
        build = self.index.side_effect
        self.index.side_effect = ValueError("offline failure")
        self.run_app()
        self.run_app()
        self.assertEqual(self.index.call_count, 1)
        self.index.side_effect = build
        next(button for button in self.app.button if button.label == "문서 처리 다시 시도").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.index.call_count, 2)
        self.assertIsNotNone(self.app.session_state.chain)


class RagIntegrationTests(unittest.TestCase):
    def test_real_pdf_loader_and_chroma_with_offline_model_substitutes(self):
        import pymupdf
        from langchain_core.embeddings import DeterministicFakeEmbedding
        from langchain_core.runnables import RunnableLambda
        from learning_assistant import rag

        pdf = pymupdf.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "AIVLE learning assistant answers using uploaded course documents.")
        content = pdf.tobytes()
        pdf.close()
        with patch.object(rag, "OpenAIEmbeddings", return_value=DeterministicFakeEmbedding(size=16)):
            with temporary_pdfs([("course.pdf", content)]) as paths:
                store, count = rag.build_index(paths, api_key="offline-test-placeholder")
        try:
            self.assertGreater(count, 0)
            with patch.object(rag, "ChatOpenAI", return_value=RunnableLambda(lambda prompt: "Offline answer")) as llm:
                retriever, chain = rag.build_rag_chain(store, api_key="offline-test-placeholder")
                for question in ["course documents", "learning assistant"]:
                    stream, sources = rag.rag_pipeline(retriever, chain, question, [])
                    self.assertEqual("".join(stream), "Offline answer")
                    self.assertIn("course.pdf", sources[0]["label"])
                llm.assert_called_once()
        finally:
            store.delete_collection()


if __name__ == "__main__":
    unittest.main()
