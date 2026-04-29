from app.rag.document import Document, DocumentChunk


class MarkdownSplitter:
    """
    Markdown 文档分割器
    这里是固定的 以段落分割
    """

    def split(self, documents: list[Document]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        # 遍历文档 固定以段落进行分割
        for document in documents:
            sections = document.content.split("\n##")
            for chunk in sections:
                content = chunk.strip()
                if not content:
                    continue
                chunks.append(DocumentChunk(
                    source=document.source,
                    content=chunk
                ))
        return chunks
