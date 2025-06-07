"""
Immutable Audit Chain Module for HIPAA Compliance

This module provides blockchain-inspired immutable audit logging
for maintaining compliant and tamper-resistant access logs.
"""

import hashlib
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from pydantic import BaseModel, Field

from ..utils.structured_logging import get_logger
from .phi_logger import PHIAccessRecord

logger = get_logger(__name__)


class ChainedAuditRecord(BaseModel):
    """
    An immutable audit record with cryptographic chaining.
    
    This class extends PHIAccessRecord with cryptographic protection
    against tampering by chaining records together in a blockchain-inspired pattern.
    """
    record: PHIAccessRecord
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    hash: str = Field(..., description="Cryptographic hash of this record")
    previous_hash: str = Field(..., description="Hash of the previous record in chain")
    nonce: int = Field(..., description="Number used once for hash calculation")
    signature: Optional[str] = Field(None, description="Digital signature if available")


class AuditChain:
    """
    Blockchain-inspired immutable audit chain for HIPAA-compliant logging.
    
    Features:
    - Tamper-resistant audit logs using cryptographic hash chaining
    - Validation of chain integrity 
    - Support for digital signatures
    - Merkle tree support for efficient verification
    """
    
    def __init__(self, audit_secret_key: str):
        """
        Initialize the audit chain.
        
        Args:
            audit_secret_key: Secret key for hash calculation
        """
        self.secret_key = audit_secret_key
        self.previous_hash = self._calculate_genesis_block_hash()
        self.chain: List[ChainedAuditRecord] = []
        self._lock = asyncio.Lock()
        
        logger.info("AuditChain initialized with genesis block")
    
    def _calculate_genesis_block_hash(self) -> str:
        """Calculate the hash for the genesis block."""
        genesis = f"HIPAA-AUDIT-GENESIS-{datetime.utcnow().isoformat()}-{self.secret_key}"
        return hashlib.sha3_256(genesis.encode()).hexdigest()
    
    def _calculate_record_hash(self, record: PHIAccessRecord, previous_hash: str, nonce: int) -> str:
        """
        Calculate cryptographic hash of an audit record.
        
        Args:
            record: The record to hash
            previous_hash: Hash of the previous record
            nonce: Number used once
            
        Returns:
            SHA3-256 hash of the record
        """
        # Create a serialized representation of the record
        record_data = record.model_dump_json()
        
        # Combine record data with previous hash and nonce
        combined = f"{record_data}{previous_hash}{nonce}{self.secret_key}"
        
        # Calculate hash
        return hashlib.sha3_256(combined.encode()).hexdigest()
    
    async def add_record(self, record: PHIAccessRecord) -> ChainedAuditRecord:
        """
        Add a record to the immutable chain.
        
        Args:
            record: The PHI access record to add
            
        Returns:
            Chained audit record with cryptographic protection
        """
        async with self._lock:
            # Find a valid nonce (simple proof-of-work)
            nonce = 0
            valid_hash = ""
            
            while not valid_hash.startswith("0"):
                nonce += 1
                valid_hash = self._calculate_record_hash(record, self.previous_hash, nonce)
            
            # Create chained record
            chained_record = ChainedAuditRecord(
                record=record,
                hash=valid_hash,
                previous_hash=self.previous_hash,
                nonce=nonce
            )
            
            # Update chain
            self.chain.append(chained_record)
            self.previous_hash = valid_hash
            
            # Log addition
            logger.info(
                f"Added record to audit chain: {record.record_id}",
                extra={"record_hash": valid_hash}
            )
            
            return chained_record
    
    async def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """
        Verify the integrity of the entire audit chain.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.chain:
            return True, None  # Empty chain is valid
            
        current_hash = self.chain[0].previous_hash
        
        for i, record in enumerate(self.chain):
            # Verify this record references the previous hash
            if record.previous_hash != current_hash:
                return False, f"Chain broken at record {i}: Invalid previous hash"
            
            # Verify the hash is valid for this record
            calculated_hash = self._calculate_record_hash(
                record.record, record.previous_hash, record.nonce
            )
            
            if calculated_hash != record.hash:
                return False, f"Chain broken at record {i}: Invalid hash"
            
            # Update current hash
            current_hash = record.hash
        
        return True, None
        
    async def search_records(self, 
                           user_id: Optional[str] = None, 
                           action: Optional[str] = None,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None) -> List[ChainedAuditRecord]:
        """
        Search audit records by criteria.
        
        Args:
            user_id: Optional user ID to filter by
            action: Optional action to filter by
            start_time: Optional start of time range
            end_time: Optional end of time range
            
        Returns:
            List of matching records
        """
        results = []
        
        for record in self.chain:
            # Filter by user_id if specified
            if user_id and record.record.user_id != user_id:
                continue
                
            # Filter by action if specified
            if action and record.record.action != action:
                continue
            
            # Filter by time range
            if start_time and record.timestamp < start_time:
                continue
            if end_time and record.timestamp > end_time:
                continue
                
            results.append(record)
        
        return results
    
    def get_merkle_root(self, records: List[ChainedAuditRecord]) -> str:
        """
        Calculate a Merkle root hash for a set of records.
        
        This enables efficient verification of a subset of the audit chain.
        
        Args:
            records: Records to include in the Merkle tree
            
        Returns:
            Merkle root hash
        """
        if not records:
            return ""
            
        # Get the hashes of all records
        hashes = [record.hash for record in records]
        
        # Build Merkle tree
        while len(hashes) > 1:
            # If odd number of hashes, duplicate the last one
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])
                
            # Combine adjacent hashes
            next_level = []
            for i in range(0, len(hashes), 2):
                combined = f"{hashes[i]}{hashes[i+1]}"
                next_hash = hashlib.sha3_256(combined.encode()).hexdigest()
                next_level.append(next_hash)
                
            hashes = next_level
        
        # Return root hash
        return hashes[0]


# Global instance
_audit_chain = None

async def get_audit_chain(secret_key: Optional[str] = None) -> AuditChain:
    """
    Get the global audit chain instance.
    
    Args:
        secret_key: Secret key for hash calculation (only used on first initialization)
        
    Returns:
        The global AuditChain instance
    """
    global _audit_chain
    
    if _audit_chain is None:
        if secret_key is None:
            from ..config.settings import get_settings
            secret_key = get_settings().AUDIT_SECRET_KEY
            
        _audit_chain = AuditChain(secret_key)
    
    return _audit_chain


async def log_immutable_phi_access(record: PHIAccessRecord) -> ChainedAuditRecord:
    """
    Log PHI access in the immutable audit chain.
    
    Args:
        record: PHI access record to log
        
    Returns:
        Chained audit record
    """
    audit_chain = await get_audit_chain()
    return await audit_chain.add_record(record)
