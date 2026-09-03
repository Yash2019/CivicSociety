from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.Models.problems_db import Problems

vectorizer = TfidfVectorizer(
    analyzer="char_wb",
    ngram_range=(3,5),
    max_features=10_000,
)

DUPLICATE_TRESHOLD = 0.6

async def find_duplicate(
        title: str,
        description: str,
        category: str,
        db: AsyncSession,
        treshold: float = DUPLICATE_TRESHOLD,
)-> dict | None:

    stmt = (
        select(Problems.id, Problems.description)
        .where(Problems.category == category)
        .order_by(Problems.created_at.desc())
        .limit(500)
        )

    result = await db.execute(stmt)
    existing = result.all()

    if not existing:
        return None

    new_text = f"{title} {description}"
    corpus = [f"{row.description}" for row in existing]
    corpus.append(new_text)

    tfid_matrix = vectorizer.fit_transform(corpus)

    similarities = cosine_similarity(tfid_matrix[-1:], tfid_matrix[:-1])[0]

    best_idx = similarities.argmax()
    best_score = similarities[best_idx]

    if best_score >= treshold:

        return {
            "is_duplicate": True,
            "duplicate_of_id": existing[best_idx].id,
            "similarity_score": round(float(best_score), 3), 
        }

    return None

