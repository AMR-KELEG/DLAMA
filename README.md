# CultLAMA
Build relation triples that are more representative to the culture of specific regions as 
opposed to LAMA which is more biased towards western entities.

- [CultLAMA](#cultlama)
  - [Usage](#usage)
    - [1. Create conda environment and install requirements](#1-create-conda-environment-and-install-requirements)
    - [2. Download mLAMA](#2-download-mlama)
    - [3. Build CultLAMA](#3-build-cultlama)
    - [4. Run the experiments](#4-run-the-experiments)
  - [Domains and their respective relation predicates currently supported within CultLAMA](#domains-and-their-respective-relation-predicates-currently-supported-within-cultlama)
  - [Results](#results)
    - [CultLAMA-v1 (Arab and Western facts)](#cultlama-v1-arab-and-western-facts)
    - [CultLAMA-v1 (Asian and Western facts)](#cultlama-v1-asian-and-western-facts)
  - [Adding new countries/regions to CultLAMA](#adding-new-countriesregions-to-cultlama)
  - [References](#references)
  - [Acknowledgements](#acknowledgements)

## Usage
### 1. Create conda environment and install requirements
```
conda create -n cultlama -y python=3.7 && conda activate cultlama
pip install -r requirements.txt
```

### 2. Download mLAMA
- mLAMA is needed since its templates are used for prompting the models.
- Note: Run the following commands from the root directory of the repository.
```bash
wget http://cistern.cis.lmu.de/mlama/mlama1.1.zip
unzip mlama1.1.zip
rm mlama1.1.zip
mv mlama1.1 mlama/data/mlama1.1/
```

### 3. Build CultLAMA
```
# Navigate to the cultlama directory
cd cultlama/

# Query raw triples from Wikidata to (data/cultlama_raw/ directory)
python generate_data_files.py --region REG --n N --langs LIST_OF_LABELS_LANGS --rel LIST_OF_RELATIONS

# Generate exhaustive lists of objects for the queried subjects to (data/cultlama/ directory)
python generate_exhaustive_objects.py --langs LIST_OF_LABELS_LANGS --rel LIST_OF_RELATIONS

```

### 4. Run the experiments
- Note: The scripts within the `mlama` subdirectory are forked from https://github.com/norakassner/mlama and adapted accordingly.
```bash
cd ../mlama # Navigate to the mlama directory within the repository
python scripts/run_prompting_experiment.py --lang "ar" --cultlama --dataset_dir DATASET_BASE_DIR \
       --templates_file_path TEMPLATES_FILE_PATH --device DEVICE_NAME --rel RELATIONS --models MODELS
```

## Domains and their respective relation predicates currently supported within CultLAMA
| Domain | Relation|
|---|---|
|Cinema and theatre | P19 (Place of birth)|
|| P20 (Place of death)|
|| P27 (Country of citizenship)|
|| P103 (Native language)|
|| P106 (Occupation)|
|| P364 (Original language of work)|
|| P449 (Original network)|
|| P495 (Country of origin)|
|| P1412 (Languages spoken or published)|
|Geography | P17 (Country)|
|| P30 (Continent)|
|| P36 (Capital)|
|| P47 (Shares border with)|
|| P1376 (Capital of)|
|History | P17 (Country)|
|Music | P19 (Place of birth)|
|| P20 (Place of death)|
|| P27 (Country of citizenship)|
|| P103 (Native language)|
|| P106 (Occupation)|
|| P136 (Genre)|
|| P264 (Record label)|
|| P495 (Country of origin)|
|| P1303 (Instrument)|
|| P1412 (Languages spoken or published)|
|Politics | P19 (Place of birth)|
|| P20 (Place of death)|
|| P27 (Country of citizenship)|
|| P37 (Official language)|
|| P103 (Native language)|
|| P106 (Occupation)|
|| P190 (Sister city)|
|| P530 (Diplomatic relation)|
|| P1412 (Languages spoken or published)|
|Sports | P17 (Country)|
|| P19 (Place of birth)|
|| P20 (Place of death)|
|| P27 (Country of citizenship)|
|| P103 (Native language)|
|| P106 (Occupation)|
|| P1412 (Languages spoken or published)|

## Results
### CultLAMA-v1 (Arab and Western facts)

| Langugage of Prompt   | Model Name                     |   P@1 Arab Facts (N=5140)|   P@1 Western Facts (N=5340)|   P@1 All facts (N=10480)|
|:-----------|:-------------------------------|:-----------:|:-----------:|:-----------------:|
| Arabic     | DarijaBERT           |      3.852 |      7.004 🔼|            5.458 |
|     | DziriBERT            |     15.506 🔼|      8.071 |           11.718 |
|     | mBERT-base (cased)   |     10.486 |     13.165 🔼|           11.851 |
|     | CAMeL-DA             |     27.257 🔼|      1.536 |           14.151 |
|     | CAMeL-MIX            |     15.914 🔼|     14.532 |           15.21  |
|     | mBERT-base (uncased) |     16.654 |     17.041 🔼|           16.851 |
|     | MARBERT (v2)         |     26.012 🔼|      9.625 |           17.662 |
|     | GigaBERT_v4          |     20.117 🔼|     18.202 |           19.141 |
|     | Arabic BERT-base     |     29.572 🔼|     10.824 |           20.019 |
|     | CAMeL-MSA            |     24.825 🔼|     17.285 |           20.983 |
|     | MARBERT              |     34.825 🔼|     15.712 |           25.086 |
|     | AraBERT-base (v0.2)  |     26.498 🔼|     24.757 |           25.611 |
|     | AraBERT-base (v0.1)  |     31.887 🔼|     20.243 |           25.954 |
|     | AraBERT-large (v0.2) |     26.809 🔼|     25.3   |           26.04  |
|     | ArabicBERT-large     |     34.942 🔼|     21.142 |           27.91  |
|     | QARiB                |     33.891 🔼|     23.633 |           28.664 |
|     | ARBERT               |     32.626 🔼|     26.217 |           29.361 |
|     | GigaBERT (v3)        |     37.899 🔼|     22.959 |           30.286 |
| English    | GigaBERT_v4          |     21.693 |     33.614  🔼|           27.767 |
|     | GigaBERT (v3)        |     21.537 |     34.569 🔼|           28.177 |
|     | BERT-base (uncased)  |     21.537 |     35.019 🔼|           28.406 |
|     | BERT-large (uncased) |     23.638 |     34.569 🔼|           29.208 |
|     | BERT-large (cased)   |     26.109 |     36.161 🔼|           31.231 |
|     | mBERT-base (uncased) |     23.191 |     41.311 🔼|           32.424 |
|     | BERT-base (cased)    |     26.342 |     38.577 🔼|           32.576 |
|     | mBERT-base (cased)   |     21.829 |     45.562 🔼|           33.922 |

### CultLAMA-v1 (Asian and Western facts)
Note: Manual inspection and updating was done for the Mandarin prompts by a native speaker.

| Langugage of Prompt   | Model Name                     |   P@1 Asian Facts (N=4959)|   P@1 Western Facts (N=5339)|   P@1 All facts (N=10298)|
|:-----------|:-------------------------------|:-----------:|:-----------:|:-----------------:|
| English    | BERT-base (uncased)            |     33.535 |     35.437 🔼 |           34.521 |
|    | BERT-large (uncased)           |     34.765 |     35.025 🔼 |           34.9   |
|    | BERT-large (cased)             |     35.612 |     35.868 🔼 |           35.745 |
|    | BERT-base (cased)              |     33.757 |     38.659 🔼 |           36.298 |
|    | mBERT-base (uncased)           |     32.023 |     41.843 🔼 |           37.114 |
|    | mBERT-base (cased)             |     34.745 |     45.177 🔼 |           40.153 |
| Mandarin   | mBERT-base (cased)             |     10.889 🔼 |      9.871 |           10.361 |
|    | mBERT-base (uncased)           |     16.616 🔼 |     12.1   |           14.275 |
|    | ChineseBERT-base               |     18.673 🔼 |     16.164 |           17.372 |
| Japanese   | mBERT-base (uncased)           |     17.161 🔼 |      7.286 |           12.041 |
|    | TohokuBERT-base (char)         |     17.725 🔼 |     13.055 |           15.304 |
|    | TohokuBERT-base (char v2)      |     11.272 |     19.816 🔼 |           15.702 |
|    | JapaneseBERT-base              |     15.064 |     20.996 🔼 |           18.139 |
|    | mBERT-base (cased)             |     21.436 🔼 |     18.936 |           20.14  |
|    | TohokuBERT-large (char)        |     17.443 |     24.031 🔼 |           20.858 |
|    | TohokuBERT-base_v2             |     22.847 |     35.662 🔼 |           29.491 |
|    | TohokuBERT-base                |     23.573 |     35.999 🔼 |           30.016 |
|    | TohokuBERT-large               |     21.738 |     39.464 🔼 |           30.928 |
|    | TohokuBERT-base (word masking) |     22.081 |     40.026 🔼 |           31.385 |
| Korean     | KykimBERT-base                 |     17.483 🔼 |     14.179 |           15.77  |
|      | mBERT-base (uncased)           |     17.241 |     17.943 🔼 |           17.605 |
|      | mBERT-base (cased)             |     13.914 |     31.748 🔼 |           23.16  |
|      | KlueBERT-base                  |     23.21  |     29.631 🔼 |           26.539 |


## Adding new countries/regions to CultLAMA

1. Add the list of country names to `cultlama/constants.py`.
```
BOTSWANA = "Botswana"
ESWATINI = "Eswatini"
LESOTHO = "Lesotho"
MADAGASCAR = "Madagascar"
NAMIBIA = "Namibia"
SOUTH_AFRICA = "South Africa"
```

2. Create a list of the new countries representing the region in `cultlama/constants.py`.
```
SOUTHERN_AFRICA = [
    BOTSWANA,
    ESWATINI,
    LESOTHO,
    MADAGASCAR,
    NAMIBIA,
    SOUTH_AFRICA,
]
```

3. Add the languages of Wikipedia that are related to each country to the `REGIONS_LANGS` variable in `cultlama/constants.py`.
```
REGIONS_LANGS ={
    ...
    BOTSWANA: ["en"],
    ESWATINI: ["en"],
    LESOTHO: ["en"],
    MADAGASCAR: ["fr"],
    NAMIBIA: ["en"],
    SOUTH_AFRICA: ["af", "zu", "en"],
    ...
}
```

4. Add the Wikidata URIs for each country to the `"region_country"` key of the `FILTERS_DICTIONARY` variable in `cultlama/filters.py`.
```
    "region_country": {
        ...
        BOTSWANA: f"VALUES ?{COUNTRY} {{wd:Q963}} . # Country is Botswana",
        ESWATINI: f"VALUES ?{COUNTRY} {{wd:Q1050}} . # Country is Eswatini",
        LESOTHO: f"VALUES ?{COUNTRY} {{wd:Q1013}} . # Country is Lesotho",
        MADAGASCAR: f"VALUES ?{COUNTRY} {{wd:Q1019}} . # Country is Madagascar",
        NAMIBIA: f"VALUES ?{COUNTRY} {{wd:Q1030}} . # Country is Namibia",
        SOUTH_AFRICA: f"VALUES ?{COUNTRY} {{wd:Q258}} . # Country is South Africa",
    },
```

5. Add the region as a new region in the `REGIONS` dictionary of `cultlama/generate_data_files.py`.
```
  REGIONS ={
    ...
    "SOUTHERN_AFRICA": SOUTHERN_AFRICA,
  }
```

6. Query facts related to the new region
```
$ python cultlama/generate_data_files.py --region SOUTHERN_AFRICA --n 6 --rel P36 --langs fr en
$ python cultlama/generate_exhaustive_objects.py --rel P36 --langs en fr
```

7. Inspect the queried facts
```
$ cat data/cultlama/en/P36_geography_SOUTHERN_AFRICA.jsonl
{"sub_uri": "Q258", "obj_uri": ["Q37701", "Q3926", "Q5465"], "sub_label": "South Africa", "obj_label": ["Bloemfontein", "Pretoria", "Cape Town"], "uuid": "P36_geography_SOUTHERN_AFRICA_0"}
{"sub_uri": "Q1019", "obj_uri": ["Q3915"], "sub_label": "Madagascar", "obj_label": ["Antananarivo"], "uuid": "P36_geography_SOUTHERN_AFRICA_1"}
{"sub_uri": "Q1030", "obj_uri": ["Q3935"], "sub_label": "Namibia", "obj_label": ["Windhoek"], "uuid": "P36_geography_SOUTHERN_AFRICA_2"}
{"sub_uri": "Q963", "obj_uri": ["Q3919"], "sub_label": "Botswana", "obj_label": ["Gaborone"], "uuid": "P36_geography_SOUTHERN_AFRICA_3"}
{"sub_uri": "Q1050", "obj_uri": ["Q101418", "Q3904"], "sub_label": "Eswatini", "obj_label": ["Lobamba", "Mbabane"], "uuid": "P36_geography_SOUTHERN_AFRICA_4"}
{"sub_uri": "Q1013", "obj_uri": ["Q3909"], "sub_label": "Lesotho", "obj_label": ["Maseru"], "uuid": "P36_geography_SOUTHERN_AFRICA_5"}

$ cat data/cultlama/fr/P36_geography_SOUTHERN_AFRICA.jsonl
{"sub_uri": "Q258", "obj_uri": ["Q37701", "Q3926", "Q5465"], "sub_label": "Afrique du Sud", "obj_label": ["Bloemfontein", "Pretoria", "Le Cap"], "uuid": "P36_geography_SOUTHERN_AFRICA_0"}
{"sub_uri": "Q1019", "obj_uri": ["Q3915"], "sub_label": "Madagascar", "obj_label": ["Antananarivo"], "uuid": "P36_geography_SOUTHERN_AFRICA_1"}
{"sub_uri": "Q1030", "obj_uri": ["Q3935"], "sub_label": "Namibie", "obj_label": ["Windhoek"], "uuid": "P36_geography_SOUTHERN_AFRICA_2"}
{"sub_uri": "Q963", "obj_uri": ["Q3919"], "sub_label": "Botswana", "obj_label": ["Gaborone"], "uuid": "P36_geography_SOUTHERN_AFRICA_3"}
{"sub_uri": "Q1050", "obj_uri": ["Q101418", "Q3904"], "sub_label": "Eswatini", "obj_label": ["Lobamba", "Mbabané"], "uuid": "P36_geography_SOUTHERN_AFRICA_4"}
{"sub_uri": "Q1013", "obj_uri": ["Q3909"], "sub_label": "Lesotho", "obj_label": ["Maseru"], "uuid": "P36_geography_SOUTHERN_AFRICA_5"}
```

## Utilities
- Script to quantify the percentage of tuples related to the 21 Western countries (for the predicates that have persons or places as their subjects 
and/or objects)
`python mlama/quantify_diversity.py --dataset_dir mlama/data/mlama1.1/en/ --output_stats_file mLAMA_stats.jsonl`

## References
```bibtex
@inproceedings{kassner2021multilingual,
    title = "Multilingual {LAMA}: Investigating Knowledge in Multilingual Pretrained Language Models",
    author = {Kassner, Nora  and
      Dufter, Philipp  and
      Sch{\"u}tze, Hinrich},
    booktitle = "to appear in Proceedings of the 16th Conference of the European Chapter of the Association for Computational Linguistics",
    year = "2021",
    address = "Online",
    publisher = "Association for Computational Linguistics",
}

@inproceedings{petroni2019language,
  title={Language Models as Knowledge Bases?},
  author={F. Petroni, T. Rockt{\"{a}}schel, A. H. Miller, P. Lewis, A. Bakhtin, Y. Wu and S. Riedel},
  booktitle={In: Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP), 2019},
  year={2019}
}
```

## Acknowledgements

* [https://github.com/huggingface/pytorch-pretrained-BERT](https://github.com/huggingface/pytorch-pretrained-BERT)
* [https://github.com/allenai/allennlp](https://github.com/allenai/allennlp)
* [https://github.com/pytorch/fairseq](https://github.com/pytorch/fairseq)
* https://github.com/facebookresearch/LAMA
* https://github.com/norakassner/mlama
