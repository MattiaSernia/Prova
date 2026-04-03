"""
TripletExtractor — versione REBEL
Sostituisce il TripletExtractor originale basato su Ollama/command-r.

Dipendenze:
    pip install transformers torch sentencepiece

Modelli disponibili (scegli uno):
    - "Babelscape/rebel-large"   → migliore qualità, ~1.5GB, più lento
    - "Babelscape/rebel-base"    → più veloce, ~500MB, qualità leggermente inferiore

Uso:
    extractor = TripletExtractor(model_name="Babelscape/rebel-large")
    triplets = extractor.pipe("Albert Einstein was born in Germany in 1879.")
    for t in triplets:
        print(t.toString())
"""

import re
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from triplet import Triplet


class TripletExtractor:

    def __init__(self, model_name: str = "Babelscape/rebel-large", temperature=0):
        """
        Args:
            model_name: nome del modello HuggingFace da usare.
                        'temperature' è mantenuto per compatibilità con il codice originale
                        ma non viene usato (REBEL è deterministico con num_beams fisso).
        """
        print(f"[TripletExtractor] Carico il modello {model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.model.eval()
        print("[TripletExtractor] Modello caricato.")

    # ------------------------------------------------------------------
    # Parsing dell'output grezzo di REBEL
    # ------------------------------------------------------------------

    def parse_triplets(self, rebel_output: str) -> list:
        """
        Parsa la stringa generata da REBEL nel formato:
            <triplet> SOGGETTO <subj> OGGETTO <obj> RELAZIONE

        Ritorna una lista di tuple (soggetto, relazione, oggetto),
        nello stesso ordine (sub, pred, obj) usato nel codice originale.
        """
        triplets = []

        # Dividi sulle occorrenze di <triplet>
        chunks = rebel_output.split("<triplet>")

        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            # Cerca il pattern: SOGGETTO <subj> OGGETTO <obj> RELAZIONE
            match = re.match(
                r"^(.+?)\s*<subj>\s*(.+?)\s*<obj>\s*(.+?)(?:\s*<triplet>|$)",
                chunk,
                re.DOTALL,
            )
            if match:
                subject  = match.group(1).strip()
                obj      = match.group(2).strip()
                relation = match.group(3).strip()

                # Pulisci token residui
                for token in ["<s>", "</s>", "<pad>", "<triplet>", "<subj>", "<obj>"]:
                    subject  = subject.replace(token, "").strip()
                    obj      = obj.replace(token, "").strip()
                    relation = relation.replace(token, "").strip()

                if subject and relation and obj:
                    triplets.append((subject, relation, obj))

        return triplets

    # ------------------------------------------------------------------
    # Estrazione su una singola frase
    # ------------------------------------------------------------------

    def answer(self, text: str) -> list:
        """
        Estrae triple da una singola frase/paragrafo.
        Ritorna una lista di tuple (soggetto, relazione, oggetto).

        Compatibile con il metodo answer() originale.
        """
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True,
        )

        output_ids = self.model.generate(
            **inputs,
            max_length=512,
            num_beams=3,        # beam search per qualità migliore
            early_stopping=True,
        )

        decoded = self.tokenizer.decode(output_ids[0], skip_special_tokens=False)
        return self.parse_triplets(decoded)

    # ------------------------------------------------------------------
    # Separazione in frasi (identica all'originale)
    # ------------------------------------------------------------------

    def string_separator(self, text: str) -> list:
        """
        Divide il testo in frasi gestendo abbreviazioni comuni.
        Logica identica al TripletExtractor originale.
        """
        abbrev = r"\b(Mr|Mrs|Dr|Prof|vs|etc|Jr|Sr|Fig|al)\."
        text = re.sub(abbrev, r"\1<DOT>", text)
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text)
        sentences = [s.replace("<DOT>", ".").strip() for s in sentences]
        return [s for s in sentences if s]

    # ------------------------------------------------------------------
    # Pipeline completa: testo → lista di Triplet
    # ------------------------------------------------------------------

    def pipe(self, text: str) -> list:
        """
        Pipeline completa:
            1. Divide il testo in frasi
            2. Per ogni frase chiama answer()
            3. Ritorna una lista di oggetti Triplet

        Compatibile con il metodo pipe() originale.
        """
        #phrases = self.string_separator(text)
        text_triplets = []

        #for phrase in phrases:
        raw_triplets = self.answer(text)
        for sub, pred, obj in raw_triplets:
            text_triplets.append(Triplet(sub, pred, obj))

        return text_triplets


# ------------------------------------------------------------------
# Test rapido se eseguito direttamente
# ------------------------------------------------------------------

if __name__ == "__main__":

    extractor = TripletExtractor(model_name="Babelscape/rebel-large")

    test_sentences = [
        "Marie Curie was born in Warsaw and won the Nobel Prize in Physics in 1903.",
        "Albert Einstein, who was born in Germany, developed the theory of relativity.",
        "The committee did not approve the proposal because it lacked sufficient evidence.",
        # Frase più vicina al dominio del tuo progetto:
        "Nexus Engineering has an active contract with RFI worth 2.1 million euros "
        "expiring in December 2025, with a 2% penalty clause.",
    ]

    for sentence in test_sentences:
        print(f"\nFrase: {sentence}")
        triplets = extractor.pipe(sentence)
        if triplets:
            for t in triplets:
                print(f"  → {t.toString()}")
        else:
            print("  → nessuna tripla estratta")