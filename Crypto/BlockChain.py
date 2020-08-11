from Block import Block
from typing import Dict, List, Optional, Tuple
from Transaction import Transaction, TransactionOutput
import copy
from constants import BlockStatus

class BlockChain:
    def __init__(self) -> None:
        self.mempool: Dict[str, Transaction] = {} # unconfirmed transactions
        self.unspntTxOut: Dict[str, Dict[int, TransactionOutput]] = {} # confirmed but unspent transactions outputs
        self.headMap: Dict[str, BlockNode] = {} # map from a head block hash to the blocknode
        self.longest: str = "" # longest chain-head hash
        self.blockMap: Dict[str, BlockNode] = {} # map from all block hashes to the blocknode
        # blockstates is a Dict[blockHash, (mempool, unspntTxOut)]
        self.blockStates: Dict[str, Tuple[Dict[str, Transaction], Dict[str, Dict[int, TransactionOutput]]]] = {}
        self.blockBalance: Dict[str, int] = {} # map from all block hashes to the corresponding wallet balance
        self.currentBalance: int = 0

    # insert a new block into blockchain, return True (if all ok) return False (if block rejected)
    def insert(self, block: Block, pubKey: str) -> Tuple[bool, BlockStatus]:
        # if this is Genesis Block
        if block.blockHeader.prevBlock is "":
            print("genesis block")
            newBlkNode = BlockNode(block)
            self.blockMap[block.hash] = newBlkNode
            self.headMap[block.hash] = newBlkNode
            self.longest = block.hash
            unspntTxOut = {}
            balance: int = 0
            for txn in block.txnList:
                nums = list(range(len(txn.txnOutputs)))
                dictTxnOuts = dict(zip(nums, txn.txnOutputs))
                unspntTxOut[txn.getHash()] = dictTxnOuts
                for txnOut in txn.txnOutputs:
                    if txnOut.scriptPubKey is pubKey:
                        balance += txnOut.amount
            self.blockBalance[block.hash] = balance
            self.currentBalance = balance
            self.blockStates[block.hash] = ({}, unspntTxOut)
            self.mempool = self.blockStates[self.longest][0]
            self.unspntTxOut = self.blockStates[self.longest][1]
        # for any block other than genesis block
        else:
            # prevblock exists in the blockchain
            if block.blockHeader.prevBlock in self.blockMap:
                # temporary buffer of txOutputs in the current block
                bufferTxOuts: Dict[str, Dict[int, TransactionOutput]] = {}
                for txn in block.txnList:
                    nums = list(range(len(txn.txnOutputs)))
                    dictTxnOuts = dict(zip(nums, txn.txnOutputs))
                    bufferTxOuts[txn.getHash()] = dictTxnOuts
                # to detect cycles in block
                atLeastOnePresent = False
                # check if any transaction in this new block is unknown to us
                # verify other important semantics
                for txn in block.txnList:
                    if txn.getHash() not in self.blockStates[block.blockHeader.prevBlock][0]:
                        # invalid transaction; reject the block
                        return (False, BlockStatus.MISSING_TXN)
                    for txnIn in txn.txnInputs:
                        if txnIn.prevTxn not in self.blockStates[block.blockHeader.prevBlock][1]:
                            # prev transaction not present in unspntTxOut
                            if txnIn.prevTxn not in bufferTxOuts:
                                # prev transaction not present in current block too
                                return (False, BlockStatus.MISSING_PREV_TXN)
                        else:
                            # TODO? check if the txnOutputs list/dict is not empty?
                            atLeastOnePresent = True
                if atLeastOnePresent is False:
                    return (False, BlockStatus.CYCLE_DETECTED)
                # update the mempool and unspntTxOut structures for the new block
                self.blockStates[block.hash] = (copy.deepcopy(self.blockStates[block.blockHeader.prevBlock][0]), copy.deepcopy(self.blockStates[block.blockHeader.prevBlock][1]))
                for txn in block.txnList:
                    if txn.getHash() in self.blockStates[block.hash][0]:
                        nums = list(range(len(txn.txnOutputs)))
                        dictTxnOuts = dict(zip(nums, txn.txnOutputs))
                        # can't do the following commented operation now
                        #self.blockStates[block.hash][1][txn.getHash()] = dictTxnOuts
                        self.blockStates[block.hash][0].pop(txn.getHash())
                        # also remove the relevant txnOutputs from unspntTxOut
                        for txnIn in txn.txnInputs:
                            # we can use block.hash instead of prevBlock's hash, as we have done deepcopy above
                            # .pop() would work, as we have used a Dict instead of a List - so the indices for other elements won't change
                            if txnIn.prevTxn in self.blockStates[block.hash][1]:
                                self.blockStates[block.hash][1][txnIn.prevTxn].pop(txnIn.prevIndex)
                            elif txnIn.prevTxn in bufferTxOuts:
                                bufferTxOuts[txnIn.prevTxn].pop(txnIn.prevIndex)
                            else:
                                # Invalid path; impossible to come here
                                return (False, BlockStatus.REJECTED)
                        # on becoming an empty list of txnOutputs, remove the transaction hash from unspntTxOut
                        if len(self.blockStates[block.hash][1][txnIn.prevTxn].keys()) == 0:
                            self.blockStates[block.hash][1].pop(txnIn.prevTxn)
                    else:
                        # invalid path; impossible to come here
                        return (False, BlockStatus.REJECTED)
                # Now, add the buffered (temporary) txnOuts into unspntTxOut
                for txn in block.txnList:
                    if len(bufferTxOuts[txn.getHash()].keys()) != 0:
                        self.blockStates[block.hash][1][txn.getHash()] = bufferTxOuts[txn.getHash()]

                # add the new block to blockMap and headMap
                newBlkNode = BlockNode(block, self.blockMap[block.blockHeader.prevBlock])
                self.blockMap[block.hash] = newBlkNode
                self.headMap[block.hash] = newBlkNode
                # update the longest pointer and corresponding mempool and unspntTxout cache if necessary
                if block.blockHeader.prevBlock in self.headMap:
                    if newBlkNode.len > self.headMap[self.longest].len:
                        self.longest = block.hash
                        self.mempool = self.blockStates[self.longest][0]
                        self.unspntTxOut = self.blockStates[self.longest][1]
                    self.headMap.pop(block.blockHeader.prevBlock)
                # Check- balance should not be a reference, it must be a copy
                balance: int = self.blockBalance[block.blockHeader.prevBlock]
                for txn in block.txnList:
                    for txnOut in txn.txnOutputs:
                        if txnOut.scriptPubKey is pubKey:
                            balance += txnOut.amount
                self.blockBalance[block.hash] = balance
                # currentBalance will always correspond to the current longest chain block head
                self.currentBalance = self.blockBalance[self.longest]
            # prevblock absent in the blockchain
            else:
                # invalid block; reject it
                return (False, BlockStatus.MISSING_PREV_BLOCK)
        print("returning True")
        return (True, BlockStatus.VALID)

# unit of node used inside blockchain implemented as linked list
class BlockNode:
    def __init__(self, block: Block, prevBlk = None) -> None:
        self.block = block
        if (prevBlk is None):
            self.prevBlk = None
            self.len: int = 1
        else:
            self.prevBlk = prevBlk
            self.len = self.prevBlk.len + 1
