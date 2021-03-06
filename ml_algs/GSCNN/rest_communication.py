# By: Oscar Andersson 2019

from flask import Flask, abort
import json
from eval import main as run_eval
import sys

import time

start_time = time.time()
last_request = time.time()
eval_calls = 0

app = Flask(__name__)

@app.route('/')
def index():
    time_since = str(int(round(time.time() - last_request)))
    mean_call_time = 0
    if eval_calls > 0:
        mean_call_time = round((time.time()-start_time) / eval_calls)
    return ("Time since last request: " + time_since +
            " seconds<br>Number of eval-calls: " + str(eval_calls) +
            "<br>Mean call time: " + str(mean_call_time) + " seconds")

@app.route('/eval', methods=['GET'])
def get_eval_results():
    global last_request, eval_calls
    print("Running evaluation")

    last_request = time.time()
    eval_calls += 1
    eval_results = run_eval()
    
    try:
        res = app.response_class(
            status=200,
            response=json.dumps(eval_results),
            mimetype='application/json'
        )
        return res
    except Exception as exception:
        print(exception)
        abort(500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
