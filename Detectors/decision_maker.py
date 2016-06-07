#!/usr/bin/python
from storage import Storage
from sklearn.externals import joblib


class DecisionMaker():


    def __init__(self, config):
        self.storage = Storage(config)
        
        self.models = { 
            'd' : joblib.load('models_binary/100decisionTreeD.pkl'),
            's_d' : joblib.load('models_binary/100decisionTreeS_D.pkl'),
            'sp_d' : joblib.load('models_binary/100decisionTreeSP_D.pkl'),
            'sp_dp' : joblib.load('models_binary/100decisionTreeSP_DP.pkl'),
        }
        
        self.features = ['bcount', 'pcount']
        self.filters = [
            'd', 's_d', 
            #'sp_d', 'sp_dp'
        ]
    

    def get_malware_tables(self, df, pred):

        if len(df) != len(pred):
            raise ValueError('Wrong length of dataframe or prediction!')

        table_src = set()
        table_dst = set()

        for i in xrange(len(pred)):
            if pred[i] != "BENIGN":
                #WARNING 's' filter
                #if 'dst' in data.iloc[i]:
                table_dst.add(df.iloc[i].dst)
                table_src.add(df.iloc[i].src)

        return table_src, table_dst


    def predict(self, data, s, malware_tables=None):
        
        df = self.storage.filter_data(data, nf_group_type=s, malware_tables=malware_tables)
        features = self.features[:]
        if s != "sp_dp":
            features.append('ucount')
        pred = self.models[s].predict(df[features])

        return self.get_malware_tables(pred)



    def make(self, timestamp=None, depth=None):

        result = None
        
        data = self.storage.select(timestamp, depth)
        
        malware_tables = self.predict(data, "d")
        
        malware_src, malware_dst = self.predict(data, "s_d", malware_tables=malware_tables)
        
        if len(malware_src) > 0:
            result = sorted(malware_src)

        #!
        #s = 's_d'

        #df = self.storage.filter_data(data, s)
        #pred = self.models[s].predict(df[features])
        
        #src_list = sorted(self.storage.get_src_by_predict(df, pred))
        #if len(src_list) > 0:
        #    result = "', '".join(src_list)
        
        return result

    def end(self):
        self.storage.close()
