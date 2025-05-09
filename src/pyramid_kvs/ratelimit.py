import json
import logging

log = logging.getLogger(__name__)


class RateLimitError(Exception):
    pass


class Ratelimit:
    """
    Rate limit your call http request.
    You must use the pyramid_kvs session implementation to get it working.
    """

    window = 1  # in seconds
    limit = 15  # max call in the during window
    key_suffix = "::ratelimit"

    def __init__(self, request):
        key = (request.session.get_session_key() + self.key_suffix).encode()
        client = request.session.client
        request.add_response_callback(self._add_headers)
        if client.get(key) is None:
            self.count = 1
            client.raw_set(key, str(self.count), self.window)
        else:
            self.count = client.incr(key)

        if self.count > self.limit:
            raise RateLimitError()

    @classmethod
    def configure(cls, settings):
        if isinstance(settings["kvs.ratelimit"], dict):
            config = settings["kvs.ratelimit"].copy()
        else:
            config = json.loads(settings["kvs.ratelimit"])

        cls.key_suffix = config.get("key_suffix", cls.key_suffix)
        cls.window = config.get("window", cls.window)
        cls.limit = config.get("limit", cls.limit)

    def _add_headers(self, request, response):
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(self.limit - self.count)
