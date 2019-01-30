from django.shortcuts import render

# Create your views here.

def get_common_response_by_api():
    return {
        'error_code': 0,
        'msg': '',
        'data': [],
    }
