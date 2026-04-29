from dataclasses import dataclass


@dataclass
class Document:
    """
    文档类
    """
    source: str
    content: str


@dataclass
class DocumentChunk:
    """
    文档片段类
    """
    source: str
    content: str
    score: int = 0
