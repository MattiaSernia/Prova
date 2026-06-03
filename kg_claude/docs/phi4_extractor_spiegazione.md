# Phi4TripletExtractor — Spiegazione completa

## 1. Cos'è il modello phi4_adaptableIE_v2

`phi4_adaptableIE_v2` è un modello linguistico da 14.7 miliardi di parametri (Small Language Model),
sviluppato a partire da Microsoft Phi-4 e ottimizzato per il task di **Information Extraction (IE)**.

A differenza dei modelli generici, questo modello è stato fine-tunato specificamente per:
- **Named Entity Recognition (NER)**: identificare entità nominate nel testo (organizzazioni, tecnologie, persone, ecc.)
- **Relation Extraction (RE)**: estrarre relazioni tra entità sotto forma di triple (soggetto, predicato, oggetto)

La caratteristica principale è la **zero-shot adaptation**: il comportamento dell'estrazione cambia
dinamicamente in base allo **schema** che forniamo nel prompt, senza bisogno di fine-tuning aggiuntivo.
Lo stesso modello può estrarre informazioni in domini completamente diversi semplicemente cambiando lo schema.

Il modello è distribuito in formato GGUF (quantizzazione Q4_K_M, ~8.9 GB) e gira localmente
tramite **Ollama**:

```
ollama pull hf.co/FinaPolat/phi4_adaptableIE_v2-gguf:Q4_K_M
```

---

## 2. Come funziona il prompt

Il modello si aspetta sempre due messaggi:

### System message
```
You are a helpful AI assistant specializing in Information Extraction tasks
such as Named Entity Recognition and Relation Extraction.
Follow the instructions given by the user.
```

### User message (template)
```
Information Extraction is the process of automatically identifying and
extracting structured information from unstructured text data.
Always extract numbers, dates, and currency values regardless of the specific task.

The task at hand is {task}.

Here is an example of task execution:
{example}

Analyze the text and targets carefully, identify relevant information.
Extract the information in the following format: `{output_format}`.
If no matching entities are found, return an empty list: [].
Please provide only the extracted information without any explanations.

Schema: {schema}
Text: {testo da analizzare}
```

Le variabili sono:
| Variabile | Contenuto |
|---|---|
| `{task}` | Descrizione del task (es. "Relation Extraction") |
| `{example}` | Esempio input → output per guidare il modello |
| `{output_format}` | Formato atteso dell'output (JSON) |
| `{schema}` | Ontologia del dominio (entità e relazioni ammesse) |

### Output atteso
Il modello risponde con un array JSON:
```json
[
  {"subject": "Nexus Engineering", "predicate": "holds", "object": "ISO 27001 certification"},
  {"subject": "Nexus Engineering", "predicate": "provides", "object": "cloud hosting"}
]
```
Se non trova nulla, restituisce `[]`.

---

## 3. Differenza con TripletExtractor (estrattore llama)

| Aspetto | TripletExtractor (llama) | Phi4TripletExtractor |
|---|---|---|
| Modello | llama3.3:70b (70B parametri) | phi4_adaptableIE_v2 (14.7B parametri) |
| Dimensione | ~42 GB | ~8.9 GB |
| Prompt | System + esempi in-context + `[subject \| predicate \| object]` | Template strutturato + schema JSON |
| Output | Formato testuale `[A \| B \| C]` parsato con regex | Array JSON parsato con `json.loads` |
| Adattabilità | Schema fisso nel codice | Schema dinamico passato nel prompt |
| Fine-tuning | Modello general-purpose guidato da few-shot | Modello fine-tunato specificamente per IE |

---

## 4. Come abbiamo applicato Phi4TripletExtractor nel progetto

### 4.1 Dove viene usato

L'estrattore viene usato in `custom_graph.py` nel metodo `_normalExtraction()`, che viene chiamato
ogni volta che un **agente** risponde a una domanda. Il testo della risposta viene passato all'estrattore
per ricavarne triple soggetto-predicato-oggetto da salvare nel grafo.

**Non** viene usato per requirements, constraints e proposals (che hanno estrattori dedicati).

### 4.2 Flusso di esecuzione

```
Risposta agente (testo libero)
        │
        ▼
CoreferenceResolver.resolve()      ← risolve i pronomi (es. "it" → "Nexus Engineering")
        │
        ▼
sentence_split(text, chunk_dim)    ← divide il testo in chunk (se chunk_dim > 0)
        │
        ▼
  per ogni chunk:
        │
        ▼
Phi4TripletExtractor.answer()      ← costruisce il prompt phi4, chiama Ollama, parsa il JSON
        │
        ▼
  {chunk_text: [{subject, predicate, object}, ...]}   ← dict restituito da pipe()
        │
        ▼
_normalExtraction() in custom_graph.py
  → crea ChunkURI (prov:Entity con ex:hasText)
  → crea TriURI (ex:Extraction)
  → per ogni triplet: crea nodo tri:triN con rdf:subject, edge:predicato, node:oggetto
  → collega: TriURI → ChunkURI → MessaggioAgente
```

### 4.3 Schema usato

Lo schema definisce le entità e le relazioni rilevanti per il dominio dei bandi di gara:

**Entità:**
`Organization`, `Technology`, `Service`, `Certification`, `Budget`, `Person`,
`Infrastructure`, `Regulation`, `Capability`, `Project`

**Relazioni:**
`provides`, `uses`, `has_certification`, `complies_with`, `costs`, `employs`,
`integrates_with`, `delivers`, `hosts`, `supports`, `has_capacity`, `has_budget`,
`manages`, `has_risk_level`, `has_deadline`, `has_value`

### 4.4 Parser dell'output

Il modello può includere testo extra attorno al JSON. Il parser usa una regex
(`\[.*\]` con flag DOTALL) per trovare il primo array JSON nella risposta,
poi valida ogni elemento assicurandosi che abbia tutti e tre i campi
(`subject`, `predicate`, `object`) non vuoti. Gli elementi malformati vengono scartati.

### 4.5 Come attivarlo

Da riga di comando, aggiungere `--extractor phi4` a qualsiasi modalità:

```bash
python main.py --extractor phi4
python main.py --kg-agents --extractor phi4
python main.py --no-kg --extractor phi4
```

Senza il flag, il comportamento di default usa `TripletExtractor` con llama3.3:70b.

---

## 5. Struttura nel grafo Knowledge Graph

Le triple estratte da phi4 vengono salvate nel grafo con la stessa struttura degli altri estrattori:

```
MessaggioAgente (prov:Entity)
    └── ChunkN (prov:Entity)          ← ex:hasText "testo del chunk"
          prov:wasDerivedFrom → MessaggioAgente
            └── tri/extractionN (ex:Extraction)
                  prov:wasDerivedFrom → ChunkN
                    └── tri:triN (ex:Triplet)
                          rdf:subject  → node:soggetto
                          edge:pred    → node:oggetto
```

Questo garantisce piena tracciabilità: ogni tripla è collegata al chunk di testo
da cui è stata estratta, e quel chunk è collegato al messaggio dell'agente che lo ha prodotto.
