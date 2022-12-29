"""Trajectory class -- calculates and represents the semantic trajectory of a text string."""

import os
import numpy as np
import openai
import transformers

DEFAULT_ENGINE = 'text-embedding-ada-002'
DEFAULT_OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

os.environ['TOKENIZERS_PARALLELISM'] = 'false'


class TrajectoryException(Exception):
    pass


class Trajectory:
    """Semantic trajectory of a text string. Construct, calculate once, then use read-only properties."""
    def __init__(self, text, engine=DEFAULT_ENGINE,
                 api_key=DEFAULT_OPENAI_API_KEY, tokenizer=transformers.GPT2TokenizerFast.from_pretrained('gpt2')):
        """
        Construct semantic trajectory object. Call calculate() before using attributes other than init parameters.

        Keyword arguments:
        engine      --  OpenAI embedding model by name (default 'text-embedding-ada-002')
        api_key     --  OpenAI api key (default OPENAI_API_KEY os environment variable)
        tokenizer   --  Hugging Face fast transformer (default GPT2TokenizerFast)

        Calculated properties:
        encoding    --  encoding produced by tokenizer
        ends        --  list of indexes (in original text) one past each token
        delta_mus   --  list per token, delta between semantic embedding of prev token (init zeros) and curr token
        """
        self._text = text
        self._engine = engine
        self._api_key = api_key
        self._tokenizer = tokenizer

        self._encoding = None
        self._ends = None
        self._delta_mus = []

    @property
    def text(self):
        return self._text

    @property
    def encoding(self):
        return self._encoding

    @property
    def ends(self):
        return self._ends

    @property
    def delta_mus(self):
        return self._delta_mus

    def calculate(self):
        """Compute the encoding, ends, and delta_mus."""
        if self._encoding is not None:
            raise TrajectoryException(f'{self.__repr__()} was already calculated.')
        if self._tokenizer.is_fast is False:
            raise TrajectoryException(f'{self.__repr__()} requires a Hugging Face fast tokenizer.')

        self._encoding = self._tokenizer(self._text)
        self._ends = [self._encoding.token_to_chars(i)[1] for i, _ in enumerate(self._encoding['input_ids'])]

        mu_prev = None
        for end in self._ends:
            state = self._text[:end]
            mu = np.array(openai.Embedding.create(input=[state], engine=self._engine)['data'][0]['embedding'])
            if mu_prev is None:
                mu_prev = np.zeros(len(mu))
            self._delta_mus.append(mu - mu_prev)
            mu_prev = mu
