import happybase


class HBaseDB:
    def __init__(self, host: str = "localhost", port: int = 9090):
        self.connection = happybase.Connection(host=host, port=port)
        self.connection.open()

    def describe_db(self) -> dict:
        tables = self.connection.tables()
        description = {}
        for table in tables:
            column_families = self.connection.table(table).families()
            description[table.decode("utf-8")] = [
                cf.decode("utf-8") for cf in column_families.keys()
            ]
        return description

    def describe_table(self, table_name: str, rows: int = 5) -> list[dict]:
        table = self.connection.table(table_name)
        data = []
        for key, row in table.scan(limit=rows):
            decoded_row = {k.decode("utf-8"): v.decode("utf-8") for k, v in row.items()}
            data.append({"row_key": key.decode("utf-8"), **decoded_row})
        return data

    def create_table(self, table_name: str, column_families: dict) -> None:
        self.connection.create_table(table_name, column_families)

    def delete_table(self, table_name: str) -> None:
        self.connection.delete_table(table_name, disable=True)

    def include_matching(self, table_name: str, query: str) -> list[dict]:
        results = []
        exists = set()
        filter_str = f"RowFilter(=, 'substring:{query}')"
        for key, data in self.connection.table(table_name).scan(filter=filter_str):
            row_key = key.decode()
            if row_key not in exists:
                results.append(self._formate_data(key, data))
                exists.add(row_key)
        return results

    def _get_id(self, key: str) -> str:
        return "_".join(key.split(":")[1].split("_")[:2])

    def _formate_data(self, key: bytes, data: dict) -> dict:
        format_data = {
            "row_key": key.decode(),
            "num": int(data.get(b"metadata:total_files", b"0").decode()),
            "files": [],
        }

        file_ids = set()
        for key in data.keys():
            if key.decode("utf-8").startswith("files"):
                file_ids.add(self._get_id(key.decode("utf-8")))

        for file_id in file_ids:
            path_key = f"files:{file_id}_path".encode("utf-8")
            size_key = f"files:{file_id}_size".encode("utf-8")
            keywords_key = f"files:{file_id}_keywords".encode("utf-8")
            high_freq_words_key = f"files:{file_id}_high_freq_words".encode("utf-8")

            format_data["files"].append(
                {
                    "id": file_id,
                    "path": data.get(path_key, b"").decode("utf-8"),
                    "size": int(data.get(size_key, b"0").decode("utf-8")),
                    "keywords": (
                        data.get(keywords_key, b"").decode("utf-8").strip().split(",")
                        if data.get(keywords_key)
                        else []
                    ),
                    "high_freq_words": (
                        data.get(high_freq_words_key, b"")
                        .decode("utf-8")
                        .strip()
                        .split(",")
                        if data.get(high_freq_words_key)
                        else []
                    ),
                }
            )

        return format_data
