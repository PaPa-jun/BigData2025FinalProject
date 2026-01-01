from hdfs.client import InsecureClient


class HDFSClient(InsecureClient):
    def __init__(
        self,
        url,
        user=None,
        redirect: bool = False,
        original_host: str = None,
        replaced_host: str = None,
        **kwargs,
    ):
        super().__init__(url, user, **kwargs)
        self.redirect = redirect
        self.original_host = original_host
        self.replaced_host = replaced_host

    def _request(self, method, url, **kwargs):
        if self.redirect is True:
            return super()._request(
                method, url.replace(self.original_host, self.replaced_host), **kwargs
            )
        else:
            return super()._request(method, url, **kwargs)
