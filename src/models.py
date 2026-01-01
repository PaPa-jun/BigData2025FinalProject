from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str


class SearchResponseItem(BaseModel):
    id: str
    name: str
    category: str
    path: str
    size: int
    keywords: list[str]
    high_freq_words: list[str]


class SearchResponse(BaseModel):
    num: int
    items: list[SearchResponseItem]


class DownloadRequest(BaseModel):
    path: str


class DownloadResponse(BaseModel):
    download_url: str
