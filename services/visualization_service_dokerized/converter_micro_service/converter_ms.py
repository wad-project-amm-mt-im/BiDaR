from flask import Flask, request, make_response
from rdflib import Graph
from time import time

import os
import mimetypes

mimetypes.add_type('images/svg+xml', '.svg')

app = Flask(__name__)


@app.route('/', methods=['GET'])
def convert_to_svg():
    if not request.args.get("rdf_content"):
        return make_response({"Error Reason":" No content Porvided"}, 400)
    try:
        svg_content = request.args.get("rdf_content")
        kg = Graph()
        kg.parse(data=svg_content, format="json-ld")
        strg = kg.serialize(format="ttl")
        response = make_response(strg, 200)
        response.content_type = "text/plain"
        return response
    except Exception as e:
        return  make_response({"Error Reason": f"Internal error: {e}"}, 500)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)