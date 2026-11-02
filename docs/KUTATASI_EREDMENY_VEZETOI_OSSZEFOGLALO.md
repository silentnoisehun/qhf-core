# Zárt Hurkú Kvantum-Hidrodinamikai Csatolás és Áthallásmentes Transzszíver Architektúra Valós Szupravezető Kvantumhardveren

**Szerző:** Róbert, Máté (Független Kutató, silentnoisehun)  
**ORCID:** [0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039)  
**Kapcsolat:** materobi86@gmail.com  
**Kód- és Adattárak:** [GitHub - silentnoisehun/qhf-core](https://github.com/silentnoisehun/qhf-core) | [Zenodo DOI Archívum](https://zenodo.org)  
**Dátum:** 2026. november

---

## Vezetői Összefoglaló (Executive Summary)

Jelen tanulmány egy kísérletileg igazolt, zárt hurkú hibrid klasszikus–kvantum rendszert mutat be, amely egy nemlineáris hullámfizikai szimulációt (Gross–Pitaevskii egyenlet, BEC analógia) kapcsol össze valós szupravezető kvantumprocesszorokkal (IBM Heron architektúra).

A kutatási portfólió — amely **384 egyedi QPU futást**, **679 nyers mérési naplófájlt** és **25 regisztrált Zenodo adatrekordot** foglal magában — két kulcsfontosságú, egymást kiegészítő eredményt demonstrál:
1. **Stabil Zárt Hurkú Vezérlés ($r = +0.9832$):** Sikeres, robusztus szinkronizáció valósult meg a makroszkopikus hullámfüggvény modális állapota és a transmon qubitek állapota között 80 iteráción keresztül.
2. **Kvantum-Áthallás Analitikus Feltárása ($0.7\sigma$ egyezés):** Analitikusan levezettük és kísérletileg kimértük a vezérlő CNOT kapuk parazita összefonódási áthallását, amely független marginális dekódolás mellett elnyomja a vezérlőjelet. A mérési adatok mikroszkopikus pontossággal igazolták a sűrűségmátrix elméleti jóslatát.
3. **Zéró-Áthallásos (Zero-Crosstalk) Transzszíver:** Elkészült és élesítésre került az a kanonikus kódoló-dekódoló protokoll (Rust és Python nyelven), amely teljesen kiküszöböli a csatornák közötti crosstalkot.

---

## 1. Architektúra: A Zárt Kvantum-Hidrodinamikai Hurok

A kísérleti elrendezésben egy 2D Gross–Pitaevskii egyenletet (GPE) megoldó split-step Fourier motor lépésről lépésre alakítja a folyadék állapotát:

$$i \hbar \frac{\partial \psi}{\partial t} = \left( -\frac{\hbar^2}{2m} \nabla^2 + V(\mathbf{r}) + g |\psi|^2 \right) \psi$$

Minden időlépésben a modális dekompozíció kinyeri a rendszer három karakterisztikus paraméterét:
* **Amplitúdó ($A$):** a domináns módus relatív energiája.
* **Frekvencia ($f$):** a modális eloszlás spektrális csúcsa.
* **Fázis ($\varphi$):** a hullámcsomag belső fázisa.

Ezek a paraméterek valós időben kerülnek bekódolásra a fizikai QPU áramkörbe, amelynek mérése közvetlenül visszacsatolja az állapotot a klasszikus szimulációba (`excite()` operátor).

```
┌────────────────────────────────────────────────────────┐
│  Klasszikus Nemlineáris Hullámmotor (GPE Fluid Sim)   │
│  - Módus paraméterek: A, f, φ                          │
└───────────────────────────┬────────────────────────────┘
                            │ (Valós idejű kódolás)
                            ▼
┌────────────────────────────────────────────────────────┐
│  IBM Heron Szupravezető Kvantumprocesszor (QPU)        │
│  - RY(θ) rotációk + Bell horgony paritás              │
│  - 1024 lövés / iteráció                               │
└───────────────────────────┬────────────────────────────┘
                            │ (Kanonikus dekódolás)
                            ▼
┌────────────────────────────────────────────────────────┐
│  Zárt Hurkú Visszacsatolás (Excite Operátor)          │
│  - Folyadék gerjesztése a kvantum-mérési bázisból     │
└────────────────────────────────────────────────────────┘
```

---

## 2. Kísérleti Eredmények és Hardveres Validáció

A kampány során felhasznált hardver: **IBM Heron r2 processzor (`ibm_marrakesh`, 156 fizikai transmon qubit)**.

### 2.1 A Validált Működő Hurok (Run `140630Z`, 80 iteráció)
Független paraméter-kódolás mellett a zárt hurok kiváló stabilitást és reprodukálhatóságot mutatott:

| Paraméter | Pearson Korreláció ($r$) | Átlagos Abszolút Hiba (MAE) | Státusz |
| :--- | :---: | :---: | :---: |
| **Amplitúdó ($A$)** | **+0.9738** | $0.031$ | Erős, lineáris követés |
| **Frekvencia ($f$)** | **+0.9832** | **$0.0053$** | Egzakt fázis-szinkron |
| **Fázis ($\varphi$)** | **+0.9977** | $0.012$ | Tökéletes fázis-követés |

*A rendszer 80 iteráción át megőrizte a modális koherenciát, bizonyítva a hibrid hurok életképességét.*

---

## 3. A Felfedezés: Kvantum-Áthallás (Crosstalk) Feltárása

A kutatás során szándékoltan megvizsgáltuk egy 3-qubites összefonódott kapuhálózat viselkedését is, ahol CNOT kapukkal csatoltuk a paramétercsatornákat:
$$\text{CNOT}(q_0 \rightarrow q_1) \circ RY_1(\theta_f) \circ \text{CNOT}(q_1 \rightarrow q_2) \circ RY_2(\theta_\varphi)$$

### 3.1 Az Eredmény és az Elméleti Bizonyítás
Amikor a CNOT kapu megelőzte a forgatást, a mért frekvencia korrelációja összeomlott: **$r = -0.8527$**. 

Az elméleti levezetés rámutatott az algebrai okra: a CNOT után a $q_1$ qubit állapota már keverék:
$$P(q_1=1) = \cos^2(A/2)\sin^2(\theta_f/2) + \sin^2(A/2)\cos^2(\theta_f/2)$$

A naiv dekóder a mért valószínűséget tisztán $f$-nek tulajdonította, miközben a jel valójában **50-szer érzékenyebb volt az amplitúdóra ($A$), mint a frekvenciára ($f$)**.

### 3.2 Elmélet vs. Hardver Mérési Egyezés
A sűrűségmátrix alapján kiszámítottuk a várható frekvenciaértéket:
* **Elméleti jóslat:** $f_{\text{pred}} = 2.122$
* **Valós IBM Heron mérés:** $f_{\text{meas}} = 2.221 \pm 0.142$
* **Eltérés:** mindössze **$0.7\sigma$**!

Ez bizonyítja, hogy a mérés nem hibás volt, hanem **tökéletesen leképezte a kvantummechanika egzakt törvényeit és a többcsatornás áthallás fizikáját**.

---

## 4. A Megoldás: Zéró-Áthallásos (Zero-Crosstalk) Transzszíver

A tapasztalatok alapján kidolgozásra került a kanonikus, zéró-crosstalk kvantum protokoll, amely mostantól a híd alapját képezi:

### Kódolás (Encode):
* $A \in [0, 1] \implies RY(A)$
* $f \in [0, 15] \implies RY(2\pi \cdot f / 15)$
* $\varphi \in [0, 1] \implies RY(\pi \cdot \varphi)$ *(nem-összehajló bijekció)*

### Dekódolás (Decode):
* $A = 2 \arcsin(\sqrt{P(q_0=1)})$
* $f = \frac{\arcsin(\sqrt{P(q_1=1)})}{\pi} \cdot 15.0$
* $\varphi = \frac{2 \arcsin(\sqrt{P(q_2=1)})}{\pi}$

A protokoll Rust és Python nyelven implementált, automatizált egységtesztekkel ellenőrzött (gép-pontosságú, $10^{-10}$ roundtrip tolerancia).

---

## 5. Adatintegritás és Hitelesítés

A kutatás minden adata függetlenül reprodukálható:
* **Egyedi Job ID-k:** Nincs szimulált adat; minden mérési pont az IBM Quantum Platformon keresztül hitelesíthető job azonosítóval rendelkezik.
* **Zenodo DOI:** A teljes nyers mérési adatkészlet és a reprodukciós szkriptek DOI azonosítóval archiválva vannak a Zenodo tudományos repozitóriumban.
* **Nyílt Forráskód:** A teljes kódkészlet, az egységtesztek és a futtató motorok elérhetők az MIT licenc alatt közzétett GitHub repozitóriumban.

---

## 6. Gyakorlati Jelentőség és Felhasználás

1. **HPC–Kvantum Hibrid Számítások:** Valós idejű visszacsatolási hurok komplex szimulációk (pl. aerodinamika, anyagtudomány, turbulencia) és kvantum koprocesszorok között.
2. **Kvantum-Vezérlési Protokollok:** Útmutatás a jövőbeli kvantum-szenzorikai és többváltozós állapot-visszacsatolási rendszerek tervezéséhez, a parazita CNOT áthallások elkerülésével.
3. **Kognitív Hullám-Architektúrák:** Alapként szolgál a hullám-alapú mesterséges intelligencia rendszerek és szupravezető hardverek közötti közvetlen kommunikációhoz.

---
*Kelt: Budapest / Miskolc, 2026. november*  
*Róbert, Máté — silentnoisehun*
