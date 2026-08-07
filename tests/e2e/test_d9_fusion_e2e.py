"""F8 -- Test suite fusi end-to-end (D9). Lewat `client` fixture (SQLite seed,
tests/conftest.py) + model AI/PBPK ASLI -- inferensi nyata, bukan mock, hanya
lookup DB yang di-seed.
"""
from app.core.config import settings


def _payload(hepatwin_id: str, dosis_mg: float, usia=40, jk="L", berat=70.0, tinggi=168.0) -> dict:
    return {
        "hepatwin_id": hepatwin_id,
        "dosis_mg": dosis_mg,
        "covariates": {"usia": usia, "jenis_kelamin": jk, "berat_badan_kg": berat, "tinggi_badan_cm": tinggi},
    }


def test_acetaminophen_overdose_is_red(client):
    """Test #4 (F8): Parasetamol/Acetaminophen -> MERAH sesuai PRD UC-02
    (Skenario A: overdosis akut 4000mg, 40th, L, 70kg, 168cm). MERAH tercapai
    lewat HIGH_EXPOSURE (dose_per_kg=57.1 >= 30) terlepas dari band AI --
    konsisten dgn F2 (reports/F2_penurunan_ambang.md)."""
    resp = client.post("/api/v1/simulate", json=_payload("HT-001", 4000.0))
    assert resp.status_code == 200
    data = resp.json()
    assert data["visual_color"] == "red"
    assert data["risk_level"] == "high"
    assert data["exposure_category"] == "HIGH_EXPOSURE"


def test_vno_safe_compound_reaches_green_end_to_end(client):
    """Test #5 (F8, diperbarui R3 utk Mesin A v2.3): senyawa vNo-DILI-concern
    (Calcitonin salmon, skor terendah katalog nyata F1) pada dosis wajar utk
    pasien dewasa sehat HARUS menghasilkan HIJAU lewat PIPELINE PENUH (AI + PBPK
    v2.3 + exposure_evaluator v2.3 + fusi) -- bukan lagi hanya pembuktian
    struktural (unit test injeksi band).

    RIWAYAT: di siklus v2.1 (`exposure_evaluator` berbasis `cmax_auc_ratio`,
    lihat `reports/_v21_archive/F2_exposure_reachability_finding.md`),
    skenario IDENTIK ini menghasilkan `HIGH_EXPOSURE` -- LOW_EXPOSURE praktis
    tidak terjangkau (0/20.250 kombinasi realistis). Upgrade Mesin A ke v2.3
    (`exposure_index` berbasis magnitude, bukan rasio) memperbaiki ini --
    dibuktikan ulang scr empiris di R2 (`reports/R2_exposure_reachability_v23.md`,
    43.41% kombinasi kini LOW_EXPOSURE) dan R3 (`reports/R3_uji_acuan_v23.md`,
    pipeline penuh)."""
    resp = client.post("/api/v1/simulate", json=_payload("HT-VNO-SAFE-TEST", 50.0, usia=25, jk="P", berat=60.0, tinggi=165.0))
    assert resp.status_code == 200
    data = resp.json()
    assert data["dili_score"] < settings.FUSION_AI_T_LOW, (
        f"dili_score={data['dili_score']} seharusnya < T_low={settings.FUSION_AI_T_LOW} utk senyawa vNo skor terendah"
    )
    assert data["exposure_category"] == "LOW_EXPOSURE"
    assert data["visual_color"] == "green"
    assert data["risk_level"] == "low"
    assert data["fusion_reason"] == "AI_LOW x LOW_EXPOSURE"


def test_is_simulatable_false_rejected(client):
    """Test #6 (F8): senyawa is_simulatable=FALSE ditolak, tidak masuk fusi
    (DoD D9). Cakupan penuh 10 biologik ada di
    tests/security/test_is_simulatable_enforcement.py -- ini verifikasi ringan
    langsung dari sudut pandang D9."""
    resp = client.post("/api/v1/simulate", json=_payload("HT-BIOLOGIC-001", 100.0))
    assert resp.status_code == 422


def test_hepatoseluler_maps_to_focal_high_intensity(client):
    """Test #7 (F8): injury_pattern=Hepatoseluler -> segmen V,VI,VII,VIII + focal + high."""
    resp = client.post("/api/v1/simulate", json=_payload("HT-HEPATOSELULER-TEST", 500.0))
    assert resp.status_code == 200
    data = resp.json()
    assert data["injury_pattern"] == "Hepatoseluler"
    assert data["affected_segments"] == ["V", "VI", "VII", "VIII"]
    assert data["hotspot_intensity"] == "high"
    assert data["hotspot_display_mode"] == "focal"
    assert data["evidence_note"] is None


def test_unclassified_falls_back_to_diffuse_dim_with_evidence_note(client):
    """Test #8 (F8): injury_pattern=Tidak Terklasifikasi -> 8 segmen + diffuse
    + dim + evidence_note terisi (fallback antihalusinasi, PRD Bab 6.6/8.3)."""
    resp = client.post("/api/v1/simulate", json=_payload("HT-VNO-SAFE-TEST", 50.0))
    assert resp.status_code == 200
    data = resp.json()
    assert data["injury_pattern"] == "Tidak Terklasifikasi"
    assert data["affected_segments"] == ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
    assert data["hotspot_intensity"] == "dim"
    assert data["hotspot_display_mode"] == "diffuse"
    assert data["evidence_note"] is not None
    assert "belum tersedia" in data["evidence_note"]


def test_hotspot_intensity_does_not_influence_color(client):
    """Test #9 (F8): dua senyawa dgn SMILES IDENTIK (dili_score dijamin sama,
    model deterministik) & kovariat/dosis identik (exposure_category dijamin
    sama, F2) tapi injury_pattern/intensitas BEDA -> visual_color/risk_level/
    blinking_speed HARUS SAMA, hotspot_intensity/mode HARUS BEDA. Membuktikan
    pemisahan tanggung jawab SS4.3: warna <- fusi, intensitas <- lookup DB,
    keduanya independen."""
    payload_kwargs = dict(dosis_mg=800.0, usia=50, jk="L", berat=80.0, tinggi=175.0)
    resp_a = client.post("/api/v1/simulate", json=_payload("HT-HEPATOSELULER-TEST", **payload_kwargs))
    resp_b = client.post("/api/v1/simulate", json=_payload("HT-UNCLASSIFIED-SAME-SMILES", **payload_kwargs))
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    a, b = resp_a.json(), resp_b.json()

    assert a["dili_score"] == b["dili_score"], "SMILES identik harus menghasilkan dili_score identik"
    assert a["visual_color"] == b["visual_color"]
    assert a["risk_level"] == b["risk_level"]
    assert a["blinking_speed"] == b["blinking_speed"]
    assert a["fusion_reason"] == b["fusion_reason"]

    assert a["hotspot_intensity"] != b["hotspot_intensity"]
    assert a["hotspot_display_mode"] != b["hotspot_display_mode"]
    assert a["hotspot_intensity"] == "high" and b["hotspot_intensity"] == "dim"
    assert a["hotspot_display_mode"] == "focal" and b["hotspot_display_mode"] == "diffuse"


def test_reproducibility_identical_requests_give_identical_responses(client):
    """Test #10 (F8): dua panggilan identik -> respons identik (deterministik,
    tidak ada state tersembunyi/acak)."""
    payload = _payload("HT-001", 1000.0)
    resp1 = client.post("/api/v1/simulate", json=payload)
    resp2 = client.post("/api/v1/simulate", json=payload)
    assert resp1.status_code == 200 and resp2.status_code == 200
    d1, d2 = resp1.json(), resp2.json()
    # Kecualikan shap_detail (boleh berbeda urutan dict-key insignificant) &
    # timing_ms (F6, secara desain BEDA tiap panggilan) dari perbandingan ketat.
    for key in ("shap_detail", "timing_ms"):
        d1.pop(key, None)
        d2.pop(key, None)
    assert d1 == d2
