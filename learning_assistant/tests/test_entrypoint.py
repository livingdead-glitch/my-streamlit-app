"""Check deployment wiring without Streamlit, native libraries or API calls."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]


class EntrypointTests(unittest.TestCase):
    def test_root_runs_learning_app_on_every_rerun(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8-sig")
        compiled = compile(source, str(ROOT / "app.py"), "exec")
        with patch("runpy.run_path") as run:
            for _ in range(2):
                exec(compiled, {"__file__": str(ROOT / "app.py"), "__name__": "__main__"})
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertEqual(Path(call.args[0]), ROOT / "learning_assistant" / "app.py")
            self.assertEqual(call.kwargs["run_name"], "__main__")

    def test_root_requirements_resolves_learning_dependencies(self):
        lines = [line.strip() for line in (ROOT / "requirements.txt").read_text().splitlines()
                 if line.strip() and not line.startswith("#")]
        self.assertEqual(lines, ["-r learning_assistant/requirements.txt"])
        requirements = ROOT / lines[0][3:]
        self.assertTrue(requirements.is_file())
        self.assertIn("python-dotenv", requirements.read_text())

    def test_application_sources_parse(self):
        for path in [ROOT / "app.py", *(ROOT / "learning_assistant").glob("*.py")]:
            with self.subTest(path=path.name):
                ast.parse(path.read_text(encoding="utf-8-sig"))


if __name__ == "__main__":
    unittest.main()
