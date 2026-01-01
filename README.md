# Hadoop-HBase File Storage and Search Engine

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Hadoop Version](https://img.shields.io/badge/hadoop-3.4.2-green)](https://hadoop.apache.org/)
[![HBase Version](https://img.shields.io/badge/hbase-2.5.13-green)](https://hbase.apache.org/)

A pseudo-distributed file storage system and search engine built on top of Hadoop HDFS and HBase, featuring file download capabilities and fuzzy search functionality.

## Features

- **Pseudo-distributed File Storage**: Store files across HDFS with distributed capabilities
- **Fuzzy Search Engine**: Advanced search functionality with fuzzy matching capabilities
- **File Download Support**: Retrieve stored files through the search interface
- **Docker Integration**: Pre-configured Docker environment with Hadoop and HBase
- **FastAPI Backend**: Modern REST API for search and file operations
- **Web Interface**: User-friendly web interface for file management and search

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Application Layer                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │   Web UI    │    │   FastAPI   │    │   Search Engine │  │
│  └─────────────┘    └─────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │           │           │
┌─────────────────────────────────────────────────────────────┐
│                       Storage Layer                         │
│  ┌─────────────┐                          ┌─────────────┐   │
│  │   HDFS      │◄────────────────────────►│   HBase     │   │
│  │ (File Data) │                          │ (Index Data)│   │
│  └─────────────┘                          └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

### System Requirements
- Python 3.12 or higher
- Docker and Docker Compose (for the Hadoop-HBase cluster)
- At least 4GB RAM for smooth operation of the Docker containers
- Or you can use your local Hadoop and Hbase.

### Python Dependencies
All dependencies are managed through `pyproject.toml` and can be installed using `uv` or standard `pip`.

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/PaPa-jun/BigData2025FinalProject.git
cd BigData2025FinalProject
```

### 2. Install Python Dependencies
Using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -r requirements.txt
```

### 3. Setup Hadoop-HBase Cluster (Optional but Recommended)

Navigate to the cluster directory and start the Docker containers:
```bash
cd cluster
docker-compose up -d
```

This will start a single-node Hadoop-HBase cluster with all necessary services pre-configured.

## Configuration

Before running the application, you need to configure the settings in `configs.cfg` file. Below is a detailed explanation of each configuration section:

### Default Configuration File
```ini
# HDFS Configuration
HDFS_URL = "http://localhost:9870"      # HDFS web interface URL
HDFS_USER = root                        # HDFS user name

# HBase Configuration
HBASE_HOST = "localhost"                # HBase server host
HBASE_PORT = 9090                       # HBase Thrift server port
INDEX_TABLE_NAME = "file_index"         # HBase table name for storing file index

# App Configuration
INITIALIZE = False                      # Whether to initialize the system on startup (usually set to True for the first run)
REDIRECT = False                        # Whether to redirect HDFS URLs

# Redirect Configuration (useful only if REDIRECT is True)
ORIGINAL_HOST = "hadoop-master"         # Original hostname in HDFS URLs
REPLACED_HOST = "localhost"             # Hostname to replace with for local access

# Initialize Configuration (useful only if INITIALIZE is True)
UPLOAD_DATA = False                     # Whether to upload data to HDFS
BUILD_INDEX_TABLE = False               # Whether to build the HBase index table

# File uploading Configuration (useful only if UPLOAD_DATA is True)
HDFS_PATH = "/"                         # HDFS path to upload files to
LOCAL_PATH = "source/data"              # Local directory or file to upload
N_THREADS = 10                          # Number of threads for parallel upload
CHUNK_SIZE = 683147264                  # Chunk size for upload (64 MB)
OVERWRITE = False                       # Whether to overwrite existing files

# Table building Configuration (useful only if BUILD_INDEX_TABLE is True)
INDEX_SOURCE_PATH = "source/keyword_index.json"         # Path to keyword index file
KEYWORDS_SOURCE_PATH = "source/file_detail.json"        # Path to file detail file
BATCH_SIZE = 50                         # Batch size for HBase operations

# FastAPI Configuration
API_HOST = "localhost"                  # FastAPI server host
API_PORT = 8000                         # FastAPI server port
RELOAD = False                          # Whether to enable auto-reload in development

# Web Server Configuration
WEB_DIR = "web"                         # Directory containing web interface files
```

## Running the Application

### 1. Configure the Application
Edit the `configs.cfg` file according to your environment and requirements.

### 2. Start the Application
```bash
python main.py
```

The application will:
- Initialize the system if `INITIALIZE = True`
- Start the FastAPI server
- Serve the web interface from the specified `WEB_DIR`

### 3. Access the Application
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **HDFS Web UI**: http://localhost:9870
- **HBase Web UI**: http://localhost:16010

## Docker Environment Details

### Dockerfile Explanation
The Dockerfile creates a single-node Hadoop-HBase cluster with the following key components:

- **Base Image**: Ubuntu latest with Asia/Shanghai timezone
- **Java Installation**: OpenJDK 8 (required for Hadoop and HBase)
- **SSH Configuration**: Passwordless SSH setup for Hadoop services
- **Hadoop Installation**: Version 3.4.2 with custom configuration files
- **HBase Installation**: Version 2.5.13 with custom configuration files
- **Exposed Ports**: All necessary ports for Hadoop and HBase services

Key environment variables:
- `JAVA_HOME`: Path to Java installation
- `HADOOP_HOME`: Hadoop installation directory
- `HBASE_HOME`: HBase installation directory

### Docker Compose Configuration
The `docker-compose.yaml` file defines a single service that:
- Builds from the Dockerfile in the current directory
- Sets the container name and hostname to `hadoop-master`
- Maps all necessary ports to the host machine
- Runs with privileged mode for Hadoop operations
- Executes startup commands to:
  1. Restart SSH service
  2. Format the HDFS namenode
  3. Start HDFS services
  4. Start YARN services
  5. Start HBase services
  6. Start HBase thrift services
  7. Keep the container running with `tail -f /dev/null`

### Verify Docker Container Health
After starting your Docker container, you can verify the cluster status by executing the following commands:
```sh
# Access the container shell
docker exec -it hadoop-hbase-single-node /bin/bash

# Check running Java processes
jps
```
If all services are running correctly, you should see output similar to:
```
195 NameNode            # Name Node server
333 DataNode            # Data Node server
513 SecondaryNameNode   # Srcondary NameNode server
712 ResourceManager     # Resource Manager server
1022 NodeManager        # Node Manager server
1526 HQuorumPeer        # HBase ZooKeeper service
1642 HMaster            # HBase master server
1821 HRegionServer      # HBase region server
2073 ThriftServer       # HBase Thrift API server
2513 Jps                # This command
```

**Key Services to Verify:**
- **Hadoop Core Services**: NameNode, DataNode, SecondaryNameNode
- **YARN Services**: ResourceManager, NodeManager  
- **HBase Services**: HMaster, HRegionServer, HQuorumPeer, ThriftServer

> **Note**: The process IDs (first column) may vary in your environment. Focus on ensuring all critical services are present in the output. If any essential service is missing, check the container logs using `docker logs hadoop-hbase-single-node` for troubleshooting.

## Development

### Directory Structure
```
├── cluster/                # Docker configuration for Hadoop-HBase cluster
│   ├── Dockerfile          # Docker build file
│   ├── docker-compose.yaml # Docker Compose configuration
│   ├── configs/            # Hadoop and HBase configuration files
│   └── scripts/            # Startup scripts and environment files
├── configs.cfg             # Main application configuration file
├── main.py                 # Application entry point
├── source/                 # Source data files
│   ├── data/               # Files to be uploaded to HDFS
│   ├── keyword_index.json  # Keyword index for search
│   └── file_detail.json    # File-keyword mappings
├── web/                    # Web interface files
├── pyproject.toml          # Python project configuration
└── README.md               # This documentation file
```

### Common Tasks

#### Getting file details

You have to get the detailed information about your files and construct the `file_detail.json` as follows:
```
{
    "/dfs/path/to/file1.docx": {
        "keywords": [
            "keywords1",
            "keywords2",
            ...
        ],
        "high_freq_words": [
            "high_freq_words1",
            "high_freq_words2",
            ...
        ]
    },
    ...
}
```

#### Creating json files
You have to create your own searching index in `keyword_index.json` as follows:
```
{
    "key1": [
        "/dfs/path/to/file1.docx",
        "/dfs/path/to/file2.pdf",
        ...
    ],
    ...
}
```

#### Uploading Data to HDFS
Set `UPLOAD_DATA = True` in `configs.cfg` to upload files from `LOCAL_PATH` to HDFS on startup.

#### Building Search Index Table
Set `BUILD_INDEX_TABLE = True` in `configs.cfg` to build the HBase index table from the source JSON files.

## API Endpoints

The FastAPI backend provides the following endpoints:

- `POST /api/search/{query}`: Search for files using fuzzy matching
- `POST /api/download/{path}`: Get download url by file's path on hdfs

## Troubleshooting

### Common Issues

1. **Connection to HDFS fails**:
   - Ensure the Docker containers are running: `docker ps`
   - Check HDFS web UI at http://localhost:9870
   - Verify `HDFS_URL` in configuration matches the actual URL

2. **HBase connection issues**:
   - Check HBase is running in Docker: `docker logs hadoop-hbase-single-node`
   - Verify `HBASE_HOST` and `HBASE_PORT` are correct
   - Ensure Thrift server is running (port 9090)

3. **Docker container connection issues**:
    - Check `REDIRECT` config in the `configs.cfg`
    - Set `REDIRECT` to `True` when you are using the docker cluster


### Logs
Application logs are printed to stdout. For Docker container logs:
```bash
docker logs hadoop-hbase-single-node
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests for:
- Bug fixes
- Performance improvements
- Additional features
- Documentation enhancements

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Apache Hadoop Community](https://hadoop.apache.org)
- [Apache HBase Community](https://hbase.apache.org)
- [FastAPI Team](https://fastapi.tiangolo.com)
- [Docker Community](https://www.docker.com)

---

**Note**: This `README` assumes you have basic knowledge of Hadoop, HBase, and Docker. For detailed documentation on these technologies, please refer to their official documentation.
