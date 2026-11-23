from types import SimpleNamespace

from app.rag.prompt_builder import HistoryTurn, build_prompt, language_instruction


def chunk(content, page=None):
    return SimpleNamespace(content=content, page_number=page)


def test_secilen_dil_prompta_yazilir():
    prompt = build_prompt("What is V&V?", [chunk("text", 3)], mode="qa", answer_language="tr")
    assert "Turkish" in prompt
    assert '<source id="1" page="3">' in prompt


def test_auto_dil_sorunun_dilini_kullanir():
    assert "same language as the user's request" in language_instruction("auto")
    assert "same language as the user's request" in language_instruction("xx")


def test_gecmis_prompta_eklenir_ve_kisaltilir():
    history = [HistoryTurn(question="İlk soru", answer="a" * 5000)]
    prompt = build_prompt("peki ikincisi?", [chunk("t")], mode="qa", history=history)
    assert "<conversation>" in prompt
    assert "İlk soru" in prompt
    assert "a" * 1600 not in prompt


def test_gecmis_yoksa_konusma_bolumu_olmaz():
    prompt = build_prompt("soru", [chunk("t")], mode="summary")
    assert "<conversation>" not in prompt
    assert "## 1. Main topic" in prompt


def test_broad_mod_tum_belgeyi_kapsar():
    prompt = build_prompt("Create a quiz", [chunk("t")], mode="broad")
    assert "whole document" in prompt
