'''
Usage:
1) To Create
merkle_tree = MerkleTree()
merkle_tree.createMerkleTree(<List of Transactions(str now)>)
2) To Verify
verifyMerkleTree(merkle_tree.mrkl_root)


EG)newMerkleTree = MerkleTree()
newMerkleTree.createMerkleTree(["a","b","c","d","e","f"])
print(verifyMerkleTree(newMerkleTree.mrkl_root))
'''

from utils import getHashValue, verifyMerkleTree
from typing import List

class MerkleTreeNode:
    def __init__(self,value = ""):
        self.hashValue: str = ""
        self.leftNode: MerkleTreeNode = None
        self.rightNode: MerkleTreeNode = None

    def calculate(self, leftNode, rightNode):
        self.leftNode = leftNode
        self.rightNode = rightNode
        if len(self.rightNode.hashValue)>0:
            self.hashValue = getHashValue(self.leftNode.hashValue, self.rightNode.hashValue)
        else:
            self.hashValue = getHashValue(self.leftNode.hashValue, "" )

    def __eq__(self, other: MerkleTreeNode) -> bool :
        if other is None:
            return False
        return self.hashValue == other.hashValue

class MerkleTree:
    def __init__(self):
        self.mrkl_root: MerkleTreeNode = None
        self.fullTree: List[MerkleTreeNode] = []

    def __eq__(self, other: MerkleTree) -> bool:
        if other is None:
            return False
        return other.mrkl_root==self.mrkl_root

    def getTxnNodes(self, txnList: List[str]) -> List[MerkleTreeNode] :
        txnNodes = []
        for i in txnList:
            txnNodes.append(MerkleTreeNode(i))

        return txnNodes

    def get_new_level(self, txnNodes: List[MerkleTreeNode]) -> List[MerkleTreeNode]:
        index: int = 0
        newLevel: List[MerkleTreeNode] = []
        while index<len(txnNodes):
            leftNode: MerkleTreeNode = txnNodes[index]
            index+=1
            rightNode: MerkleTreeNode = MerkleTreeNode()
            if index!=len(txnNodes):
                rightNode = txnNodes[index]

            newTempNode: MerkleTreeNode = MerkleTreeNode()
            newTempNode.calculate(leftNode,rightNode)
            newLevel.append(newTempNode)
            index+=1

        return newLevel

    def createMerkleTree(self, txnList: List[str]):
        txnNodes: List[MerkleTreeNode] = self.getTxnNodes(txnList)
        self.fullTree.extend(txnNodes)
        newLevel: List[MerkleTreeNode] = self.get_new_level(txnNodes)
        self.fullTree.extend(newLevel)
        while len(newLevel)>1:
            newLevel = self.get_new_level(newLevel)
            self.fullTree.extend(newLevel)

        self.mrkl_root = newLevel[0]
