import sys
import os
import numpy as NP
import time
import pickle
from utils   import *
from dator import *
from regressor import *

class LDCascador(object):
    """
    Cascade regression for landmark
    """
    def __init__(self):     
        self.name     = None
        self.version  = None
        self.stageNum = None
        
        self.dataWrapper = None
        self.regWrapper  = None
        self.regressors  = []
        self.meanShape   = None

    def printParas(self):
        print('------------------------------------------')
        print('----------   Configuration    ------------')
        print('Name           = %s'%(self.name))
        print('Version        = %s'%(self.version))
        print('Stage Num      = %s'%(self.stageNum))
        print('\n-- Data Config --')
        self.dataWrapper.printParas()
        print('\n-- Regressor Config --')
        self.regWrapper.printParas()
        print('---------   End of Configuration   -------')
        print('------------------------------------------\n')
                   
    def config(self, paras):
         self.name     = paras['name']
         self.version  = paras['version']
         self.stageNum = paras['stageNum']

         ### Construct the regressor wrapper
         regPara = paras['regressorPara']
         self.regWrapper = RegressorWrapper(regPara)

         ### Construct the data wrapper
         dataPara = paras['dataPara']
         if 'dataset' in paras:
             dataPara['dataset'] = paras['dataset']
         self.dataWrapper = DataWrapper(dataPara)

    def train(self, save_path):
        ### mkdir model folder for train model
        if not os.path.exists('%s/model'%(save_path)):
            os.mkdir('%s/model'%(save_path))
        
        ### read data first 
        begTime = time.time()
        trainSet = self.dataWrapper.read()     
        dataNum = trainSet.initShapes.shape[0]
        self.meanShape = trainSet.meanShape
        t = getTimeByStamp(begTime, 
                           time.time(), 'min')
        print("\tLoading Data: %f mins"%(t))
        print("\tData Number : %d"%(dataNum))
        trainSet.calResiduals()
        sumR = NP.mean(NP.abs(trainSet.residuals))
        print("\tManhattan Distance in MeanShape : %f\n"%sumR)
        
        for idx in xrange(self.stageNum):
            print("\t%drd stage begin ..."%idx)
            begTime = time.time()            
            ### train one stage
            reg = self.regWrapper.getClassInstance(idx)
            reg.train(trainSet)
            self.regressors.append(reg)        
            
            ### calculate the residuals
            trainSet.calResiduals()
            sumR = NP.mean(NP.abs(trainSet.residuals))
            print("\tManhattan Distance in MeanShape : %f"%sumR)

            t = getTimeByStamp(begTime, 
                               time.time(), 'min')
            print("\t%drd stage end : %f mins\n"%(idx, t))
        self.saveModel(save_path)

    def detect(self, img, bndbox, initShape):
        mShape = Shape.shapeNorm2Real(self.meanShape,
                                      bndbox)   
        for reg in self.regressors:
            affineT = Affine.fitGeoTrans(mShape,
                                         initShape)
            reg.detect(img, bndbox, initShape, affineT)
        
    
    def loadModel(self, model):
        path_obj = open(model, 'r').readline().strip()      
        folder = os.path.split(model)[0]
        objFile = open("%s/%s"%(folder, path_obj), 'rb')
        self = pickle.load(objFile)
        objFile.close()
        return self
        
    def saveModel(self, save_path):
        name = self.name.lower()
        model_path = "%s/model/train.model"%(save_path)
        model = open(model_path, 'w')        
        model.write("%s.pyobj"%(name))
        obj_path = "%s/model/%s.pyobj"%(save_path, name)
        
        objFile = open(obj_path, 'wb')
        pickle.dump(self, objFile)
        objFile.close()        
        model.close()
        
    

