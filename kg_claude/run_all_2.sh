#!/bin/bash
export OLLAMA_MAX_LOADED_MODELS=2

# kg-format frozen to turtle-light, chunk-dimension frozen to 0 (default).
# Modes covered: C_{OA} (--c-oa), C_{OP} (--c-op), C_{O} (default, no mode flag).
# C_{OAP} excluded (already run in run_all.sh). C_null not included (already run, no format dependency).
# Extractors: phi4 (schema only) and llama.

python3 main.py --cft belval --c-oa --extractor phi4 --kg-format turtle-light
python3 main.py --cft belval --c-oa --extractor phi4 --kg-format turtle-light --no-text
python3 main.py --cft belval --c-oa --extractor llama --kg-format turtle-light
python3 main.py --cft belval --c-oa --extractor llama --kg-format turtle-light --no-text

python3 main.py --cft belval --c-op --extractor phi4 --kg-format turtle-light
python3 main.py --cft belval --c-op --extractor phi4 --kg-format turtle-light --no-text
python3 main.py --cft belval --c-op --extractor llama --kg-format turtle-light
python3 main.py --cft belval --c-op --extractor llama --kg-format turtle-light --no-text

python3 main.py --cft belval --extractor phi4 --kg-format turtle-light
python3 main.py --cft belval --extractor phi4 --kg-format turtle-light --no-text
python3 main.py --cft belval --extractor llama --kg-format turtle-light
python3 main.py --cft belval --extractor llama --kg-format turtle-light --no-text

python3 main.py --cft chrb --c-oa --extractor phi4 --kg-format turtle-light
python3 main.py --cft chrb --c-oa --extractor phi4 --kg-format turtle-light --no-text
python3 main.py --cft chrb --c-oa --extractor llama --kg-format turtle-light
python3 main.py --cft chrb --c-oa --extractor llama --kg-format turtle-light --no-text

python3 main.py --cft chrb --c-op --extractor phi4 --kg-format turtle-light
python3 main.py --cft chrb --c-op --extractor phi4 --kg-format turtle-light --no-text
python3 main.py --cft chrb --c-op --extractor llama --kg-format turtle-light
python3 main.py --cft chrb --c-op --extractor llama --kg-format turtle-light --no-text

python3 main.py --cft chrb --extractor phi4 --kg-format turtle-light
python3 main.py --cft chrb --extractor phi4 --kg-format turtle-light --no-text
python3 main.py --cft chrb --extractor llama --kg-format turtle-light
python3 main.py --cft chrb --extractor llama --kg-format turtle-light --no-text

python3 main.py --cft cabinet --c-oa --extractor phi4 --kg-format turtle-light
python3 main.py --cft cabinet --c-oa --extractor phi4 --kg-format turtle-light --no-text
python3 main.py --cft cabinet --c-oa --extractor llama --kg-format turtle-light
python3 main.py --cft cabinet --c-oa --extractor llama --kg-format turtle-light --no-text

python3 main.py --cft cabinet --c-op --extractor phi4 --kg-format turtle-light
python3 main.py --cft cabinet --c-op --extractor phi4 --kg-format turtle-light --no-text
python3 main.py --cft cabinet --c-op --extractor llama --kg-format turtle-light
python3 main.py --cft cabinet --c-op --extractor llama --kg-format turtle-light --no-text

python3 main.py --cft cabinet --extractor phi4 --kg-format turtle-light
python3 main.py --cft cabinet --extractor phi4 --kg-format turtle-light --no-text
python3 main.py --cft cabinet --extractor llama --kg-format turtle-light
python3 main.py --cft cabinet --extractor llama --kg-format turtle-light --no-text
