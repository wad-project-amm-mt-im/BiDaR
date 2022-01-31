import re
import sys

import pandas as pd
import pyspark
import urllib
import urllib.request

import sys
if sys.version_info[0] < 3: 
    from StringIO import StringIO
else:
    from io import StringIO

file = open("./df_received.json", "r")


TESTDATA = file.read()

pd_df = pd.read_json(TESTDATA)

service_url = 'http://localhost:5011/tasks'
params = {
    'df_json': pd_df.to_json(),
    'option': "stackplot",
}
url = service_url + '?' + urllib.parse.urlencode(params)
result = urllib.request.urlopen(url).read()

import json

dict = json.loads(result)


