"""
Direct DB-layer persistence tests (section 26 "Persistence" group):
sessions, messages (with JSONB sources), artifacts, and cascade deletes.
"""
from sqlalchemy import select

from app.models.db_models import Artifact, Message, SessionModel


async def test_message_persists_with_jsonb_sources(db_session):
    session = SessionModel(title="Persistence test")
    db_session.add(session)
    await db_session.commit()

    sources = [{"episode": "Ep 1", "guest": "Guest 1", "text": "quote", "score": 0.9}]
    message = Message(session_id=session.id, role="assistant", content="answer", sources=sources)
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)

    assert message.sources == sources


async def test_artifact_persists_and_links_to_message(db_session):
    session = SessionModel(title="Artifact persistence test")
    db_session.add(session)
    await db_session.commit()

    message = Message(session_id=session.id, role="assistant", content="here's a doc")
    db_session.add(message)
    await db_session.commit()

    artifact = Artifact(
        message_id=message.id, artifact_type="markdown", title="Notes", content="# Notes"
    )
    db_session.add(artifact)
    await db_session.commit()
    await db_session.refresh(artifact)

    assert artifact.artifact_type == "markdown"
    assert artifact.message_id == message.id


async def test_deleting_session_cascades_to_messages_and_artifacts(db_session):
    session = SessionModel(title="Cascade test")
    db_session.add(session)
    await db_session.commit()

    message = Message(session_id=session.id, role="user", content="hello")
    db_session.add(message)
    await db_session.commit()

    artifact = Artifact(message_id=message.id, artifact_type="html", title="Page", content="<p>hi</p>")
    db_session.add(artifact)
    await db_session.commit()

    await db_session.delete(session)
    await db_session.commit()

    remaining_messages = (await db_session.execute(select(Message))).scalars().all()
    remaining_artifacts = (await db_session.execute(select(Artifact))).scalars().all()
    assert remaining_messages == []
    assert remaining_artifacts == []
