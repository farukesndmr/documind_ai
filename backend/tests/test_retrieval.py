from types import SimpleNamespace

from app.rag.retriever import keyword_ranking, reciprocal_rank_fusion


def chunk(chunk_id, index, content):
    return SimpleNamespace(id=chunk_id, chunk_index=index, content=content)


def test_rrf_iki_listede_de_olan_one_cikar():
    fused = reciprocal_rank_fusion([1, 2, 3], [3, 4, 1])
    assert fused[0] in {1, 3}
    assert set(fused) == {1, 2, 3, 4}


def test_rrf_bos_listelerle_calisir():
    assert reciprocal_rank_fusion([], []) == []
    assert reciprocal_rank_fusion([5, 6], []) == [5, 6]


def test_anahtar_kelime_siralamasi():
    chunks = [
        chunk(10, 0, "Kahve Etiyopya kökenlidir."),
        chunk(11, 1, "Waterfall modelinde test en sonda yapılır."),
        chunk(12, 2, "Agile yaklaşımında test her sprintte yapılır. Agile esnektir."),
    ]
    ranking = keyword_ranking(chunks, "Agile test nasıl yapılır?")
    assert ranking[0] == 12
    assert 10 not in ranking


def test_anahtar_kelime_yoksa_bos_doner():
    chunks = [chunk(1, 0, "metin")]
    assert keyword_ranking(chunks, "?") == []
