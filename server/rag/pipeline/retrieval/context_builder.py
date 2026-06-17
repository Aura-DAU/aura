class ContextBuilder:

    def build(self, chunks):

        documents = []

        sources = []
        seen_urls = set()

        for idx, chunk in enumerate(
            chunks,
            start=1
        ):

            metadata = chunk["metadata"]

            document = f"""
<doc
id="{idx}"
score="{chunk.get('reranked_score', chunk.get('score', 0))}"
title="{metadata.get('title', '')}"
cluster="{metadata.get('cluster', '')}"
category="{metadata.get('category', '')}"
faculty_name="{metadata.get('faculty_name', '')}"
event_name="{metadata.get('event_name', '')}"
url="{metadata.get('url', '')}"
h1="{metadata.get('h1', '')}"
h2="{metadata.get('h2', '')}"
h3="{metadata.get('h3', '')}"
scraped_date="{metadata.get('scraped_date', '')}"
>
{metadata.get('text', '')}

</doc>
"""
            documents.append(document)

            url = metadata.get("url")

            if url and url not in seen_urls:

                sources.append({
                    "title": metadata.get("title"),
                    "url": url,
                    "cluster": metadata.get("cluster")
                })

                seen_urls.add(url)

        context = (
            "<context>\n"
            + "\n".join(documents)
            + "\n</context>"
        )

        return {
            "context": context,
            "sources": sources
        }