"""Entry-point script to label radiology reports."""
import pandas as pd

from args import ArgParser
from loader import Loader
from stages import Extractor, Classifier, Aggregator
from constants import *


def write(reports, labels, locations, output_path, verbose=False):
    """Write labeled reports to specified path."""
    labeled_reports = pd.DataFrame({REPORTS: reports})
    for index, category in enumerate(CATEGORIES):
        labeled_reports[category] = labels[:, index]
        locations[category]
        labeled_reports[category+'_location'] = locations[category]

    if verbose:
        print(f"Writing reports and labels to {output_path}.")
    labeled_reports[[REPORTS] + CATEGORIES + [category+'_location' for category in CATEGORIES]].to_csv(output_path,
                                                   index=False)


def label(args):
    """Label the provided report(s)."""

    loader = Loader(args.reports_path, args.extract_impression)

    extractor = Extractor(args.mention_phrases_dir,
                          args.unmention_phrases_dir,
                          verbose=args.verbose)
    classifier = Classifier(args.pre_negation_uncertainty_path,
                            args.negation_path,
                            args.post_negation_uncertainty_path,
                            verbose=args.verbose)
    aggregator = Aggregator(CATEGORIES,
                            verbose=args.verbose)

    # Load reports in place.
    loader.load()
    # Extract observation mentions in place.
    extractor.extract(loader.collection)
    # Classify mentions in place.
    classifier.classify(loader.collection)
    # Aggregate mentions to obtain one set of labels for each report.
    labels, locations = aggregator.aggregate(loader.collection)

    write(loader.reports, labels, locations, args.output_path, args.verbose)


if __name__ == "__main__":
    parser = ArgParser()
    label(parser.parse_args())
