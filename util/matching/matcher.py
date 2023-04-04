from typing import Annotated
from typing import List
import numpy as np

from fastapi import APIRouter
from fastapi import Body

from schemas.requests.text import RawFile, Instrument, MatchParameters
from util.parsing.files_to_instruments import convert_files_to_instruments
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')


def convert_texts_to_vector(texts: list):
    embeddings = model.encode(list(texts))
    return [embeddings[i] for i in range(embeddings.shape[0])]

def match_instruments(instruments: List[Instrument], parameters : MatchParameters):
    texts = []
    negated_texts = []
    instrument_ids = []
    question_indices = []

    for instrument in instruments:
        for question_idx, question in enumerate(instrument.questions):
            texts.append(question.question_text)
            #negated = negate(question.question_text, instrument.language) # TODO
            negated = question.question_text
            negated_texts.append(negated)
            instrument_ids.append(instrument.instrument_id)
            question_indices.append(question_idx)

    vectors = convert_texts_to_vector(texts)
    vectors_neg = convert_texts_to_vector(negated_texts)

    pairwise_similarity = util.cos_sim(vectors, vectors).numpy()
    pairwise_similarity_neg1 = util.cos_sim(vectors_neg, vectors).numpy()
    pairwise_similarity_neg2 = util.cos_sim(vectors, vectors_neg).numpy()
    pairwise_similarity_neg_mean = np.mean([pairwise_similarity_neg1, pairwise_similarity_neg2], axis=0)

    similarity_polarity = np.sign(pairwise_similarity - pairwise_similarity_neg_mean)
    # Make sure that any 0's in polarity are converted to 1's
    where_0 = np.where(similarity_polarity == 0)
    similarity_polarity[where_0] = 1

    similarity_max = np.max([pairwise_similarity, pairwise_similarity_neg_mean], axis=0)
    similarity_with_polarity = similarity_max * similarity_polarity

    return similarity_with_polarity