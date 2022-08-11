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
python scripts/run_prompting_experiment.py --lang "ar" --cultlama --dataset_dir DATASET_BASE_DIR
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
