#! /usr/bin/python

import requests
import sys
class get_data:
    def get_current_data(url):
        headers = {'cache-control': 'no-cache'}
        try:
            r = requests.request("GET", url, headers=headers)
            return(r.text)
        except requests.exceptions.RequestException as e:
            print (e)
            sys.exit(1)
    