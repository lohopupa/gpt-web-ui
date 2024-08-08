
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    model: str
    query: str
    categories: list[str]
    n_ctx: int | None
    delta: int | None
    use_search: bool | None