import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_static import curata_valuri  # noqa: E402


def _v(parat, tip, n):
    return {"parat": parat, "obiect_tip": tip, "nr_dosare": n}


def test_scoate_valurile_penale_de_familie_si_procedurale():
    valuri = [
        _v("BANCA TRANSILVANIA", "Confirmare renuntare urmarire penala art", 58),
        _v("DGASPC SUCEAVA", "Reintegrare familie", 40),
        _v("STATUL ROMAN", "Succesiune", 35),
        _v("OMNIASIG SA", "Reexaminare taxe timbru", 33),
        _v("CASA DE PENSII", "Recalculare pensie", 500),
    ]
    assert [g["obiect_tip"] for g in curata_valuri(valuri)] == ["Recalculare pensie"]


def test_unește_dublurile_și_păstrează_cifra_mare():
    valuri = [
        _v("NORDIS MANAGEMENT SRL", "Plângere carte funciară", 148),
        _v("Nordis Management S.R.L.", "Plângere carte funciară", 151),
    ]
    rez = curata_valuri(valuri)
    assert len(rez) == 1 and rez[0]["nr_dosare"] == 151


def test_executarea_unei_banci_nu_e_fiscala():
    rez = curata_valuri([
        {"parat": "BANCA TRANSILVANIA SA", "obiect_tip": "Contestație la executare fiscală",
         "domeniu": "fiscal", "nr_dosare": 1686},
        {"parat": "AGENŢIA NAŢIONALĂ DE ADMINISTRARE FISCALĂ",
         "obiect_tip": "Contestație la executare fiscală", "domeniu": "fiscal", "nr_dosare": 190},
    ])
    tipuri = {g["parat"]: (g["obiect_tip"], g["domeniu"]) for g in rez}
    assert tipuri["BANCA TRANSILVANIA SA"] == ("Contestație la executare", "recuperare")
    assert tipuri["AGENŢIA NAŢIONALĂ DE ADMINISTRARE FISCALĂ"][0] == "Contestație la executare fiscală"
