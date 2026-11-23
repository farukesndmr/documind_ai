import pytest

from app.documents.pdf_utils import _clean_page_text
from app.documents.text_utils import split_pages_into_chunks, split_text_into_chunks


def test_bos_metin_bos_liste_doner():
    assert split_text_into_chunks("") == []
    assert split_text_into_chunks("   \n  ") == []


def test_kisa_metin_tek_parca():
    assert split_text_into_chunks("kısa metin") == ["kısa metin"]


@pytest.mark.parametrize("size,overlap", [(200, 0), (500, 50), (1000, 150)])
def test_parcalar_boyut_sinirini_asmaz(size, overlap):
    text = ("Agile V&V her sprintte yapılır. " * 50 + "\n\n") * 4
    chunks = split_text_into_chunks(text, chunk_size=size, overlap=overlap)
    assert chunks
    assert all(len(c) <= size for c in chunks)


def test_cumle_ortasindan_bolmez():
    text = "Birinci cümle burada biter. " * 60
    chunks = split_text_into_chunks(text, chunk_size=300, overlap=0)
    assert all(c.endswith(".") for c in chunks)


def test_metnin_basi_ve_sonu_kaybolmaz():
    text = "BAŞ " + "kelime " * 1000 + "SON"
    chunks = split_text_into_chunks(text, chunk_size=500, overlap=50)
    assert chunks[0].startswith("BAŞ")
    assert chunks[-1].endswith("SON")


def test_ardisik_parcalar_ortusur():
    text = " ".join(f"k{i}" for i in range(600))
    chunks = split_text_into_chunks(text, chunk_size=300, overlap=60)
    first_tail_word = chunks[0].split()[-1]
    assert first_tail_word in chunks[1].split()


def test_sayfa_numarasi_korunur():
    chunks = split_pages_into_chunks([(1, "bir. " * 300), (3, "üç")], chunk_size=500)
    assert {c.page_number for c in chunks} == {1, 3}
    assert chunks[-1].content == "üç"


def test_pdf_metni_temizlenir():
    assert _clean_page_text("geliş-\ntirme   süreci\n\n\n\nson") == "geliştirme süreci\n\nson"
