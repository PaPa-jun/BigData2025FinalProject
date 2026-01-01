import uvicorn
from src import create_app, load_configs, initialize, HBaseDB, HDFSClient

configs = load_configs("configs.cfg")
db_cli = HBaseDB(host=configs["HBASE_HOST"], port=configs["HBASE_PORT"])
hdfs = HDFSClient(
    url=configs["HDFS_URL"],
    user=configs["HDFS_USER"],
    redirect=configs["REDIRECT"],
    original_host=configs["ORIGINAL_HOST"],
    replaced_host=configs["REPLACED_HOST"],
)
app = create_app(db_cli, configs)

if __name__ == "__main__":
    if configs["INITIALIZE"] is True:
        initialize(
            db_cli,
            hdfs,
            configs["UPLOAD_DATA"],
            configs["HDFS_PATH"],
            configs["LOCAL_PATH"],
            configs["N_THREADS"],
            configs["CHUNK_SIZE"],
            configs["OVERWRITE"],
            configs["BUILD_INDEX_TABLE"],
            configs["INDEX_TABLE_NAME"],
            configs["INDEX_SOURCE_PATH"],
            configs["KEYWORDS_COURCE_PATH"],
            configs["BATCH_SIZE"],
        )

    uvicorn.run(
        "main:app",
        host=configs["API_HOST"],
        port=configs["API_PORT"],
        reload=configs["RELOAD"],
    )
