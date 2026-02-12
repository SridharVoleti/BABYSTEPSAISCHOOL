# 2025-10-22: Core Blockchain Academic Ledger Engine
# Authors: Cascade

from .ledger_service import Blockchain

class LedgerEngine:
    """
    # 2025-10-22: Orchestrates the blockchain ledger services.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the blockchain.
        """
        self.blockchain = Blockchain()

    def add_achievement(self, achievement_data):
        """
        # 2025-10-22: Adds a new achievement to the ledger.
        """
        # 2025-10-22: In a real system, transactions would be gathered before creating a new block.
        # For simplicity, we create a new block for each achievement.
        last_block = self.blockchain.last_block
        last_proof = last_block['proof']
        proof = self.blockchain.proof_of_work(last_proof)

        # 2025-10-22: Add the transaction.
        self.blockchain.new_transaction(achievement_data)

        # 2025-10-22: Forge the new Block by adding it to the chain.
        previous_hash = self.blockchain.hash(last_block)
        block = self.blockchain.new_block(proof, previous_hash)

        return {"message": "New achievement added to ledger", "block": block}

    def get_full_chain(self):
        return self.blockchain.chain
