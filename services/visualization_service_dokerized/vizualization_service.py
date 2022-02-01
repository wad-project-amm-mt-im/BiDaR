from flask import Flask, request, make_response
from rdflib import Graph
from time import time

import os
import mimetypes
import urllib


mimetypes.add_type('images/svg+xml', '.svg')


app = Flask(__name__)


def create_svg(data_as_ttl):
    strg = str(data_as_ttl)
    unique_prefix = f"./{str(request.remote_addr)}+_{time()}"
    
    dat_ttl_path = f"{unique_prefix}_data.ttl"
    dat_dot_path = f"{unique_prefix}_data.dot"
    dat_svg_path = f"{unique_prefix}_data.svg"

    f = open(dat_ttl_path, "w")
    f.write(strg)
    f.close()
    
    os.system(f"python3 ./ontology_visualization/ontology_viz.py \
        -o {dat_dot_path}  {dat_ttl_path} -O ./ontology_visualization/ontology.ttl")
    
    os.system(f"dot -Tsvg -o {dat_svg_path} {dat_dot_path}")
    
    f = open(f'{dat_svg_path}')
    
    svg_content = f.read()
    
    f.close()

    os.system(f"rm -rf {dat_ttl_path}")
    os.system(f"rm -rf {dat_dot_path}")
    os.system(f"rm -rf {dat_svg_path}")
    
    return svg_content


@app.route('/', methods=['GET'])
def convert_to_svg():
    if not request.args.get("rdf_content"):
        return make_response({"Error Reason":" No content Porvided"}, 400)
    try:
        svg_content = request.args.get("rdf_content")
        print(svg_content)
        #with open("content_received.json-ld", "w") as f:
        #    f.write(svg_content)
        response = make_response(create_svg(svg_content), 200)
        response.content_type = "images/svg+xml"
        return response
    except Exception as e:
        return  make_response({"Error Reason": f"Internal error: {e}"}, 500)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)