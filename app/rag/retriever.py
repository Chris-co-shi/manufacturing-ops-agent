from app.rag.document import DocumentChunk
from app.rag.loader import MarkdownKnowledgeLoader
from app.rag.splitter import MarkdownSplitter


def _extract_keywords(query) -> list[str]:
    candidate_keywords = [
        "库存",
        "扣减",
        "同步",
        "SAP",
        "XMOM",
        "设备",
        "报警",
        "AGV",
        "投料",
        "失败",
        "异常",
        "补偿",
        "重试",
        "冻结",
        "现场",
    ]
    return [keyword for keyword in candidate_keywords if keyword in query]


def _score(query, content) -> int:
    keywords = _extract_keywords(query)
    score = 0

    for keyword in keywords:
        if keyword in content:
            score += 1
    return score


class KeywordRetriever:
    def __init__(self, knowledge_base: str = "data/knowledge"):
        self.loader = MarkdownKnowledgeLoader(knowledge_base)
        self.splitter = MarkdownSplitter()
        self.chunks = self._load_chunk()

    def _load_chunk(self) -> list[DocumentChunk]:
        documents = self.loader.load()
        return self.splitter.split(documents)

    def retrieve(self, query: str, top_k: int = 3) -> list[DocumentChunk]:
        scored_chunks: list[DocumentChunk] = []
        for chunk in self.chunks:
            score = _score(query=query, content=chunk.content)
            if score > 0:
                scored_chunks.append(
                    DocumentChunk(
                        source=chunk.source,
                        content=chunk.content,
                        score=score,
                    )
                )
        scored_chunks.sort(key=lambda item: item.score, reverse=True)

        selected_chunks: list[DocumentChunk] = []
        used_sources: set[str] = set()
        for chunk in scored_chunks:
            if chunk.source in used_sources:
                continue

            selected_chunks.append(chunk)
            used_sources.add(chunk.source)

            if len(selected_chunks) >= top_k:
                break
        return selected_chunks
