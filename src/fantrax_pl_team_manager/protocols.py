from typing import Any, Mapping, Protocol, TypeVar

T = TypeVar("T")

class HttpClient(Protocol):
    def fantrax_request(self, path: str) -> Mapping[str, Any]: ...

class Mapper(Protocol[T]):
    def from_json(self, payload: Mapping[str, Any]) -> T: ...
