import json
import os
import re
import urllib.error
import urllib.request
from typing import Sequence


def _get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def _get_configured_model() -> str | None:
    return os.getenv("OLLAMA_MODEL")


def _post_json(url: str, payload: dict, timeout: int = 120) -> dict:
    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
        return json.loads(response_body)


def _get_json(url: str, timeout: int = 10) -> dict:
    request = urllib.request.Request(
        url=url,
        method="GET"
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
        return json.loads(response_body)


def _get_available_ollama_model() -> str:
    configured_model = _get_configured_model()

    if configured_model:
        return configured_model

    base_url = _get_ollama_base_url()

    try:
        data = _get_json(f"{base_url}/api/tags")
        models = data.get("models", [])

        if models:
            return models[0]["name"]
    except Exception:
        pass

    return "llama3.2"


def _clean_answer(answer: str) -> str:
    cleaned = answer.strip()

    cleaned = re.sub(r"^cevap\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^answer\s*:\s*", "", cleaned, flags=re.IGNORECASE)

    # Japonca / Çince karakter karışmasını temizler.
    cleaned = re.sub(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]+", "", cleaned)

    cleaned = cleaned.strip()

    if not cleaned:
        return "Bu bilgi dokümanda açıkça bulunmuyor."

    return cleaned


def _build_context(chunks: Sequence) -> str:
    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        chunk_id = getattr(chunk, "id", "unknown")
        document_id = getattr(chunk, "document_id", "unknown")
        chunk_index = getattr(chunk, "chunk_index", "unknown")
        content = getattr(chunk, "content", "")

        context_parts.append(
            f"[Kaynak {index} | document_id={document_id} | chunk_id={chunk_id} | chunk_index={chunk_index}]\n"
            f"{content}"
        )

    return "\n\n---\n\n".join(context_parts)


def generate_answer_with_llm(question: str, chunks: Sequence) -> str:
    context = _build_context(chunks)

    prompt = f"""
Sen DocuMind AI adlı bir PDF analiz asistanısın.

Aşağıdaki kurallara kesinlikle uy:

1. Cevabı sadece verilen PDF parçalarına göre ver.
2. PDF parçalarında açıkça bulunmayan bilgileri uydurma.
3. Cevabı her zaman Türkçe ver.
4. İngilizce, Japonca veya başka bir dil karıştırma.
5. Gereksiz genel açıklama yapma.
6. Kısa, net ve belgeye dayalı cevap ver.
7. Eğer cevap PDF parçalarında yoksa sadece şunu söyle:
"Bu bilgi dokümanda açıkça bulunmuyor."

PDF PARÇALARI:
{context}

KULLANICININ SORUSU:
{question}

TÜRKÇE CEVAP:
""".strip()

    base_url = _get_ollama_base_url()
    model = _get_available_ollama_model()

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.8,
            "num_predict": 300
        }
    }

    try:
        data = _post_json(
            url=f"{base_url}/api/generate",
            payload=payload
        )

        answer = data.get("response", "")

        return _clean_answer(answer)

    except urllib.error.URLError:
        return "Ollama çalışmıyor olabilir. Lütfen Ollama uygulamasının açık olduğundan emin ol."

    except Exception as error:
        return f"Model cevabı oluşturulurken hata oluştu: {str(error)}"