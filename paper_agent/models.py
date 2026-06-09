"""论文研读 Agent 使用的数据模型。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
#把下面的paper类转换成数据类
class Paper:
    """一篇论文的统一元数据。
    说明这个类不光光是只服务于arXiv，也适用于其他来源的论文。
    """

    arxiv_id: str
    title: str
    authors: list[str]
    summary: str
    published: str
    updated: str
    pdf_url: str
    page_url: str
    source: str = "arxiv"
    '''
    论文来源，默认是arXiv，可以是其他来源，比如semantic scholar，openaliex等等。
    '''
    citation_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """把论文对象转换成可以写入 JSON 的字典。"""

        return asdict(self)
        '''
        调用dataclass里面的asdict方法，把这个类转换成一个字典，方便写入json文件。
        '''


@dataclass(slots=True)
class Evidence:
    """可以支撑综述结论的一条论文证据。"""

    paper_id: str
    paper_title: str
    source: str
    excerpt: str
    score: int
    location: str

    def to_dict(self) -> dict[str, Any]:
        """把证据对象转换成可以写入 JSON 的字典。"""

        return asdict(self)
