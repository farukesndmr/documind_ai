import ollama

from app.core.config import settings


def build_context_from_chunks(chunks) -> str:
    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[Source {index} | document_id={chunk.document_id} | "
            f"chunk_index={chunk.chunk_index}]\n{chunk.content}"
        )

    return "\n\n".join(context_parts)


def build_fallback_answer(question: str, chunks) -> str:
    if not chunks:
        return "Bu soruyla ilgili dokümanlarda uygun bir bilgi bulunamadı."

    context_preview = "\n\n".join(
        chunk.content for chunk in chunks[:3]
    )

    return (
        "Local AI modeli çalıştırılamadı. "
        "Aşağıda soruyla en alakalı bulunan kaynak parçalar gösteriliyor.\n\n"
        f"Soru: {question}\n\n"
        f"İlgili içerik:\n{context_preview}"
    )


def generate_answer_with_llm(question: str, chunks) -> str:
    if not chunks:
        return "Bu soruyla ilgili dokümanlarda uygun bir bilgi bulunamadı."

    context = build_context_from_chunks(chunks)

    prompt = f"""
Kullanıcının sorusunu sadece verilen kaynak metinlere dayanarak cevapla.

Kurallar:
- Kaynaklarda yoksa "Bu bilgi dokümanda bulunamadı." de.
- Cevabı kısa, net ve anlaşılır yaz.
- Gereksiz tahmin yapma.
- Cevabın sonunda kullandığın source numaralarını belirt.

Kullanıcı sorusu:
{question}

Kaynak metinler:
{context}
"""

    try:
        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Sen kaynaklara bağlı cevap veren bir doküman analiz asistanısın."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response["message"]["content"]

    except Exception as error:
        print(f"Ollama error: {error}")
        return build_fallback_answer(question, chunks)