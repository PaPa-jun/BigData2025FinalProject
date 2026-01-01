import jieba, json, hashlib, math, os
from .hadoop import HDFSClient
from .db import HBaseDB
from .models import SearchResponse, SearchResponseItem, SearchRequest
from tqdm import tqdm
from typing import List, Set, Tuple, Any


def parse_query(query: str) -> list[str]:
    words = jieba.cut_for_search(query)
    keywords = [word.strip() for word in words if word.strip()]
    return keywords


def calculate_similarity(
    query_words: Set[str], target_words: List[str], weight: float = 1.0
) -> float:
    if not target_words or not query_words:
        return 0.0

    target_set = set(target_words)
    intersection = len(query_words.intersection(target_set))
    union = len(query_words.union(target_set))

    if union == 0:
        return 0.0

    jaccard_similarity = intersection / union
    return weight * jaccard_similarity


def calculate_tfidf_score(query_words: Set[str], item: SearchResponseItem) -> float:
    score = 0.0

    name_words = parse_query(item.name)
    name_score = calculate_similarity(query_words, name_words, weight=3.0)
    score += name_score

    if item.keywords:
        all_keywords = []
        for keyword in item.keywords:
            all_keywords.extend(parse_query(keyword))
        keyword_score = calculate_similarity(query_words, all_keywords, weight=2.0)
        score += keyword_score

    if item.high_freq_words:
        high_freq_score = calculate_similarity(
            query_words, item.high_freq_words, weight=1.0
        )
        score += high_freq_score

    path_words = parse_query(item.path)
    path_score = calculate_similarity(query_words, path_words, weight=0.5)
    score += path_score

    if item.size > 0:
        size_penalty = math.log10(item.size) / 10.0  # 对数惩罚，避免过大影响
        score = score * (1 - min(size_penalty, 0.3))  # 最多惩罚30%

    return score


def rerank(request: SearchRequest, origin: SearchResponse) -> SearchResponse:
    if not origin.items:
        return origin

    query_tokens = parse_query(request.query)
    query_words = set(word.lower() for word in query_tokens if word.strip())

    if not query_words:
        return origin

    scored_items: List[Tuple[float, SearchResponseItem]] = []

    for item in origin.items:
        relevance_score = calculate_tfidf_score(query_words, item)
        scored_items.append((relevance_score, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    sorted_items = [item for _, item in scored_items]

    return SearchResponse(num=len(sorted_items), items=sorted_items)


def execute_search(db: HBaseDB, table_name: str, keywords: list[str]) -> SearchResponse:
    items = []
    row_keys = set()
    file_ids = set()
    for keyword in keywords:
        results = db.include_matching(table_name, keyword)
        for result in results:
            if result["row_key"] in row_keys:
                continue
            for file in result["files"]:
                if file["id"] in file_ids:
                    continue
                items.append(
                    SearchResponseItem(
                        id=file["id"],
                        name=file["path"].split("/")[-1],
                        category=file["path"].split("/")[-2],
                        path=file["path"],
                        size=file["size"],
                        keywords=file["keywords"],
                        high_freq_words=file["high_freq_words"],
                    )
                )
                file_ids.add(file["id"])
            row_keys.add(result["row_key"])
    return SearchResponse(num=len(items), items=items)


def load_configs(config_path: str) -> dict:
    configs = {}
    with open(config_path, "r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            if not line:
                continue

            key, value = line.strip().split(" = ")
            converted_value = value

            if value.lower() == "true":
                converted_value = True
            elif value.lower() == "false":
                converted_value = False
            elif value.isdigit():
                converted_value = int(value)
            else:
                try:
                    if "." in value and all(
                        c.isdigit() or c == "." for c in value.replace("-", "", 1)
                    ):
                        converted_value = float(value)
                except ValueError:
                    pass

            if isinstance(converted_value, str):
                if (
                    converted_value.startswith('"') and converted_value.endswith('"')
                ) or (
                    converted_value.startswith("'") and converted_value.endswith("'")
                ):
                    converted_value = converted_value[1:-1]

            configs[key] = converted_value

    return configs


def build_index_table(
    db: HBaseDB,
    hdfs: HDFSClient,
    table_name: str,
    index_source: str,
    keywords_source: str,
    batch_size: int = 50,
) -> None:
    with open(index_source, "r") as file:
        indexes = json.load(file)
    with open(keywords_source, "r") as file:
        keywords = json.load(file)

    column_families = {
        "files": dict(),
        "metadata": dict(),
    }

    if table_name.encode() in db.connection.tables():
        db.delete_table(table_name)
    db.create_table(table_name, column_families)

    table = db.connection.table(table_name)
    batch = table.batch(batch_size=batch_size)

    path2id = {}
    for rowkey, file_paths in tqdm(indexes.items(), desc="Building HBase Index Table"):
        valid_files = []
        row_data = {}
        for file_path in file_paths:
            if hdfs.status(file_path, strict=False) is None:
                continue

            if file_path not in path2id:
                file_hash = hashlib.md5(file_path.encode("utf-8")).hexdigest()
                file_id = f"f_{file_hash[:16]}"
                path2id[file_path] = file_id
            else:
                file_id = path2id[file_path]

            file_keywords = keywords.get(file_path, {}).get("keywords", [])
            high_freq_words = keywords.get(file_path, {}).get("high_freq_words", [])
            file_size = hdfs.status(file_path)["length"]

            row_data[f"files:{file_id}_path"] = file_path.encode("utf-8")
            row_data[f"files:{file_id}_keywords"] = ",".join(file_keywords).encode(
                "utf-8"
            )
            row_data[f"files:{file_id}_high_freq_words"] = ",".join(
                high_freq_words
            ).encode("utf-8")
            row_data[f"files:{file_id}_size"] = str(file_size).encode("utf-8")

            valid_files.append(file_path)

        if valid_files:
            row_data["metadata:total_files"] = str(len(valid_files)).encode("utf-8")
            batch.put(rowkey.encode("utf-8"), row_data)
    batch.send()

    return db.describe_table(table_name, rows=10)


def get_folder_size(folder_path):
    """计算文件夹的总大小"""
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
    return total_size


def initialize(
    db: HBaseDB,
    hdfs: HDFSClient,
    upload_data: bool = False,
    hdfs_path: str = "/data",
    local_path: str = "/data",
    n_threads: int = 10,
    chunk_size: int = 64 * 1024 * 1024,
    overwrite: bool = False,
    build_table: bool = False,
    table_name: str = "file_index",
    index_source: str = "index.json",
    keywords_source: str = "keywords.json",
    batch_size: int = 50,
) -> None:
    if upload_data is True:
        if os.path.isdir(local_path):
            total_size = get_folder_size(local_path)
            desc = "Uploading folder"
        else:
            total_size = os.path.getsize(local_path)
            desc = "Uploading file"

        progress_bar = tqdm(total=total_size, unit="B", unit_scale=True, desc=desc)

        current_file_size = 0
        current_bytes_transferred = 0
        current_file_path = None

        def progress_callback(file_path, bytes_transferred):
            nonlocal current_file_size, current_bytes_transferred, current_file_path

            if bytes_transferred == -1:
                if current_file_size > 0:
                    remaining = current_file_size - current_bytes_transferred
                    if remaining > 0:
                        progress_bar.update(remaining)
                current_file_size = 0
                current_bytes_transferred = 0
                current_file_path = None
            else:
                if file_path != current_file_path:
                    if current_file_path is not None and current_file_size > 0:
                        remaining = current_file_size - current_bytes_transferred
                        if remaining > 0:
                            progress_bar.update(remaining)

                    current_file_path = file_path
                    if os.path.exists(file_path):
                        current_file_size = os.path.getsize(file_path)
                    else:
                        full_path = (
                            os.path.join(local_path, file_path)
                            if os.path.isdir(local_path)
                            else file_path
                        )
                        current_file_size = (
                            os.path.getsize(full_path)
                            if os.path.exists(full_path)
                            else 0
                        )

                    current_bytes_transferred = 0

                if bytes_transferred > current_bytes_transferred:
                    transferred_diff = bytes_transferred - current_bytes_transferred
                    progress_bar.update(transferred_diff)
                    current_bytes_transferred = bytes_transferred

        try:
            hdfs.upload(
                hdfs_path,
                local_path,
                n_threads=n_threads,
                chunk_size=chunk_size,
                progress=progress_callback,
                overwrite=overwrite,
            )
        finally:
            progress_bar.close()
            print("Upload completed!")

    if build_table is True:
        table_info = build_index_table(
            db, hdfs, table_name, index_source, keywords_source, batch_size
        )
        print(
            f"Table {table_name} building completed.",
            "\n",
            json.dumps(table_info, indent=2),
        )
