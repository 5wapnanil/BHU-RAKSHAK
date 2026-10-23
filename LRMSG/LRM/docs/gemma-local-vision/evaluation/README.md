# PahaarPulse VLM Evaluation Directory

This directory contains the tools and protocols for evaluating Vision-Language Models (such as Gemma 3 4B) against expert-adjudicated landslide photographs.

## Directory Structure
- `EVALUATION_FRAMEWORK.md`: Formal geotechnical taxonomy, adjudication rules, and metric definitions.
- `evaluation_dataset_template.csv`: Standardized CSV schema for expert geotechnical annotation.
- `eval_images/`: Recommended isolated directory for ground-truth benchmark photographs (kept separate from operational database uploads).

## Usage Instructions

### 1. Preparing the Dataset
1. Populate `evaluation_dataset.csv` using `evaluation_dataset_template.csv` as the schema.
2. Ensure images are stored locally and accessible.
3. Have at least two qualified geotechnical experts independently annotate `expert_ground_truth_hazard` and `visible_indicators`.
4. Set `adjudication_status` to `adjudicated` once consensus is reached.

### 2. Running Model Evaluation
Execute the reproducible evaluation script:
```powershell
python backend/scripts/evaluate_vlm.py --dataset docs/gemma-local-vision/evaluation/evaluation_dataset.csv --provider ollama
```

### 3. Output
The evaluation tool will:
- Run inference through the specified provider (`ollama`, `google`, or `mock`).
- Handle `indeterminate` outputs explicitly.
- Compute per-class Precision, Recall, and F1, plus the Confusion Matrix, Macro F1, and Coverage Rate.
- If no expert labels are present, output an explicit warning and abstain from calculating false accuracy metrics.
- Export an annotated results CSV with model predictions populated.
