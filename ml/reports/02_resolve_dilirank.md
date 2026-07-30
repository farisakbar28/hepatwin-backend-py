# 02 -- Resolusi Nama -> SMILES (DILIrank 2.0)

- Input: `ml/data/interim/_dilirank_clean.csv` (1336 baris)
- Output: `ml/data/interim/dilirank_smiles.csv` (1225 baris)

| Metrik | Jumlah |
|---|---|
| Berhasil resolve | 1225 |
| -- di antaranya via fallback strip-garam | 5 |
| Biologik dibuang (-mab/-cept/-ase/...) | 35 |
| Gagal resolve | 76 |

## Nama gagal resolve (dibiarkan kosong, TIDAK ditebak)

- Agalsidase beta
- Aldesleukin
- Alglucosidase alfa
- Anakinra
- Benzylpenicilloyl polylysine
- Botulinum toxin type a
- Botulinum toxin type b
- Casimersen
- Certolizumab pegol
- Cholestyramine
- Choriogonadotropin alfa
- Colesevelam hydrochloride
- Crofelemer
- Dalteparin sodium
- Darbepoetin alfa
- Defibrotide sodium
- Denileukin diftitox
- Dermatan
- Enoxaparin sodium
- Eteplirsen
- Ferumoxides
- Ferumoxsil
- Filgrastim
- Follitropin alfa/beta
- Gemtuzumab ozogamicin
- Givosiran sodium
- Glatiramer acetate
- Golodirsen
- Hetastarch
- Hyaluronidase recombinant human
- Ibritumomab tiuxetan
- Inclisiran sodium
- Inotersen sodium
- Interferon alfa-2a, recombinant
- Interferon alfacon-1
- Interferon beta-1a
- Interferon beta-1b
- Interferon gamma-1b
- Ivermectin
- Lumasiran sodium
- Mecasermin recombinant
- Muromonab-cd3
- Nusinersen sodium
- Oprelvekin
- Pafuraidine
- Palifermin
- Patiromer sorbitex calcium
- Patisiran sodium
- Pegademase bovine
- Pegcetacoplan
- Pegfilgrastim
- Peginterferon alfa-2a
- Peginterferon alfa-2b
- Pegvisomant
- Pentosan polysulfate sodium
- Phentermine resin complex
- Polyethylene glycol 3350
- Polymyxin b sulfate
- Polythiazide
- Porfimer sodium
- Protamine sulfate
- Radium ra-223 dichloride
- Romiplostim
- Sargramostim
- Secretin synthetic human
- Sevelamer hydrochloride
- Simethicone-cellulose
- Sodium polystyrene sulfonate
- Somatropin
- Sucralfate
- Technetium tc-99m exametazime kit
- Tetracycline phosphate complex
- Thyrotropin alfa
- Tinzaparin sodium
- Verteporfin
- Viltolarsen
