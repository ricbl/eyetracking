# chexpert-labeler
CheXpert NLP tool to extract observations from radiology reports.

Read more about our project [here](https://stanfordmlgroup.github.io/competitions/chexpert/) and our AAAI 2019 paper [here](https://arxiv.org/abs/1901.07031).

## Prerequisites

Please install following dependencies or use the Dockerized labeler (see below).

1. Clone the [NegBio repository](https://github.com/ncbi-nlp/NegBio):

```Shell
git clone https://github.com/ncbi-nlp/NegBio.git
```

2. Add the NegBio directory to your `PYTHONPATH`:

```Shell
export PYTHONPATH={path to negbio directory}:$PYTHONPATH
```

3. Make the virtual environment:

```Shell
conda env create -f environment.yml
```

4. Activate the virtual environment:

```Shell
conda activate chexpert-label
```

5. Install NLTK data:

```Shell
python -m nltk.downloader universal_tagset punkt wordnet
```

6. Download the `GENIA+PubMed` parsing model:

```python
>>> from bllipparser import RerankingParser
>>> RerankingParser.fetch_and_load('GENIA+PubMed')
```

## Usage
Place reports in a headerless, single column csv `{reports_path}`. Each report must be contained in quotes if (1) it contains a comma or (2) it spans multiple lines. See [sample_reports.csv](https://raw.githubusercontent.com/stanfordmlgroup/chexpert-labeler/master/sample_reports.csv) (with output [labeled_reports.csv](https://raw.githubusercontent.com/stanfordmlgroup/chexpert-labeler/master/labeled_reports.csv))for an example.

```Shell
python label.py --reports_path {reports_path}
```

Run `python label.py --help` for descriptions of all of the command-line arguments.

### Dockerized Labeler

```sh
docker build -t chexpert-labeler:latest .
docker run -v $(pwd):/data chexpert-labeler:latest \
  python label.py --reports_path /data/sample_reports.csv --output_path /data/labeled_reports.csv --verbose
```

## Contributions
This repository builds upon the work of [NegBio](https://negbio.readthedocs.io/en/latest/).

This tool was developed by Jeremy Irvin, Pranav Rajpurkar, Michael Ko, Yifan Yu, and Silviana Ciurea-Ilcus.

## Citing
If you're using the CheXpert labeling tool, please cite [this paper](https://arxiv.org/abs/1901.07031):

```
@inproceedings{irvin2019chexpert,
  title={CheXpert: A large chest radiograph dataset with uncertainty labels and expert comparison},
  author={Irvin, Jeremy and Rajpurkar, Pranav and Ko, Michael and Yu, Yifan and Ciurea-Ilcus, Silviana and Chute, Chris and Marklund, Henrik and Haghgoo, Behzad and Ball, Robyn and Shpanskaya, Katie and others},
  booktitle={Thirty-Third AAAI Conference on Artificial Intelligence},
  year={2019}
}
```
