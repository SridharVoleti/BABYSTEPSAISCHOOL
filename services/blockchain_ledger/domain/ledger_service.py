# 2025-10-22: Service for managing a simple blockchain ledger
# Authors: Cascade

import hashlib
import json
from time import time

class Blockchain:
    """
    # 2025-10-22: A simple implementation of a blockchain to store academic achievements.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the blockchain with a genesis block.
        """
        self.chain = []
        self.current_transactions = []
        # 2025-10-22: Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        # 2025-10-22: Creates a new block and adds it to the chain.
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # 2025-10-22: Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, achievement_data):
        """
        # 2025-10-22: Adds a new transaction (achievement) to the list of transactions.
        """
        self.current_transactions.append(achievement_data)
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        # 2025-10-22: Hashes a block (SHA-256).
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        # 2025-10-22: Simple Proof of Work algorithm.
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        # 2025-10-22: Validates the proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
