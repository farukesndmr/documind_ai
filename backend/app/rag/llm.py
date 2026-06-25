import json
import os
import re
import urllib.error
import urllib.request


def get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def clean_answer(answer: str) -> str:
    cleaned = answer.strip()

    cleaned = re.sub(r"^cevap\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^answer\s*:\s*", "", cleaned, flags=re.IGNORECASE)

    # Japonca / Çince karakter karışmasını temizler.
    cleaned = re.sub(
        r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]+",
        "",
        cleaned,
    )

    cleaned = cleaned.strip()

    if not cleaned:
        return "Cevap oluşturulamadı."

    return cleaned


def post_ollama_generate(
    prompt: str,
    mode: str,
) -> str:
    base_url = get_ollama_base_url()
    model = get_ollama_model()

    print(f"Using Ollama model: {model}")
    print(f"RAG answer mode: {mode}")

    if mode == "summary":
        temperature = 0.25
        num_predict = 1000
    else:
        temperature = 0.1
        num_predict = 400

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.85,
            "num_predict": num_predict,
        },
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url=f"{base_url}/api/generate",
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        response_body = response.read().decode("utf-8")
        response_data = json.loads(response_body)

    return clean_answer(response_data.get("response", ""))


def generate_with_llm(
    prompt: str,
    mode: str,
) -> str:
    try:
        return post_ollama_generate(
            prompt=prompt,
            mode=mode,
        )

    except urllib.error.URLError:
        return (
            "Ollama çalışmıyor olabilir. "
            "Lütfen Ollama uygulamasının açık olduğundan emin ol."
        )

    except Exception as error:
        return f"Model cevabı oluşturulurken hata oluştu: {str(error)}"