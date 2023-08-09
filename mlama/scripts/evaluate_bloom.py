import os
import re
import json
from tqdm import tqdm
from pathlib import Path
from argparse import ArgumentParser
from transformers import AutoModelForCausalLM, AutoTokenizer


PROMPTS = {
    "P1412": {
        "zh-cn": "问题: {}用什么国家语言交流? 答案是:",
        "en": "Question: What language does {} communicate? The answer is:",
        "ar": "سؤال: ما هي لغة {}؟ الإجابة: ",
    },
    "P1376": {
        "zh-cn": "问题: 哪个国家的首都是{}? 答案是:",
        "en": "Question: Which country has {} as its capital? The answer is:",
        "ar": "سؤال: ما الدولة التي عاصمتها هي {}؟ الإجابة:",
    },
    "P1303": {
        "zh-cn": "问题：{}玩什么乐器？答案是：",
        "en": "Question: What instrument does {} play? The answer is:",
        "ar": "سؤال:ما هي الألة التي يلعبها {}؟ الإجابة: ",
    },
    "P530": {
        "zh-cn": "问题：与{}保持外交关系的国家是? 答案是：",
        "en": "Question: What is the country that maintains diplomatic relations with {}? The answer is:",
        "ar": "سؤال: ما هي الدولة التي تمتلك علاقة دبلوماسية مع {}؟ الإجابة: ",
    },
    "P495": {
        "zh-cn": "问题：哪一个国家创造了{}? 答案是：",
        "en": "Question: Which country created {}? The answer is:",
        "ar": "سؤال: ما هي الدولة التي اخترعت {}؟ الإجابة: ",
    },
    "P449": {
        "zh-cn": "问题：{}最初是在哪里播出的? 答案是：",
        "en": "Question: Where was {} originally aired on? The answer is:",
        "ar": "سؤال: أين تم بث {}؟ الإجابة: ",
    },
    "P364": {
        "zh-cn": "问题：{}的起源语言是什么? 答案是：",
        "en": "Question: What is the language of origin of {}? The answer is:",
        "ar": "سؤال:ما هي اللغة الأصلية ل '{}'؟ الإجابة: ",
    },
    "P264": {
        "zh-cn": "问题：{}与哪个唱片公司签约? 答案是:",
        "en": "Question: Which record label is {} signed to? The answer is:",
        "ar": "سؤال: ما هي العلامة الموسيقية التي يمثلها {}؟ الإجابة: ",
    },
    "P190": {
        "zh-cn": "问题：{}的姐妹城市是? 答案是：",
        "en": "Question: What is the sister city of {}? The answer is: ",
        "ar": "سؤال: ما هي المدينة التوأم ل {}؟ الإجابة: ",
    },
    "P136": {
        "zh-cn": "问题：{}与哪种音乐流派有关？答案是:",
        "en": "Question: Which musical genre is {} associated with? The answer is:",
        "ar": "سؤال: أي نوع من الموسيقي يعزف {}؟ الإجابة: ",
    },
    "P17": {
        "zh-cn": "问题：{}位于哪个国家？答案是：",
        "en": "Question: In which country is {} located? The answer is: ",
        "ar": "سؤال: في أي دولة تقع {}؟ الإجابة: ",
    },
    "P19": {
        "zh-cn": "问题：{}出生于哪个城市？答案是：",
        "en": "Question: In which city was {} born? The answer is: ",
        "ar": "سؤال: أين ولد {}؟ الإجابة: ",
    },
    "P20": {
        "zh-cn": "问题：{}在哪个城市去世？答案是：",
        "en": "Question: In which city did {} die? The answer is: ",
        "ar": "سؤال: أين توفي {}؟ الإجابة: ",
    },
    "P27": {
        "zh-cn": "问题：{}是哪个国家的公民？答案是：",
        "en": "Question: What country is {} a citizen of? The answer is: ",
        "ar": "سؤال: ما هي دولة مواطنة {}؟ الإجابة: ",
    },
    "P30": {
        "zh-cn": "问题：{}位于哪个大洲？答案是：",
        "en": "Question: Which continent is {} located in? The answer is:",
        "ar": "سؤال: ما هي القارة حيث تقع {}؟ الإجابة: ",
    },
    "P36": {
        "zh-cn": "问题：{}的首都是？答案是：",
        "en": "Question: What is the capital of {}? The answer is:",
        "ar": "سؤال: ما هي عاصمة {}؟ الإجابة: ",
    },
    "P37": {
        "zh-cn": "问题：{}的官方语言是什么？ 答案是：",
        "en": "Question: What is the official language of {}? The answer is: ",
        "ar": "سؤال: ما هي اللغة الرسمية ل {}؟ الإجابة: ",
    },
    "P47": {
        "zh-cn": "问题：{}与哪个国家接壤？答案是：",
        "en": "Question：What is the country that shares border with {}? The answer is:",
        "ar": "سؤال: ما هي الدولة التي تشترك في الحدود مع {}؟ الإجابة: ",
    },
    "P103": {
        "zh-cn": "问题：{}的母语是什么？答案是：",
        "en": "Question: What is the native language of {}? The answer is: ",
        "ar": "سؤال: ما هي اللغة الأصلية ل {}؟ الإجابة: ",
    },
    "P106": {
        "zh-cn": "问题：{}的职业是什么？答案是：",
        "en": "Question: What is the profession of {}? The answer is: ",
        "ar": "سؤال: ما هي مهنة {}؟ الإجابة: ",
    },
}


def load_jsonl_file(file_path):
    """Load a jsonl file."""
    with open(file_path, "r") as f:
        triples = [json.loads(l) for l in f]
    return triples


def save_jsonl_file(file_path, tuples):
    """Save tuples as a jsonl file."""
    with open(file_path, "w") as f:
        for t in tuples:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")


def get_bloom_output(predicate, entity, lang, model, tokenizer):
    """Answer a question using bloom model loaded on the GPU."""
    prompt = PROMPTS[predicate][lang].format(entity)

    inputs = tokenizer((prompt), return_tensors="pt").to("cuda")
    outputs_ids = model.generate(**inputs, max_new_tokens=40)

    outputs_strs = tokenizer.batch_decode(outputs_ids)

    return outputs_strs


def get_bloom_predictions(predicate, lang, model, tokenizer, triples):
    for triple in tqdm(triples):
        bloom_completion = get_bloom_output(
            predicate, triple["sub_label"], lang, model, tokenizer
        )[0]
        triple["prediction"] = bloom_completion
    return triples


if __name__ == "__main__":
    parser = ArgumentParser("Probe bloom and bloomz models.")
    parser.add_argument(
        "--dataset_dir", help="Directory of langs with predicate jsonl files."
    )
    parser.add_argument(
        "--predicates",
        nargs="*",
        default=None,
        help="List of predicates to use for probing.",
    )
    parser.add_argument(
        "-model_name", "-m", help="The name of the bloom(z) model to be probed."
    )
    parser.add_argument("--lang", help="Language of prompts to use")

    args = parser.parse_args()
    model_name = args.model_name
    lang = args.lang

    predicates = args.predicates
    if not predicates:
        predicates = list(PROMPTS.keys())

    OUTPUT_DIR = f"output_dlama/results/{re.sub('/', '_', model_name)}/{lang}"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto").to(
        "cuda"
    )

    for predicate in tqdm(predicates):
        triples = sum(
            [
                load_jsonl_file(file_path=file_path)
                for file_path in Path(args.dataset_dir, lang).glob(
                    f"{predicate}_*.jsonl"
                )
            ],
            [],
        )
        output_triples = get_bloom_predictions(
            predicate, lang, model, tokenizer, triples
        )

        PREDICATE_OUTPUT_DIR = str(Path(OUTPUT_DIR, predicate))
        os.makedirs(PREDICATE_OUTPUT_DIR, exist_ok=True)

        predicate_output_file_path = str(
            Path(PREDICATE_OUTPUT_DIR, f"{predicate}.jsonl")
        )
        save_jsonl_file(predicate_output_file_path, output_triples)
