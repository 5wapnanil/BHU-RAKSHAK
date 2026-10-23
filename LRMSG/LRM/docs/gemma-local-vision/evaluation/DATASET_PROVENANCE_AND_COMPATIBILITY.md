# Landslide Dataset Provenance & Compatibility Register

## 1. Overview and Purpose

This register documents candidate landslide datasets evaluated for potential benchmarking with the PahaarPulse Vision-Language Model (VLM) pipeline (Gemma 3 4B / hosted GenAI).

In accordance with PahaarPulse research integrity and safety directives:
1. **License Verification Gate:** No dataset may be downloaded, ingested, or redistributed unless its license terms are explicitly verified, permissive, and legally compatible.
2. **Modality & Architecture Separation:** Micro-scale ground-level field report triage (Gemma 3 RGB vision) must remain strictly decoupled from macro-scale remote-sensing satellite segmentation (multispectral GeoTIFF / binary pixel masks). Mismatched inputs must be actively rejected.
3. **Zero Metric Fabrication:** Accuracy or performance scores must never be claimed using synthetic labels, unverified datasets, or proxy annotations.

---

## 2. Dataset Compatibility & Provenance Matrix

| Dataset Identifier | Source / Reference | Modality | Annotation Schema | License Status | Geographic Scope | Compatible with Gemma Field VLM? | Admission Decision & Primary Blocker |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **`HLAD`** | Zenodo Record [22811448](https://zenodo.org/records/22811448) / DOI `10.5281/zenodo.22811448` | High-Resolution Optical Imagery (~4,000 images) | Bounding Boxes & Scar Segmentation Masks | **UNVERIFIED (Blank License)** | Himalayan Region | **NO** | **REJECTED_BLOCKED:** Visible license field on Zenodo is blank. Annotations delineate scar geometry (object detection/segmentation), lacking categorical geotechnical hazard severity (`low`/`moderate`/`high`/`critical`) and structural impact indicators. |
| **`Landslide4Sense`** | Hugging Face [ibm-nasa-geospatial/Landslide4sense](https://huggingface.co/datasets/ibm-nasa-geospatial/Landslide4sense) / IEEE GRSS [10.1109/MGRS.2022.3168877](https://doi.org/10.1109/MGRS.2022.3168877) | 14-Band Multispectral Satellite Patches (Sentinel-2, ALOS DEM, Slope) | Pixel-Wise Binary Segmentation Masks (0/1) | Academic Research License (Competition terms) | Global Multi-Region Mountainous Sites | **NO** | **REJECTED_BLOCKED:** 14-band multispectral array data ($128 \times 128$) requires specialized remote-sensing segmentation networks (U-Net, SegFormer), not conversational RGB vision models. Binary mask does not represent geotechnical triage classes. Belongs to GIS macro-pipeline. |
| **`PahaarPulse-Field-Benchmark`** | Internal Geotechnical Protocol (`field_photo_benchmark_template.csv`) | Standard Field Photographs (RGB JPEG / PNG / WebP) | Categorical Geotechnical Hazard Triage + 8 Physical Indicators | CC BY 4.0 / Internal Project Protocol | Indian Himalayan Region (Uttarakhand, Sikkim, Himachal Pradesh) | **YES (Target Architecture)** | **APPROVED_TARGET_SCHEMA:** Native RGB modality matching mobile/web field submissions. Full schema alignment with `GemmaHazardOutput`. Currently pending independent dual-expert adjudication. |

---

## 3. Detailed Dataset Dossiers

### 3.1 HLAD (Himalayan Landslide Detection Dataset)
- **Archive Identifier:** Zenodo Record `22811448`
- **DOI:** `10.5281/zenodo.22811448`
- **Reported Volume:** Approximately 4,000 high-resolution images.
- **Physical Modality:** High-resolution optical photography and drone orthophotos of slope failures across Himalayan valleys.
- **Annotation Schema:** Spatial masks and bounding boxes highlighting visible landslide scars.
- **License Status & Verification:**
  - Status: **UNVERIFIED — VISIBLE LICENSE FIELD BLANK**.
  - Risk Analysis: Zenodo's metadata specifies no open license (such as CC BY, CC0, or MIT). Without explicit written terms or publisher clarification, copying, downloading, redistributing, or fine-tuning models on this dataset risks intellectual property and terms-of-service violations.
- **Suitability & Architecture Separation:**
  - **Schema Mismatch:** Bounding boxes delineate *where* a scar is, but do not provide ground-truth geotechnical triage classifications (`low`, `moderate`, `high`, `critical`, `indeterminate`) or road-closure statuses.
  - **Perspective Mismatch:** Overhead drone imagery does not reflect the oblique eye-level perspective of field observers submitting photos of tension cracks, road margins, and retaining walls.
- **Policy Enforcement:** Automated evaluation harness must **reject** ingestion of HLAD until formal license terms are established and labels are geotechnically categorized.

---

### 3.2 Landslide4Sense Benchmark
- **Archive Identifier:** IEEE DataPort / Landslide4Sense Challenge
- **Source URL:** `https://landslide4sense.github.io/`
- **Reported Volume:** 3,799 training patches, 245 validation patches, 800 test patches ($128 \times 128$ pixels).
- **Physical Modality:** 14-channel multispectral satellite imagery:
  - Bands 1–12: Sentinel-2 Level-1C top-of-atmosphere reflectance (Coastal aerosol, Blue, Green, Red, VRE1-VRE3, NIR, Narrow NIR, Water vapor, SWIR1, SWIR2).
  - Band 13: ALOS PALSAR Digital Elevation Model (DEM).
  - Band 14: Topographic slope angle derived from DEM.
- **Annotation Schema:** 1-channel binary segmentation mask (0 = non-landslide background, 1 = landslide area).
- **License Status & Verification:**
  - Status: Competition/Research use only.
- **Suitability & Architecture Separation:**
  - **Modality Incompatibility:** Vision-Language Models (such as Gemma 3 4B) operate on 3-channel RGB visual tokens (or standard image formats via SigLIP vision encoders). They cannot ingest 14-channel floating-point multispectral satellite tensors without custom spectral projection layers.
  - **Task Incompatibility:** Binary semantic segmentation (classifying pixels as scar vs. non-scar) is an orthogonal computer vision task to preliminary geotechnical hazard triage.
  - **Architectural Placement:** Multispectral satellite monitoring belongs to macro-scale regional susceptibility services (e.g., PostGIS, ESA Copernicus ingestion), completely separate from the Gemma conversational field-screening service.
- **Policy Enforcement:** Evaluation harness must **reject** `.tif`, `.tiff`, `.npy`, `.h5` multispectral tensors with `UnsupportedModalityError`.

---

## 4. Input Rejection and Validation Rules

The evaluation engine (`backend/app/services/vlm_evaluation.py`) implements three non-negotiable validation barriers:

1. **File Modality Barrier:**
   - Supported extensions: `.jpg`, `.jpeg`, `.png`, `.webp`.
   - Magic byte validation for image streams.
   - Any attempt to feed multi-channel scientific formats (`.tif`, `.tiff`, `.npy`, `.h5`, `.hdf5`, `.nc`) raises `UnsupportedModalityError`.

2. **Annotation Schema Barrier:**
   - Evaluates presence of categorical `expert_ground_truth_hazard` in `{"low", "moderate", "high", "critical", "indeterminate"}`.
   - Datasets containing only binary segmentation masks (`0`/`1`), bounding box coordinates (`[xmin, ymin, xmax, ymax]`), or polygon shapefiles raise `MismatchedAnnotationSchemaError`.

3. **License Verification Barrier:**
   - Any dataset registered with `license_verified: false` (such as `HLAD`) is blocked from automatic fetching or batch evaluation, raising `UnverifiedLicenseError`.
