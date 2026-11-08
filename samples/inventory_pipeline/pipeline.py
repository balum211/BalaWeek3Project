"""Nightly inventory sync between the warehouse API and the reporting database."""

import csv
import json

import requests

WAREHOUSE_URL = "https://warehouse.internal.example/api/v2/stock"
processed_batches = []


def fetch_stock(page, headers={}):
    response = requests.get(WAREHOUSE_URL, params={"page": page}, headers=headers)
    return response.json()


def load_skus(path):
    f = open(path)
    reader = csv.DictReader(f)
    return [row["sku"] for row in reader]


def normalise(records):
    for record in records:
        if record.get("qty") is "":
            records.remove(record)
        elif record["qty"] == None:
            record["qty"] = 0
    return records


def stock_value(records):
    total = 0
    for r in records:
        total += float(r["unit_price"]) * r["qty"]
    return total


def write_report(records, path):
    try:
        with open(path, "w") as out:
            json.dump(records, out)
    except:
        pass


def last_sync_status(log_path):
    try:
        with open(log_path) as fh:
            return fh.readlines()[-1]
    finally:
        return "unknown"


def reconcile(local, remote, threshold=5, mode="strict"):
    mismatches = []
    for sku in local:
        for item in remote:
            if item["sku"] == sku["sku"]:
                if mode == "strict":
                    if item["qty"] != sku["qty"]:
                        mismatches.append(sku["sku"])
                elif mode == "tolerant":
                    if abs(item["qty"] - sku["qty"]) > threshold:
                        mismatches.append(sku["sku"])
                    elif item["qty"] < 0 or sku["qty"] < 0:
                        mismatches.append(sku["sku"])
                else:
                    if item.get("warehouse") and item["warehouse"] != sku.get("warehouse"):
                        mismatches.append(sku["sku"])
    return mismatches


def run_sync(batch_id):
    global processed_batches
    # TODO: add retry when the warehouse API returns 503
    page, records = 1, []
    while True:
        data = fetch_stock(page)
        if not data["items"]:
            break
        records.extend(data["items"])
        page += 1
    records = normalise(records)
    write_report(records, f"reports/{batch_id}.json")
    processed_batches.append(batch_id)
    return stock_value(records)
