# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
import json
import torch
import pickle
from tqdm import tqdm
import modules.base_connector as base
import multiprocessing
from multiprocessing.pool import ThreadPool
import numpy as np
import utils


def get_ranking(
    log_probs, sample, masked_tokens_indecies, candidate_objects_dict,
):
    experiment_result = {}
    objects_probabilities = {}
    objects_true = sample["obj_label"]

    # Make sure the type of objects_true is a list
    if type(objects_true) == type(""):
        objects_true = [objects_true]

    for i, num_masks in enumerate(candidate_objects_dict):
        # Find the range of the masked indecies
        masked_indecies = masked_tokens_indecies[i]

        # Extract the probabilities of subwords in the range of the masked tokens
        predictions = log_probs[i][masked_indecies]

        for object in candidate_objects_dict[num_masks]:
            object_subword_probabiltiies = [
                prediction[subword_id]
                for subword_id, prediction in zip(
                    candidate_objects_dict[num_masks][object], predictions
                )
            ]
            objects_probabilities[object] = np.mean(object_subword_probabiltiies)

    # Sort the dictionary by the probabilities of the candidate objects
    sorted_objects_probabilities = sorted(
        objects_probabilities.items(), key=lambda t: t[1], reverse=True
    )

    # Ranks of all true objects
    ranks = [
        i for i, t in enumerate(sorted_objects_probabilities) if t[0] in objects_true
    ]

    experiment_result["ranks"] = ranks
    experiment_result["prob_true"] = [sorted_objects_probabilities[r] for r in ranks]
    experiment_result["predicted"] = [t[0] for t in sorted_objects_probabilities]
    experiment_result["probs"] = [t[1] for t in sorted_objects_probabilities]

    return experiment_result


def run_evaluation(args, NUM_MASK, candidate_objects_dict, model=None):
    model_name = args.model_name.title()

    # initialize logging
    log_directory = args.full_logdir
    logger = utils.init_logging(log_directory)
    logger.info("\n" + "model name: {}\n".format(model_name) + "\n")

    # dump arguments on file for log
    with open("{}/args.json".format(log_directory), "w") as outfile:
        json.dump(vars(args), outfile)

    # Load the data of a specific relation
    data = utils.load_jsonl(args.dataset_filename)

    if args.lowercase:
        # lowercase all samples
        logger.info("lowercasing all samples...")
        all_samples = utils.lowercase_samples(data, MASK_TOKEN=model.tokenizer.mask_token)
    else:
        # keep samples as they are
        all_samples = data

    # Only keep samples having a uuid!
    # TODO: Why do some samples have no id?!
    # TODO: This filtering should be done on saving the file, not on loading!
    all_samples = [
        sample
        for sample in all_samples
        if "uuid" in sample and sample["sub_label"] and sample["obj_label"]
    ]

    MASK_TOKEN = model.tokenizer.mask_token
    # Form the prompts for the model
    for sample in all_samples:
        # Add the sample's subject to the template
        # TODO: Is there a better way for getting the mask token?
        sample["masked_sentence"] = utils.fill_template_with_values(
            args.template.strip(), sample["sub_label"].strip(), MASK_TOKEN
        )

    samples_batches = utils.batchify(all_samples, args.batch_size)

    # ThreadPool
    num_threads = args.threads
    if num_threads <= 0:
        # use all available threads
        num_threads = multiprocessing.cpu_count()
    pool = ThreadPool(num_threads)
    list_of_results = []

    for i in tqdm(range(len(samples_batches))):
        samples_b = samples_batches[i]
        sentences_b = []
        current_batch_size = len(samples_b)

        # Form multiple versions of the template
        # with different number of masked tokens
        for i, sample in enumerate(samples_b):
            masked_sentences = []
            for num_mask in range(1, NUM_MASK + 1):
                sentence = sample["masked_sentence"]
                sentence = sentence.replace(MASK_TOKEN, MASK_TOKEN * num_mask)
                # TODO: Refactor this!
                sentence = sentence.replace("][", "] [")
                sentence = sentence.replace(">", "> ")
                masked_sentences.append(sentence)
                sentences_b.append([sentence])
            samples_b[i]["masked_sentences"] = masked_sentences

        #  Fill the masks for all the templates of the current batch
        (
            original_log_probs_tensor,
            tokens_ids_list,
            indecies_of_masked_tokens_list,
        ) = model.get_batch_generation(sentences_b, logger=logger)

        # Group the templates of each sample
        dim_reshape = (
            current_batch_size,
            NUM_MASK,
            original_log_probs_tensor.shape[1],
            original_log_probs_tensor.shape[2],
        )
        original_log_probs_tensor = torch.reshape(
            original_log_probs_tensor, dim_reshape
        )
        #  Group the indecies of masked tokens of each sample
        indecies_of_masked_tokens_list = [
            indecies_of_masked_tokens_list[
                sample_index * NUM_MASK : (sample_index + 1) * NUM_MASK
            ]
            for sample_index in range(len(indecies_of_masked_tokens_list))
        ]

        ranking_function_arguments = [
            (
                original_log_probs,
                sample,
                masked_tokens_indecies,
                candidate_objects_dict,
            )
            for sample, original_log_probs, masked_tokens_indecies in zip(
                samples_b, original_log_probs_tensor, indecies_of_masked_tokens_list,
            )
        ]

        # Run the ranking computation in parallel for the samples in the batch!
        batch_ranking_results = pool.starmap(get_ranking, ranking_function_arguments)

        assert len(batch_ranking_results) == len(samples_b)

        for sample, batch_ranking_result in zip(samples_b, batch_ranking_results):
            element = {
                "sample": sample,
                "uuid": sample["uuid"],
                "masked_topk": batch_ranking_result,
            }
            # Add the sample results to a list
            list_of_results.append(element)

    pool.close()
    pool.join()

    # dump pickle with the result of the experiment
    all_results = dict(list_of_results=list_of_results)
    with open("{}/result.pkl".format(log_directory), "wb") as f:
        pickle.dump(all_results, f)
