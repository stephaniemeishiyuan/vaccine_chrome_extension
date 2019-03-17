import numpy as np
from bert_serving.client import BertClient
from termcolor import colored
from flask_cors import CORS
import os

prefix_q = '##### **Q:** '
topk = 5
import sys

from flask import Flask, render_template, request, redirect, Response, jsonify
import random, json

app = Flask(__name__)
CORS(app)

@app.route("/receive", methods = ['POST'])
def worker():
    data = request.get_json()
    filepath = os.path.abspath('README2.md')
    print(filepath)
    with open(filepath) as fp:
        questions = [v.replace(prefix_q, '').strip() for v in fp if v.strip() and v.startswith(prefix_q)]
    with BertClient(port=5555, port_out=5556) as bc:
        doc_vecs = bc.encode(questions)
    score = np.sum(data['result'] * doc_vecs, axis=1)
    topk_idx = np.argsort(score)[::-1][:topk]
    result = questions[topk_idx[0]]
    return jsonify({'message': result})

if __name__ == "__main__":
	app.run()
