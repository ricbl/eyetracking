"""Define mention classifier class."""
import logging
from pathlib import Path
from negbio.pipeline import parse, ptb2ud, negdetect
from negbio.neg import semgraph, propagator, neg_detector
from negbio import ngrex
from tqdm import tqdm
from negbio.ngrex import parser,pattern

from constants import *

from negbio.neg import utils, semgraph, propagator

def compile(ngrex):
    """
    Compiles the given expression into a pattern
    
    Args:
        ngrex(str): expression
        
    Returns:
        NgrexPattern: a pattern
    """
    p = parser.yacc.parse(ngrex)
    pattern.validate_names(p)
    return p


def load(filename):
    """
    Read a pattern file
    
    Args:
        filename(str): file name
    
    Returns:
        list: a list of NgexPattern
    """
    patterns = []
    with open(filename) as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            if line[0] == '#':
                continue
            patterns.append(compile(line))
            for conj in ['and','or']:
                patterns.append(compile('{} < {dependency:/conj:'+conj+'/} (' + line + ')'))
    return patterns

class ModifiedDetector(neg_detector.Detector):
    """Child class of NegBio Detector class.

    Overrides parent methods __init__, detect, and match_uncertainty.
    """
    def __init__(self, pre_negation_uncertainty_path,
                 negation_path, post_negation_uncertainty_path):
        self.neg_patterns = load(negation_path)
        self.uncertain_patterns = load(post_negation_uncertainty_path)
        self.preneg_uncertain_patterns\
            = load(pre_negation_uncertainty_path)

    def detect(self, sentence, locs):
        """Detect rules in report sentences.

        Args:
            sentence(BioCSentence): a sentence with universal dependencies
            locs(list): a list of (begin, end)

        Return:
            (str, MatcherObj, (begin, end)): negation or uncertainty,
            matcher, matched annotation
        """
        # print(sentence)
        # print(locs)
        logger = logging.getLogger(__name__)

        try:
            g = semgraph.load(sentence)
            propagator.propagate(g)
        except Exception:
            logger.exception('Cannot parse dependency graph ' +
                             f'[offset={sentence.offset}]')
            raise
        else:
            for loc in locs:
                for node in neg_detector.find_nodes(g, loc[0], loc[1]):
                    # Match pre-negation uncertainty rules first.
                    preneg_m = self.match_prenegation_uncertainty(g, node)
                    if preneg_m:
                        yield UNCERTAINTY, preneg_m, loc
                    else:
                        # Then match negation rules.
                        # print(node)
                        # print(g)
                        neg_m = self.match_neg(g, node)
                        # print(neg_m)
                        if neg_m:
                            # print(NEGATION, neg_m, loc)
                            yield NEGATION, neg_m, loc
                        else:
                            # Finally match post-negation uncertainty rules.
                            postneg_m = self.match_uncertainty(g, node)
                            if postneg_m:
                                yield UNCERTAINTY, postneg_m, loc

    def match_uncertainty(self, graph, node):
        for pattern_ in self.uncertain_patterns:
            for m in pattern_.finditer(graph):
                n0 = m.group(0)
                if n0 == node:
                    return m

    def match_prenegation_uncertainty(self, graph, node):
        for pattern_ in self.preneg_uncertain_patterns:
            for m in pattern_.finditer(graph):
                n0 = m.group(0)
                if n0 == node:
                    return m

    def match_neg(self, graph, node):
        """
        Returns a matcher
        """
        
        for pattern_ in self.neg_patterns:
            for m in pattern_.finditer(graph):
                # print(m.pattern)
                n0 = m.group(0)
                if n0 == node:
                    try:
                        key = m.get('key')
                        if semgraph.has_out_edge(graph, key, ['neg']):
                            continue
                    except:
                        pass
                    if semgraph.has_out(graph, n0, ['new'], ['amod']):
                        continue
                    # print(m)
                    return m
        # print('la')
        return None

class Classifier(object):
    """Classify mentions of observations from radiology reports."""
    def __init__(self, pre_negation_uncertainty_path, negation_path,
                 post_negation_uncertainty_path, verbose=False):
        self.parser = parse.NegBioParser(model_dir=PARSING_MODEL_DIR)
        lemmatizer = ptb2ud.Lemmatizer()
        self.ptb2dep = ptb2ud.NegBioPtb2DepConverter(lemmatizer, universal=True)

        self.verbose = verbose

        self.detector = ModifiedDetector(pre_negation_uncertainty_path,
                                         negation_path,
                                         post_negation_uncertainty_path)

    def classify(self, collection):
        """Classify each mention into one of
        negative, uncertain, or positive."""
        documents = collection.documents
        if self.verbose:
            print("Classifying mentions...")
            documents = tqdm(documents)
        for document in documents:
            # Parse the impression text in place.
            self.parser.parse_doc(document)
            # Add the universal dependency graph in place.
            self.ptb2dep.convert_doc(document)
            # Detect the negation and uncertainty rules in place.
            negdetect.detect(document, self.detector)
            # print(document)
            
            # for passage in document.passages:
            #     # print(passage)
            #     for sentence in passage.sentences:
            #         dict_ids = {}
            #         for annotation in sentence.annotations:
            #             dict_ids[annotation.id] = annotation.text
            #         for relation in sentence.relations:
            #             for i, node in enumerate(relation.nodes):
            #                 if dict_ids[node.refid] == 'normal':# and node.role=='dependant':
            #                     print(relation.infons, '>', dict_ids[relation.nodes[1-i].refid], '>', sentence.text)
                
            # To reduce memory consumption, remove sentences text.
            del document.passages[0].sentences[:]
