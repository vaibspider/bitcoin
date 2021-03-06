import ScriptEngine
from Crypto.PublicKey import RSA
import utils
from typing import List
from constants import hashSize

class TransactionOutput:
    def __init__(self, amount: int):
        self.amount = amount
        self.scriptPubKey = ""

    def __repr__(self):
        return '{}:{}'.format(self.amount, self.scriptPubKey)

    def createScriptPubKey(self, publicKeyOfReceiver:str):
        self.scriptPubKey = ScriptEngine.createPubKeyScript(utils.getHashValue(publicKeyOfReceiver,hashSize))

class TransactionInput:
    def __init__(self, prevTxn: str, prevIndex: int) -> None:
        self.prevTxn: str = prevTxn
        self.prevIndex: int = prevIndex
        self.scriptSig: str = ""
        self.dataToSign: str = ""

    def __repr__(self):
        return '{}:{}'.format(self.prevTxn, self.prevIndex)


    def createDataToSign(self, prevPubKeyScript: str, myPublicKey: str, txnOutputs: List[TransactionOutput]):
        inp = self #First Create TxnInp and txnOutputs
        dataToSign = ""
        dataToSign += inp.prevTxn
        dataToSign += str(inp.prevIndex)
        for i in txnOutputs:
            dataToSign += str(i.amount)
            dataToSign += i.scriptPubKey
        self.dataToSign = dataToSign
        return dataToSign


    def createSignature(self, dataToSign: str, privateKey):
        return utils.sign(privateKey, dataToSign)


    def createScriptSig(self, prevPubKeyScript: str, myPublicKey: str, myPrivateKey: str, txnOutputs: List[TransactionOutput]):
        dataToSign = self.createDataToSign(prevPubKeyScript, myPublicKey, txnOutputs)
        signature = self.createSignature(dataToSign, RSA.importKey(myPrivateKey))
        self.scriptSig = ScriptEngine.createScriptSig(prevPubKeyScript, myPublicKey, signature)



class Transaction:
    def __init__(self, txnInputs: List[TransactionInput], txnOutputs: List[TransactionOutput], lockTime: int):
        self.txnInputs = txnInputs
        self.txnOutputs = txnOutputs
        self.lockTime = lockTime
        self.hash = ""

    def getRawDataToHash(self):
        dataToHash = ""
        dataToHash+= str(len(self.txnInputs))
        for i in self.txnInputs:
            dataToHash+= i.prevTxn
            dataToHash+= str(i.prevIndex)
            dataToHash+= i.scriptSig

        dataToHash+= str(len(self.txnOutputs))
        for i in self.txnOutputs:
            dataToHash+= str(i.amount)
            dataToHash+= str(i.scriptPubKey)

        dataToHash+= str(self.lockTime)

        return dataToHash


    def calculateHash(self) -> None:
        rawData = self.getRawDataToHash()
        self.hash = utils.getHashValue(rawData,hashSize)

    def getHash(self) -> str:
        if self.hash == "":
            self.calculateHash()
        return self.hash

    def getScriptPubKey(self, index: int) -> str:
        return self.txnOutputs[index].scriptPubKey
