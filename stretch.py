"""
Stretch run: retrain the 10-epoch model ("after") and the 10-epoch + label
smoothing model ("after2") on seeds 42 / 7 / 2024, saving per-post predictions.

Settings and split match takemeter.ipynb (cells 8, 14, 16, 18). The notebook
never saved per-post output, so this is the only way to get it.

Run:  .venv\\Scripts\\python stretch.py
"""
import json

import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification, AutoTokenizer,
    Trainer, TrainingArguments, set_seed,
)

LABELS = ["business", "incident", "legal", "claim", "analysis"]
BASE_MODEL = "distilbert-base-uncased"
EPOCHS, LEARNING_RATE, BATCH_SIZE, MAX_LENGTH = 10, 2e-5, 16, 128
SEEDS = [42, 7, 2024]
CONFIGS = {"after": 0.0, "after2": 0.1}  # name -> label_smoothing_factor


def split_dataset(df, seed, test_size=0.15, val_size=0.15):
    rest, test = train_test_split(
        df, test_size=test_size, random_state=seed, stratify=df["label"]
    )
    train, val = train_test_split(
        rest, test_size=val_size / (1 - test_size), random_state=seed,
        stratify=rest["label"],
    )
    return tuple(x.reset_index(drop=True) for x in (train, val, test))


def to_ids(df):
    out = df.copy()
    out["labels"] = out["label"].astype(str).str.strip().map({l: i for i, l in enumerate(LABELS)})
    return out[["text", "labels"]]


def run(df, seed, smoothing):
    train_df, val_df, test_df = split_dataset(df, seed)
    set_seed(seed)
    tok = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL, num_labels=len(LABELS),
        id2label=dict(enumerate(LABELS)), label2id={l: i for i, l in enumerate(LABELS)},
    )

    def ds(frame):
        return Dataset.from_pandas(to_ids(frame)).map(
            lambda b: tok(b["text"], truncation=True, padding="max_length", max_length=MAX_LENGTH),
            batched=True,
        )

    args = TrainingArguments(
        output_dir="./takemeter_out", num_train_epochs=EPOCHS,
        learning_rate=LEARNING_RATE, per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE, eval_strategy="epoch",
        save_strategy="no", logging_steps=10, seed=seed, report_to="none",
        disable_tqdm=True, label_smoothing_factor=smoothing,
    )
    trainer = Trainer(model=model, args=args, train_dataset=ds(train_df), eval_dataset=ds(val_df))
    trainer.train()

    out = trainer.predict(ds(test_df))
    logits = out.predictions
    gold = np.array(out.label_ids)
    pred = logits.argmax(-1)
    exp = np.exp(logits - logits.max(-1, keepdims=True))
    conf = (exp / exp.sum(-1, keepdims=True)).max(-1)

    rows = [
        {"seed": seed, "text": t, "gold": LABELS[g], "pred": LABELS[p], "confidence": float(c)}
        for t, g, p, c in zip(test_df["text"], gold, pred, conf)
    ]
    right = gold == pred
    ranked = np.argsort(conf)
    third = len(conf) // 3
    _, rec, f1, sup = precision_recall_fscore_support(
        gold, pred, labels=range(len(LABELS)), zero_division=0
    )[:4]
    summary = {
        "seed": seed,
        "n_test": int(len(gold)),
        "accuracy": float(accuracy_score(gold, pred)),
        "f1_macro": float(f1_score(gold, pred, average="macro", zero_division=0)),
        "per_label": {
            l: {"recall": float(rec[i]), "f1": float(f1[i]), "support": int(sup[i])}
            for i, l in enumerate(LABELS)
        },
        "confidence": {
            "mean_when_right": float(conf[right].mean()),
            "mean_when_wrong": float(conf[~right].mean()),
            "accuracy_most_confident_third": float(right[ranked[-third:]].mean()),
            "accuracy_least_confident_third": float(right[ranked[:third]].mean()),
            "n_per_third": int(third),
        },
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "torch_version": torch.__version__,
        "label_smoothing_factor": smoothing,
    }
    return rows, summary


if __name__ == "__main__":
    df = pd.read_csv("labels.csv")
    for name, smoothing in CONFIGS.items():
        all_rows, all_summaries = [], []
        for seed in SEEDS:
            rows, summary = run(df, seed, smoothing)
            print(f"{name} seed {seed}: accuracy {summary['accuracy']:.3f}  macro F1 {summary['f1_macro']:.3f}", flush=True)
            all_rows += rows
            all_summaries.append(summary)
        with open(f"stretch_predictions_{name}.json", "w", encoding="utf-8") as f:
            json.dump(all_rows, f, indent=2)
        with open(f"stretch_results_{name}.json", "w", encoding="utf-8") as f:
            json.dump(all_summaries, f, indent=2)
