"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """
    Upgrade operations for this migration.
    
    HIPAA COMPLIANCE NOTICE:
    When creating migrations that handle PHI or PII:
    - Ensure data is encrypted at rest using pgcrypto
    - Apply row-level security policies
    - Use constraints to enforce data integrity
    - Add appropriate audit logging triggers
    """
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """
    Downgrade operations for this migration.
    
    CAUTION: Downgrading may result in data loss. Ensure backups exist.
    HIPAA COMPLIANCE: Data destruction operations must maintain audit trail.
    """
    ${downgrades if downgrades else "pass"}
