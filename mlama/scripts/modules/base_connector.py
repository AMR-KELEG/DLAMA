# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
import torch


class Base_Connector:
    def __init__(self, device_name):

        # these variables should be initialized
        self.vocab = None

        # This defines where the device where the model is. Changed by try_cuda.
        self._model_device = torch.device(device_name)

    def optimize_top_layer(self, vocab_subset):
        """
        optimization for some LM
        """
        pass

    def _init_inverse_vocab(self):
        self.inverse_vocab = {w: i for i, w in enumerate(self.vocab)}

    def try_cuda(self):
        """Move model to GPU if one is available."""
        self._cuda()

    def _cuda(self):
        """Move model to GPU."""
        raise NotImplementedError

    def init_indices_for_filter_logprobs(self, vocab_subset, logger=None):
        index_list = []
        new_vocab_subset = []
        for word in vocab_subset:
            if word in self.inverse_vocab:
                inverse_id = self.inverse_vocab[word]
                index_list.append(inverse_id)
                new_vocab_subset.append(word)
            else:
                msg = "word {} from vocab_subset not in model vocabulary!".format(word)
                if logger is not None:
                    logger.warning(msg)
                else:
                    print("WARNING: {}".format(msg))

        # 1. gather correct indices
        indices = torch.as_tensor(index_list)
        return indices, index_list

    def filter_logprobs(self, log_probs, indices):
        new_log_probs = log_probs.index_select(dim=2, index=indices)
        return new_log_probs

    def get_id(self, string):
        raise NotImplementedError()

    def get_generation(self, sentences, logger=None):
        [log_probs], [token_ids], [masked_indices] = self.get_batch_generation(
            [sentences], logger=logger, try_cuda=False
        )
        return log_probs, token_ids, masked_indices

    def get_batch_generation(self, sentences_list, logger=None, try_cuda=True):
        raise NotImplementedError()
