#!/bin/bash
export OLLAMA_MAX_LOADED_MODELS=2

python3 main.py --cft belval --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 10 
python3 main.py --cft belval --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 30
python3 main.py --cft belval --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 50
python3 main.py --cft belval --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 70
python3 main.py --cft belval --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 100


python3 main.py --cft chrb --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 10 
python3 main.py --cft chrb --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 30
python3 main.py --cft chrb --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 50
python3 main.py --cft chrb --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 70
python3 main.py --cft chrb --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 100


python3 main.py --cft cabinet --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 10 
python3 main.py --cft cabinet --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 30
python3 main.py --cft cabinet --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 50
python3 main.py --cft cabinet --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 70
python3 main.py --cft cabinet --c-oa --extractor llama --kg-format turtle-light --chunk-dimension 100