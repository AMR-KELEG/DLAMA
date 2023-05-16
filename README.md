# DLAMA
The repository for the `DLAMA: A Framework for Curating Culturally Diverse Facts for Probing
the Knowledge of Pretrained Language Models` paper accepted to `ACL 2023 - Findings`.

The codebase allows for curating relation triples that are more representative of the culture of specific regions as opposed to LAMA which is more biased towards western entities.

- [DLAMA](#dlama)
  - [Usage](#usage)
    - [1. Create conda environment and install requirements](#1-create-conda-environment-and-install-requirements)
    - [2. Download mLAMA](#2-download-mlama)
    - [3. Build DLAMA](#3-build-dlama)
    - [4. Run the experiments](#4-run-the-experiments)
  - [Relation predicates currently supported within DLAMA](#relation-predicates-currently-supported-within-dlama)
  - [Adding new countries/regions to DLAMA](#adding-new-countriesregions-to-dlama)
  - [Utilities](#utilities)
  - [References](#references)
  - [Acknowledgements](#acknowledgements)

## Usage
### 1. Create conda environment and install requirements
```
conda create -n dlama -y python=3.7 && conda activate dlama
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

### 3. Build DLAMA
```
# Navigate to the dlama directory
cd dlama/

# Query raw triples from Wikidata to (data/dlama_raw/ directory)
python generate_data_files.py --region REG --n N --langs LIST_OF_LABELS_LANGS --rel LIST_OF_RELATIONS

# Generate exhaustive lists of objects for the queried subjects to (data/dlama/ directory)
python generate_exhaustive_objects.py --langs LIST_OF_LABELS_LANGS --rel LIST_OF_RELATIONS

```

### 4. Run the experiments
- Note: The scripts within the `mlama` subdirectory are forked from https://github.com/norakassner/mlama and adapted accordingly.
```bash
cd ../mlama # Navigate to the mlama directory within the repository
python scripts/run_prompting_experiment.py --lang "ar" --dlama --dataset_dir DATASET_BASE_DIR \
       --templates_file_path TEMPLATES_FILE_PATH --device DEVICE_NAME --rel RELATIONS --models MODELS
```

## Relation predicates currently supported within DLAMA
Relation predicate| Relation label
--- | ---
P17 | Country 
P19 | Place of birth 
P20 | Place of death 
P27 | Country of citizenship 
P30 | Continent 
P36 | Capital 
P37 | Official language 
P47 | Shares border with 
P103 | Native language 
P106 | Occupation 
P136 | Genre 
P190 | Sister city 
P264 | Record label 
P364 | Original language of work 
P449 | Original network 
P495 | Country of origin 
P530 | Diplomatic relation 
P1303 | Instrument 
P1376 | Capital of 
P1412 | Languages spoken or published 

## Adding new countries/regions to DLAMA

1. Add the list of country names to `dlama/constants.py`.
```
BOTSWANA = "Botswana"
ESWATINI = "Eswatini"
LESOTHO = "Lesotho"
MADAGASCAR = "Madagascar"
NAMIBIA = "Namibia"
SOUTH_AFRICA = "South Africa"
```

2. Create a list of the new countries representing the region in `dlama/constants.py`.
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

3. Add the languages of Wikipedia that are related to each country to the `REGIONS_LANGS` variable in `dlama/constants.py`.
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

4. Add the Wikidata URIs for each country to the `"region_country"` key of the `FILTERS_DICTIONARY` variable in `dlama/filters.py`.
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

5. Add the region as a new region in the `REGIONS` dictionary of `dlama/generate_data_files.py`.
```
  REGIONS ={
    ...
    "SOUTHERN_AFRICA": SOUTHERN_AFRICA,
  }
```

6. Query facts related to the new region
```
$ python dlama/generate_data_files.py --region SOUTHERN_AFRICA --n 6 --rel P36 --langs fr en
$ python dlama/generate_exhaustive_objects.py --rel P36 --langs en fr
```

7. Inspect the queried facts
```
$ cat data/dlama/en/P36_geography_SOUTHERN_AFRICA.jsonl
{"sub_uri": "Q258", "obj_uri": ["Q37701", "Q3926", "Q5465"], "sub_label": "South Africa", "obj_label": ["Bloemfontein", "Pretoria", "Cape Town"], "uuid": "P36_geography_SOUTHERN_AFRICA_0"}
{"sub_uri": "Q1019", "obj_uri": ["Q3915"], "sub_label": "Madagascar", "obj_label": ["Antananarivo"], "uuid": "P36_geography_SOUTHERN_AFRICA_1"}
{"sub_uri": "Q1030", "obj_uri": ["Q3935"], "sub_label": "Namibia", "obj_label": ["Windhoek"], "uuid": "P36_geography_SOUTHERN_AFRICA_2"}
{"sub_uri": "Q963", "obj_uri": ["Q3919"], "sub_label": "Botswana", "obj_label": ["Gaborone"], "uuid": "P36_geography_SOUTHERN_AFRICA_3"}
{"sub_uri": "Q1050", "obj_uri": ["Q101418", "Q3904"], "sub_label": "Eswatini", "obj_label": ["Lobamba", "Mbabane"], "uuid": "P36_geography_SOUTHERN_AFRICA_4"}
{"sub_uri": "Q1013", "obj_uri": ["Q3909"], "sub_label": "Lesotho", "obj_label": ["Maseru"], "uuid": "P36_geography_SOUTHERN_AFRICA_5"}

$ cat data/dlama/fr/P36_geography_SOUTHERN_AFRICA.jsonl
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
