# Cultlama

Build relation triples that are more representative to the culture of specific regions as 
opposed to LAMA which is more biased towards western entities.

### Relation predicates and domains currently supported within cultlama
TODO

### Usage
```
# Navigate to the cultlama directory
cd cultlama/

# Query raw triples from Wikidata to (data/cultlama_raw/ directory)
python generate_data_files.py --region REG --n N --rel LIST_OF_RELATIONS

# Generate exhaustive lists of objects for the queried subjects to (data/cultlama/ directory)
python generate_exhaustive_objects.py --rel LIST_OF_RELATIONS

```

### Extending cultlama
It should be fairly possible to extend the dataset to new cultures and languages.

#### Adding a new culture
TODO

### Querying labels of facts in different regions
TODO

