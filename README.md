# pmd-metadata-from-csvw

A repository showing how metadata held within a [CSVW](https://w3c.github.io/csvw/primer/) metadata file could be transformed into a structure accepted by [PublishMyData (PMD)](https://github.com/Swirrl/cogs-issues/wiki/PMD4-metadata). Given a CSVW metadata file containing dataset metadata such as titles, descriptions etc., [`metadata.py`](./metadata.py) will take this as an input and output a `.trig` containing the triple structure expected by PMD.

### Usage:

[`metadata.py`](./metadata.py) contains a class, `PMDMetadata` with a sole method, `from_csvw`. A CSVW metadata file may be specified, after which a `.trig` file will be output.

```python
PMDMetadata.from_csvw("./example.csv-metadata.json")
```

An example [CSV file](./example.csv), [CSVW metadata file](./example.csv-metadata.json) and [`.trig`](./example.trig) output have been included.