def configuration(token,model='gpt-oss:20b'):
    return {
        'models':{'mode':'replace','providers':{'ihb':{'baseUrl':'http://ihb-relay:8080/v1',
            'apiKey':token,'api':'openai-completions','models':[{'id':model,'name':model,
                'reasoning':True,'input':['text'],'contextWindow':65536,'maxTokens':4096,
                'cost':{'input':0,'output':0,'cacheRead':0,'cacheWrite':0}}]}}},
        'agents':{'defaults':{'workspace':'/workspace','model':{'primary':'ihb/'+model,'fallbacks':[]},
            'models':{'ihb/'+model:{'params':{'temperature':0}}},'thinkingDefault':'medium',
            'timeoutSeconds':600,'skipBootstrap':True,
            'compaction':{'memoryFlush':{'enabled':False}},'sandbox':{'mode':'off'}}},
        'tools':{'allow':['read','write','edit','exec','process'],
            'elevated':{'enabled':False},'exec':{'host':'gateway','security':'full','ask':'off'}},
        'channels':{},'plugins':{'enabled':False},'browser':{'enabled':False},
        'update':{'checkOnStart':False},'gateway':{'mode':'local','bind':'loopback'},
    }
