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
        
        self.features = ['bcount', 'pcount']

        
    
    def make(self, timestamp=None, depth=None):
        result = "empty"
        
        data = self.storage.select(timestamp, depth)

        print "found: ", len(data)

        #!
        s = 's_d'

        features = self.features[:]
        if s != "sp_dp":
            features.append('ucount')
        
        df = self.storage.filter_data(data, s)
        pred = self.models[s].predict(df[features])
        
        src_list = self.storage.get_src_by_predict(data, pred)
        if len(src_list) > 0:
            result = ",".join(src_list)
        
        return result

    def end(self):
        self.storage.close()