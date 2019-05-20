# -*- coding: utf-8 -*-
"""
Created on Fri Sep 21 08:41:12 2018

@author: zhangj
"""

import http.client, uuid, json

def msft_translate(text):
    # Replace the subscriptionKey string value with your valid subscription key.
    subscriptionKey = 'Enter your key'
    
    host = 'api.cognitive.microsofttranslator.com'
    path = '/translate?api-version=3.0'
    
    params = "&to=en";
    
    def translate (content):
    
        headers = {
            'Ocp-Apim-Subscription-Key': subscriptionKey,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
    
        conn = http.client.HTTPSConnection(host)
        conn.request ("POST", path + params, content, headers)
        response = conn.getresponse ()
        return response.read ()
    
    requestBody = [{
        'Text' : text,
    }]
    content = json.dumps(requestBody, ensure_ascii=False).encode('utf-8')
    result = translate (content)
    output = json.loads(result)
    
    return(output[0]['translations'][0]['text'])
