from typing import TextIO, Union, Optional

from sacremoses import MosesPunctNormalizer, MosesTokenizer
from sacremoses.util import xml_unescape
from subword_nmt.apply_bpe import BPE as subword_nmt_bpe, read_vocabulary
from transliterate import translit

from .utils import BPECodesAdapter

__all__ = ['Tokenizer', 'BPE']

###############################################################################
#
# Tokenizer
#
###############################################################################


class Tokenizer:
    """
    Tokenizer.

    Args:
        lang (str): the language code (ISO 639-1) of the texts to tokenize
        lower_case (bool, optional): if True, the texts are lower-cased before being tokenized.
            Defaults to True.
        romanize (bool or None, optional): if True, the texts are romanized.
            Defaults to None (romanization enabled based on input language).
        descape (bool, optional): if True, the XML-escaped symbols get de-escaped.
            Default to False.
    """

    def __init__(self,
                 lang: str = 'en',
                 lower_case: bool = True,
                 romanize: Optional[bool] = None,
                 descape: bool = False):
        assert lower_case, 'lower case is needed by all the models'

        if lang in ('cmn', 'wuu', 'yue'):
            lang = 'zh'
        if lang == 'jpn':
            lang = 'ja'

        if lang == 'zh':
            raise NotImplementedError('jieba is not yet implemented')
        if lang == 'ja':
            raise NotImplementedError('mecab is not yet implemented')

        self.lang = lang
        self.lower_case = lower_case
        self.romanize = romanize if romanize is not None else lang == 'el'
        self.descape = descape

        self.normalizer = MosesPunctNormalizer(lang=lang)
        self.tokenizer = MosesTokenizer(lang=lang)

    def tokenize(self, text: str) -> str:
        """Tokenizes a text and returns the tokens as a string"""

        # REM_NON_PRINT_CHAR
        # not implemented

        # NORM_PUNC
        text = self.normalizer.normalize(text)

        # DESCAPE
        if self.descape:
            text = xml_unescape(text)

        # MOSES_TOKENIZER

        # see: https://github.com/facebookresearch/LASER/issues/55#issuecomment-480881573
        text = self.tokenizer.tokenize(text,
                                       return_str=True,
                                       escape=False,
                                       aggressive_dash_splits=False)

        # jieba
        # MECAB
        # not implemented

        if self.romanize:
            text = translit(text, self.lang, reversed=True)

        if self.lower_case:
            text = text.lower()

        return text


###############################################################################
#
# Apply BPE
#
###############################################################################


class BPE:
    """
    BPE encoder.

    Args:
        bpe_codes (str or TextIO): the path to LASER's BPE codes (``93langs.fcodes``),
            or a text-mode file object.
        bpe_codes (str or TextIO): the path to LASER's BPE vocabulary (``93langs.fvocab``),
            or a text-mode file object.
    """

    def __init__(self, bpe_codes: Union[str, TextIO],
                 bpe_vocab: Union[str, TextIO]):

        f_bpe_codes = None
        f_bpe_vocab = None

        try:
            if isinstance(bpe_codes, str):
                f_bpe_codes = open(bpe_codes, 'r', encoding='utf-8')
            if isinstance(bpe_vocab, str):
                f_bpe_vocab = open(bpe_vocab, 'r', encoding='utf-8')

            self.bpe = subword_nmt_bpe(codes=BPECodesAdapter(f_bpe_codes
                                                             or bpe_codes),
                                       vocab=read_vocabulary(f_bpe_vocab
                                                             or bpe_vocab,
                                                             threshold=None))
            self.bpe.version = (0, 2)

        finally:
            if f_bpe_codes:
                f_bpe_codes.close()
            if f_bpe_vocab:
                f_bpe_vocab.close()

    def encode_tokens(self, sentence_tokens: str) -> str:
        """Returns the BPE-encoded sentence from a tokenized sentence"""
        return self.bpe.process_line(sentence_tokens)
