import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import db
import openrouter_client as client


class OpenRouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path_patch = patch.object(db, "DB_PATH", Path(self.tmp.name) / "test.db")
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)
        db.init_db()

    def response(self, content):
        return Mock(json=Mock(return_value={"choices": [{"message": {"content": content}}]}))

    @patch.object(client.requests, "post")
    def test_request_context_and_reset(self, post):
        post.return_value = self.response(" Ответ ")
        with patch.object(client, "OPENROUTER_API_KEY", "test-key"), patch.object(
            client, "OPENROUTER_MODEL", "provider/model"
        ):
            self.assertEqual(client.ask_openrouter(1, "Вопрос"), "Ответ")
            client.ask_openrouter(1, "Уточнение")
        args, kwargs = post.call_args
        self.assertEqual(args[0], client.OPENROUTER_API_URL)
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["json"]["model"], "provider/model")
        messages = kwargs["json"]["messages"]
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual([m["content"] for m in messages[1:]], ["Вопрос", "Ответ", "Уточнение"])
        self.assertEqual(db.get_history(2, 20), [])
        db.delete_history(1)
        self.assertEqual(db.get_history(1, 20), [])

    def test_history_is_bounded_and_persistent(self):
        for i in range(4):
            db.save_turn(1, str(i), f"answer {i}", 2)
        db.init_db()
        self.assertEqual([m["content"] for m in db.get_history(1, 20)][::2], ["2", "3"])

    @patch.object(client.requests, "post")
    def test_empty_or_failed_answers_do_not_change_history(self, post):
        db.save_turn(1, "old", "answer", 20)
        before = db.get_history(1, 20)
        for payload in ({"choices": []}, {"choices": [{"message": {"content": None}}]}):
            post.return_value = Mock(json=Mock(return_value=payload))
            self.assertEqual(client.ask_openrouter(1, "new"), client.EMPTY_ANSWER)
            self.assertEqual(db.get_history(1, 20), before)
        post.return_value = Mock(json=Mock(return_value={"error": {"message": "failure"}}))
        with self.assertRaises(RuntimeError):
            client.ask_openrouter(1, "new")
        post.side_effect = client.requests.Timeout("timeout")
        with self.assertRaises(client.requests.Timeout):
            client.ask_openrouter(1, "new")
        self.assertEqual(db.get_history(1, 20), before)


if __name__ == "__main__":
    unittest.main()
