from typing import Any, Mapping, Protocol, TypeVar

T = TypeVar("T")

class HttpClient(Protocol):
    def the_odds_api_request(self, url: str, params={}, headers={}) -> Mapping[str, Any]: ...

class Mapper(Protocol[T]):
    def from_json(self, payload: Mapping[str, Any]) -> T: ...
