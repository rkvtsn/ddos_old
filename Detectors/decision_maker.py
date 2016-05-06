#!/usr/bin/python
from storage import Storage
from sklearn.externals import joblib


class DecisionMaker():

    def __init__(self, config):
        self.storage = Storage(config)
        
        self.models = { 
            'd' : joblib.load('models/100decisionTreeD.pkl'),
            's_d' : joblib.load('models/100decisionTreeS_D.pkl'),
            'sp_d' : joblib.load('models/100decisionTreeSP_D.pkl'),
            'sp_dp' : joblib.load('models/100decisionTreeSP_DP.pkl'),
        }

        
    def predict(data, s):
        return self.models[s].predict(self.storage.filter_data(data, s))
    
    def make(self, timestamp=None, depth=None):
        result = "empty"
        
        data = self.storage.select(timestamp, depth)

        print "found: ", len(data)

        pred = self.predict(data, 's_d')
        
        src_list = storage.get_src_by_predict(data, pred)
        if len(src_list) > 0:
            result = ",".join(src_list)
        
        return result

    def end(self):
        self.storage.close()