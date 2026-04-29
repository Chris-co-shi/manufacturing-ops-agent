from pathlib import Path

from app.rag.document import Document


class MarkdownKnowledgeLoader:
    """
    Markdown 知识库加载器
    """

    def __init__(self, knowledge_dir: str):
        self.knowledge_dir = Path(knowledge_dir)

    """
        加载内容
    """

    def load(self) -> list[Document]:
        documents: list[Document] = []
        if not self.knowledge_dir.exists():
            return documents
        for file in self.knowledge_dir.glob("*.md"):
            content = file.read_text(encoding="utf-8")
            documents.append(
                Document(
                    source=file.name,
                    content=content
                )
            )
        return documents
