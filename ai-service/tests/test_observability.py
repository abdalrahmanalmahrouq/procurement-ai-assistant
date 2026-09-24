import unittest
from uuid import UUID, uuid4

from fastapi import Request

from app.observability import get_request_id, normalize_request_id


class ObservabilityTests(unittest.TestCase):
    def request(self, request_id: str | None = None) -> Request:
        headers = []
        if request_id is not None:
            headers.append((b"x-request-id", request_id.encode()))
        return Request({"type": "http", "headers": headers})

    def test_request_id_is_generated_when_header_is_missing(self):
        UUID(get_request_id(self.request()))

    def test_valid_upstream_request_id_is_preserved(self):
        request_id = str(uuid4())

        self.assertEqual(get_request_id(self.request(request_id)), request_id)

    def test_invalid_upstream_request_id_is_replaced(self):
        request_id = normalize_request_id("not-a-uuid")

        self.assertNotEqual(request_id, "not-a-uuid")
        UUID(request_id)


if __name__ == "__main__":
    unittest.main()
