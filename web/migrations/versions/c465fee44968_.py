
"""empty message

Revision ID: c465fee44968
Revises: d0bc9f32b2b9
Create Date: 2021-06-04 14:42:12.843116

"""
from pgadmin.model import db, User
import uuid


# revision identifiers, used by Alembic.
revision = 'c465fee44968'
down_revision = 'd0bc9f32b2b9'
branch_labels = None
depends_on = None


def upgrade():
    db.engine.execute("ALTER TABLE user RENAME TO user_old")

    db.engine.execute("""
        CREATE TABLE user (
            id INTEGER NOT NULL,
            username VARCHAR(256) NOT NULL,
            email VARCHAR(256),
            password VARCHAR(256),
            active BOOLEAN NOT NULL,
            confirmed_at DATETIME,
            masterpass_check VARCHAR(256),
            auth_source VARCHAR(256) NOT NULL DEFAULT 'internal',
            fs_uniquifier NOT NULL UNIQUE,
            PRIMARY KEY (id),
            UNIQUE (username, auth_source, fs_uniquifier),
            CHECK (active IN (0, 1))
        );
        """)

    user_old = db.engine.execute(
        'select id, username, email, password, active, '
        'confirmed_at, masterpass_check, auth_source '
        'from user_old')

    db.engine.execute(User.__table__.insert(), [
        {
            **row,
            'fs_uniquifier': uuid.uuid4().hex
        } for row in user_old
    ])

    db.engine.execute("DROP TABLE user_old")


def downgrade():
    # pgAdmin only upgrades, downgrade not implemented.
    pass
