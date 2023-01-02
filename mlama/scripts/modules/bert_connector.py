# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
import torch
import numpy as np
from modules.base_connector import *
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForMaskedLM, BasicTokenizer


class CustomBaseTokenizer(BasicTokenizer):
    def __init__(self, do_lower_case, MASK_token):
        super.__init__(do_lower_case=do_lower_case)
        self.MASK = MASK_token

    def tokenize(self, text):
        """Tokenizes a piece of text."""
        text = self._clean_text(text)
        # This was added on November 1st, 2018 for the multilingual and Chinese
        # models. This is also applied to the English models now, but it doesn't
        # matter since the English models were not trained on any Chinese data
        # and generally don't have any Chinese data in them (there are Chinese
        # characters in the vocabulary because Wikipedia does have some Chinese
        # words in the English Wikipedia.).
        text = self._tokenize_chinese_chars(text)
        orig_tokens = text.split()
        split_tokens = []
        for token in orig_tokens:

            # pass MASK forward
            if self.MASK in token:
                split_tokens.append(self.MASK)
                if token != self.MASK:
                    remaining_chars = token.replace(self.MASK, "").strip()
                    if remaining_chars:
                        split_tokens.append(remaining_chars)
                continue

            if self.do_lower_case:
                token = token.lower()
                token = self._run_strip_accents(token)
            split_tokens.extend(self._run_split_on_punc(token))

        output_tokens = " ".join(split_tokens).split()
        return output_tokens


class Bert(Base_Connector):
    def __init__(self, bert_model_name, device):
        super().__init__(device)

        # When using a cased model, make sure to pass do_lower_case=False directly to BaseTokenizer
        do_lower_case = False
        if "uncased" in bert_model_name:
            do_lower_case = True

        # Load pre-trained model tokenizer (vocabulary)
        self.tokenizer = AutoTokenizer.from_pretrained(bert_model_name)

        # original vocab
        self.map_indices = None
        self.vocab = list(self.tokenizer.get_vocab())
        self._init_inverse_vocab()

        # Add custom tokenizer to avoid splitting the ['MASK'] token
        custom_basic_tokenizer = CustomBaseTokenizer(
            do_lower_case=do_lower_case, MASK_token=self.tokenizer.mask_token
        )
        self.tokenizer.basic_tokenizer = custom_basic_tokenizer

        # Load pre-trained model (weights)
        # ... to get prediction/generation
        self.masked_bert_model = AutoModelForMaskedLM.from_pretrained(bert_model_name)
        self.masked_bert_model.eval()

        # ... to get hidden states
        try:
            self.bert_model = self.masked_bert_model.bert
            self.pad_id = self.inverse_vocab[self.tokenizer._pad_token]
            self.unk_index = self.inverse_vocab[self.tokenizer._unk_token]
        except:
            self.bert_model = self.masked_bert_model.roberta
            self.pad_id = self.inverse_vocab[self.tokenizer._pad_token]
            self.unk_index = self.inverse_vocab[self.tokenizer._unk_token]

    def get_id(self, string):
        tokenized_text = self.tokenizer.tokenize(string)
        indexed_string = self.tokenizer.convert_tokens_to_ids(tokenized_text)
        if self.map_indices is not None:
            # map indices to subset of the vocabulary
            indexed_string = self.convert_ids(indexed_string)

        return indexed_string

    def __get_input_tensors_batch(self, sentences_list):
        tokens_tensors_list = []
        segments_tensors_list = []
        masked_indices_list = []
        tokenized_text_list = []
        max_tokens = 0
        for sentences in sentences_list:
            (
                tokens_tensor,
                segments_tensor,
                masked_indices,
                tokenized_text,
            ) = self.__get_input_tensors(sentences)
            tokens_tensors_list.append(tokens_tensor)
            segments_tensors_list.append(segments_tensor)
            masked_indices_list.append(masked_indices)
            tokenized_text_list.append(tokenized_text)
            # assert(tokens_tensor.shape[1] == segments_tensor.shape[1])
            if tokens_tensor.shape[1] > max_tokens:
                max_tokens = tokens_tensor.shape[1]
        # print("MAX_TOKENS: {}".format(max_tokens))
        # apply padding and concatenate tensors
        # use [PAD] for tokens and 0 for segments
        final_tokens_tensor = None
        final_segments_tensor = None
        final_attention_mask = None
        for tokens_tensor, segments_tensor in zip(
            tokens_tensors_list, segments_tensors_list
        ):
            dim_tensor = tokens_tensor.shape[1]
            pad_lenght = max_tokens - dim_tensor
            attention_tensor = torch.full([1, dim_tensor], 1, dtype=torch.long)
            if pad_lenght > 0:
                pad_1 = torch.full([1, pad_lenght], self.pad_id, dtype=torch.long)
                pad_2 = torch.full([1, pad_lenght], 0, dtype=torch.long)
                attention_pad = torch.full([1, pad_lenght], 0, dtype=torch.long)
                tokens_tensor = torch.cat((tokens_tensor, pad_1), dim=1)
                segments_tensor = torch.cat((segments_tensor, pad_2), dim=1)
                attention_tensor = torch.cat((attention_tensor, attention_pad), dim=1)
            if final_tokens_tensor is None:
                final_tokens_tensor = tokens_tensor
                final_segments_tensor = segments_tensor
                final_attention_mask = attention_tensor
            else:
                final_tokens_tensor = torch.cat(
                    (final_tokens_tensor, tokens_tensor), dim=0
                )
                final_segments_tensor = torch.cat(
                    (final_segments_tensor, segments_tensor), dim=0
                )
                final_attention_mask = torch.cat(
                    (final_attention_mask, attention_tensor), dim=0
                )

        return (
            final_tokens_tensor,
            final_segments_tensor,
            final_attention_mask,
            masked_indices_list,
            tokenized_text_list,
        )

    def __get_input_tensors(self, sentences):

        if len(sentences) > 1:
            print(sentences)
            raise ValueError("Only one sentence is expected!")

        first_tokenized_sentence = self.tokenizer.tokenize(sentences[0])
        first_segment_id = np.zeros(len(first_tokenized_sentence), dtype=int).tolist()

        # add [SEP] token at the end
        try:
            first_tokenized_sentence.append(self.tokenizer.sep_token)
        except Exception as e:
            print("Problem with adding separator token!")
            raise e
        first_segment_id.append(0)

        tokenized_text = first_tokenized_sentence
        segments_ids = first_segment_id

        # add [CLS] token at the beginning
        try:
            tokenized_text.insert(0, self.tokenizer.sep_token)
        except Exception as e:
            print("Problem with adding CLS token!")
            raise e
        segments_ids.insert(0, 0)

        # look for masked indices
        masked_indices = []
        for i in range(len(tokenized_text)):
            token = tokenized_text[i]
            if token == MASK:
                masked_indices.append(i)

        indexed_tokens = self.tokenizer.convert_tokens_to_ids(tokenized_text)

        # Convert inputs to PyTorch tensors
        tokens_tensor = torch.tensor([indexed_tokens])
        segments_tensors = torch.tensor([segments_ids])

        return tokens_tensor, segments_tensors, masked_indices, tokenized_text

    def __get_token_ids_from_tensor(self, indexed_string):
        token_ids = []
        if self.map_indices is not None:
            # map indices to subset of the vocabulary
            indexed_string = self.convert_ids(indexed_string)
            token_ids = np.asarray(indexed_string)
        else:
            token_ids = indexed_string
        return token_ids

    #  TODO: Move this to a configuration file
    def _cuda(self):
        self.masked_bert_model.to(self._model_device)

    def get_batch_generation(self, sentences_list, logger=None, try_cuda=True):
        if not sentences_list:
            return None
        if try_cuda:
            self.try_cuda()

        (
            tokens_tensor,
            segments_tensor,
            attention_mask_tensor,
            masked_indices_list,
            tokenized_text_list,
        ) = self.__get_input_tensors_batch(sentences_list)

        if logger is not None:
            logger.debug("\n{}\n".format(tokenized_text_list))

        with torch.no_grad():
            logits = self.masked_bert_model(
                input_ids=tokens_tensor.to(self._model_device),
                token_type_ids=segments_tensor.to(self._model_device),
                attention_mask=attention_mask_tensor.to(self._model_device),
            ).logits
            log_probs = F.log_softmax(logits, dim=-1).cpu()
        token_ids_list = []
        for indexed_string in tokens_tensor.numpy():
            token_ids_list.append(self.__get_token_ids_from_tensor(indexed_string))

        return log_probs, token_ids_list, masked_indices_list
