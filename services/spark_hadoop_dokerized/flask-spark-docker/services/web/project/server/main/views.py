# services/web/server/main/views.py


import redis
from rq import Queue, push_connection, pop_connection
from flask import current_app, render_template, Blueprint, jsonify, request, make_response
from pandas import DataFrame as df
import pandas as pd
from server.main.tasks import create_task, get_spark_df, get_data_for_plots

import json

main_blueprint = Blueprint('main', __name__,)

@main_blueprint.route('/', methods=['GET'])
def home():
    return render_template('main/home.html')


@main_blueprint.route('/tasks', methods=['GET'])
def run_task():
    __df_as_str_json = request.args.get("df_json")
    __option = request.args.get("option")
    
    request_df = pd.read_json(__df_as_str_json)
    #with open("df_received.json", "w") as f:
    #    f.write(request_df.to_json())
    spark_df = get_spark_df(request_df)
    
    if __option == "stackplot":
        relevant_columns=["countryLabel", "population", "month", "year"]
    elif __option == "lineplot":
        relevant_columns=["countryLabel", "lifeExpectancy", "month", "year"]
    elif __option == "pieplot": 
        relevant_columns=["countryLabel", "HDI", "month", "year"]
    
    data = get_data_for_plots(spark_df, relevant_columns=relevant_columns)

    response =  make_response(json.dumps(data), 200) 
    response.mimetype = "text/plain"
    return response


@main_blueprint.route('/tasks/<task_id>', methods=['GET'])
def get_status(task_id):
    q = Queue()
    task = q.fetch_job(task_id)
    if task:
        response_object = {
            'status': 'success',
            'data': {
                'task_id': task.get_id(),
                'task_status': task.get_status(),
                'task_result': task.result,
            }
        }
    else:
        response_object = {'status': 'error'}
    return jsonify(response_object)


@main_blueprint.before_request
def push_rq_connection():
    push_connection(redis.from_url(current_app.config['REDIS_URL']))


@main_blueprint.teardown_request
def pop_rq_connection(exception=None):
    pop_connection()
