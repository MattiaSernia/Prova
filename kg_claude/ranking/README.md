# Ranking dei punti di injection

Questo documento spiega il criterio di ranking implementato in
[`rank_injection.py`](rank_injection.py): un metodo per stabilire **quale
punto di injection del Knowledge Graph funziona meglio** per l'extractor
`llama`.

## Cosa viene classificato

Le "configurazioni" messe a confronto sono i **4 punti di injection** del KG,
ordinati dal meno al più iniettato:

| Sigla     | File di validazione                     |
|-----------|-----------------------------------------|
| `C_{O}`   | `single_validation_kg.txt`              |
| `C_{OA}`  | `single_validation_kgagents.txt`        |
| `C_{OP}`  | `single_validation_kgcft.txt`           |
| `C_{OAP}` | `single_validation_kgagents_tri.txt`    |

Si legge **solo il setting `llama/TURTLE/TEXT`**: l'extractor è frozen a
`llama`, il formato è TURTLE (l'unico che possiede gli esperimenti di
injection) e si considerano solo i run con il testo (`TEXT`).

## Le categorie

Il confronto viene fatto separatamente per ogni **categoria**, cioè ogni
combinazione di **CFT × metrica**. Le CFT sono 3 e le metriche 2
(requirements e constraints), quindi le categorie sono **6**:

```
belval-requirements    belval-constraints
chrb-requirements      chrb-constraints
cabinet-requirements   cabinet-constraints
```

Per ogni CFT il numero totale di requirements/constraints è noto
(`CFT_META` nello script), così i conteggi grezzi vengono convertiti in
**percentuale di soddisfatti**.

## Assegnazione dei punti

Dentro **ogni** categoria i 4 punti di injection vengono ordinati per
percentuale di soddisfatti (decrescente) e ricevono un punteggio in base alla
posizione:

- 1° posto (percentuale più alta) → **1 punto**
- 2° posto → **2 punti**
- 3° posto → **3 punti**
- 4° posto → **4 punti**

> **Il punteggio è una posizione, quindi meno punti = meglio.**

### Pareggi

Configurazioni con la **stessa percentuale** condividono la **media delle
posizioni** che occupano. Esempio: due config a pari merito al primo posto
prendono `(1 + 2) / 2 = 1.5` punti ciascuna. In questo modo ogni categoria
distribuisce sempre lo stesso monte punti totale: `1 + 2 + 3 + 4 = 10`.

### Dati mancanti

Se un file di validazione non esiste, quella configurazione viene trattata
come **0%** e finisce ultima in quella categoria.

## Punteggio finale

Per ogni punto di injection si **sommano i punti ottenuti nelle 6 categorie**.
Il totale minimo possibile è `6 × 1 = 6` (primo in ogni categoria), il massimo
`6 × 4 = 24` (ultimo ovunque).

> **La configurazione con il totale più basso è la migliore.**

## Esempio numerico

Supponiamo, per la categoria `belval-requirements`:

| Injection | % soddisfatti | Posizione | Punti |
|-----------|---------------|-----------|-------|
| `C_{OAP}` | 82%           | 1°        | 1     |
| `C_{OP}`  | 74%           | 2°        | 2     |
| `C_{OA}`  | 61%           | 3°        | 3     |
| `C_{O}`   | 53%           | 4°        | 4     |

Questo procedimento si ripete per tutte e 6 le categorie; alla fine i punti di
ciascuna riga vengono sommati e la tabella finale ordina i 4 injection point
dal totale più basso (migliore) al più alto (peggiore).

## Come si esegue

```bash
python3 ranking/rank_injection.py            # breakdown per categoria + tabella finale
python3 ranking/rank_injection.py --quiet    # solo la tabella finale
```
