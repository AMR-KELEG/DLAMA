import os
import json
import time
import openai
import argparse
from tqdm import tqdm
from pathlib import Path

openai.api_key = os.getenv("OPENAI_API_KEY")


PROMPTS = {
    "P30": {
        "ar": 'أين يقع "{}"؟ أجب باسم قارة فقط',
        "en": 'Where is "{}" located in? Reply with a name of a continent only.',
    },
    "P36": {
        "ar": 'ما هي عاصمة "{}"؟ أجب باسم المدينة فقط',
        "en": 'What is the capital of "{}"? Reply with the name of the city only.',
    },
    "P37": {
        "ar": 'ما هي اللغة الرسمية ل "{}"؟ أجب باسم لغة فقط',
        "en": 'What is the official language of "{}"? Reply with the language name only.',
    },
    "P47": {
        "ar": 'ما هي الدولة التي تشترك حدودها مع "{}"؟ أجب باسم دولة فقط',
        "en": 'What is the country that shares border with "{}"? Reply with a country name only.',
    },
    "P190": {
        "ar": 'ما هي المدينة التوأم لمدينة "{}"؟ أجب باسم المدينة فقط',
        "en": 'What is the twin city of "{}"? Reply with the name of the city only.',
    },
    "P530": {
        "ar": 'ما هي الدولة التي تقيم علاقات دبلوماسية مع "{}"؟ أجب باسم دولة فقط',
        "en": 'What is the country that maintains dimplomatic relations with "{}"? Reply with a country name only.',
    },
    "P1376": {
        "ar": 'ما هي الدولة التي عاصمتها "{}"؟ أجب باسم دولة فقط',
        "en": 'What is the country of which the capital is "{}"? Reply with a country name only.',
    },
}


SYSTEM_DESCRIPTION = {"ar": "تعامل كأنك موسوعة.", "en": "You are an encyclopedia."}


def load_jsonl_file(file_path):
    """Load a jsonl file."""
    with open(file_path, "r") as f:
        triples = [json.loads(l) for l in f]
    return triples


def save_jsonl_file(file_path, tuples):
    """Save tuples as a jsonl file."""
    with open(file_path, "w") as f:
        for t in tuples:
            f.write(json.dumps(t) + "\n")


def get_gpt_completion(predicate, entity, lang):
    """Answer a question using OpenAI's API."""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_DESCRIPTION[lang]},
            {"role": "user", "content": PROMPTS[predicate][lang].format(entity)},
        ],
    )
    return [c["message"]["content"] for c in response.to_dict()["choices"]]


def probe_gpt_using_DLAMA_jsonl(predicate, lang, input_file_path):
    """Probe GPT using a DLAMA predicate and save the tuples with the answers to a jsonl file."""
    output_triples = []
    for triple in tqdm(load_jsonl_file(input_file_path)[:3]):
        # Handle rate-limiting in a naive way!
        while True:
            try:
                time.sleep(1)
                choices = get_gpt_completion(predicate, triple["sub_label"], lang)
                break
            except:
                print("Rate-limited")
                # TODO: Tune the time to wait before sending another request
                time.sleep(30)

        triple["gpt3.5-turbo_choices"] = choices
        output_triples.append(triple)
    return output_triples


def compute_accuracy(tuples):
    """Measure the GPT3.5 model's accuracy."""
    n_correct = int(0)
    n_correct_substr = int(0)
    n_tuples = len(tuples)
    for t in tuples:
        gpt_choices = t["gpt3.5-turbo_choices"]
        obj_labels = t["obj_label"]

        # An answer is correct if it is one of candidate answers
        n_correct += int(any([c in obj_labels for c in gpt_choices]))

        # An answer is correct if any of the candidate answers is a substr of the answer
        n_correct_substr += int(any([o in c for o in obj_labels for c in gpt_choices]))

    return {
        "Total number of tuples": n_tuples,
        "# of correct answers (Exact match)": n_correct,
        "% of correct answers (Exact match)": round(100 * n_correct / n_tuples, 1),
        "# of correct answers (Overlap)": n_correct_substr,
        "% of correct answers (Overlap)": round(100 * n_correct_substr / n_tuples, 1),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Probe GPT using DLAMA.")
    parser.add_argument(
        "--predicates",
        nargs="*",
        required=True,
        help="A white-space separated list DLAMA predicates (e.g.: 'P17 P20').",
    )
    parser.add_argument(
        "--langs",
        nargs="*",
        default=None,
        required=True,
        help="A white-space separated list of Wikipedia languages (e.g.: 'en ko').",
    )
    parser.add_argument(
        "--dataset_dir", required=True, help="A directory of jsonl files."
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="A directory to store output jsonl files to.",
    )
    args = parser.parse_args()

    # Create the output directory
    os.makedirs(args.output_dir, exist_ok=True)

    for predicate in args.predicates:
        for lang in args.langs:
            for input_file_path in sorted(
                Path(args.dataset_dir, lang).glob(f"{predicate}_*.jsonl")
            ):
                base_filename = input_file_path.name
                output_file_path = str(Path(args.output_dir, base_filename))

                gpt_tuples = probe_gpt_using_DLAMA_jsonl(
                    predicate, lang, input_file_path
                )
                print(base_filename)
                print(compute_accuracy(gpt_tuples))

                save_jsonl_file(output_file_path, gpt_tuples)
