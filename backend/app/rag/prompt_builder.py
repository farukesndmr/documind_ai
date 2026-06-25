from typing import Sequence


def build_context(chunks: Sequence) -> str:
    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        chunk_id = getattr(chunk, "id", "unknown")
        document_id = getattr(chunk, "document_id", "unknown")
        chunk_index = getattr(chunk, "chunk_index", "unknown")
        content = getattr(chunk, "content", "")

        context_parts.append(
            f"[Kaynak {index} | document_id={document_id} | "
            f"chunk_id={chunk_id} | chunk_index={chunk_index}]\n"
            f"{content}"
        )

    return "\n\n---\n\n".join(context_parts)


def build_summary_prompt(question: str, chunks: Sequence) -> str:
    context = build_context(chunks)

    return f"""
Sen DocuMind AI adlı bir PDF ders asistanısın.

Görevin:
Verilen PDF parçalarına dayanarak öğrencinin sınava çalışabileceği kaliteli bir Türkçe ders notu oluşturmak.

Kesin kurallar:
1. Cevabı Türkçe yaz.
2. İngilizce cümle kurma.
3. Teknik terimler önemliyse Türkçesini yaz, parantez içinde İngilizcesini verebilirsin.
4. PDF parçalarında geçen konulara bağlı kal.
5. Gereksiz motivasyon cümleleri yazma.
6. Tek paragraf yazma.
7. Sınav odaklı ve düzenli anlat.

Cevap formatı:

## 1. Ana Konu
PDF'in genel olarak ne anlattığını açıkla.

## 2. Temel Kavramlar
Önemli kavramları madde madde açıkla.

## 3. Önemli Noktalar
Sınavda sorulabilecek kritik bilgileri yaz.

## 4. Süreç / Mantık
Konu bir süreç anlatıyorsa adım adım açıkla.

## 5. Sınav İçin Bilinmesi Gerekenler
Öğrencinin ezberlemesi veya anlaması gereken noktaları yaz.

## 6. Kısa Genel Özet
Konuyu birkaç cümleyle toparla.

PDF PARÇALARI:
{context}

KULLANICININ İSTEĞİ:
{question}

TÜRKÇE DERS NOTU:
""".strip()


def build_qa_prompt(question: str, chunks: Sequence) -> str:
    context = build_context(chunks)

    return f"""
Sen DocuMind AI adlı bir PDF soru-cevap asistanısın.

Kesin kurallar:
1. Cevabı sadece verilen PDF parçalarına göre ver.
2. PDF parçalarında açıkça bulunmayan bilgileri uydurma.
3. Cevabı Türkçe ver.
4. İngilizce veya başka dilde cümle kurma.
5. Kısa, net ve belgeye dayalı cevap ver.
6. Eğer cevap PDF parçalarında yoksa sadece şunu söyle:
"Bu bilgi dokümanda açıkça bulunmuyor."

PDF PARÇALARI:
{context}

KULLANICININ SORUSU:
{question}

TÜRKÇE CEVAP:
""".strip()


def build_prompt(
    question: str,
    chunks: Sequence,
    mode: str,
) -> str:
    if mode == "summary":
        return build_summary_prompt(
            question=question,
            chunks=chunks,
        )

    return build_qa_prompt(
        question=question,
        chunks=chunks,
    )