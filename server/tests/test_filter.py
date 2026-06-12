import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import llm as srv  # noqa: E402


def _user(text):
    return srv.UserMessage(role="user", content=text)


def test_moderate_flags_banned_passes_clean():
    assert srv.moderate("I really like apples") is True
    assert srv.moderate("I really like strawberries") is False


def test_filter_redacts_only_offending_sentence():
    text = "Sure, I can help. You said: strawberries. Is there anything else?"
    assert srv.filter_reply(text) == "Sure, I can help. Content filtered. Is there anything else?"


def test_run_agent_turn_redacts_echoed_banned_term():
    out = srv.run_agent_turn([_user("tell me about strawberries")])
    assert "Content filtered." in out
    assert "strawberries" not in out


def test_run_agent_turn_passes_clean_input():
    out = srv.run_agent_turn([_user("tell me about apples")])
    assert "Content filtered." not in out
    assert "apples" in out
