from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
import json
import os
from rdflib import Graph
from rdflib.parser import Parser
from rdflib import *
from SPARQLWrapper import SPARQLWrapper
from rdflib.plugin import register, Serializer, Parser
from flask import Markup
# from rdflib_jsonld import


vizualization = Blueprint('vizualization', __name__)



def create_svg(result_as_str):

    kg = Graph()
    
    kg.parse(data=result_as_str, format="json-ld")
    strg = kg.serialize(format="ttl")
    
    f = open("./services/visualization_service/ontology_visualization/data.ttl", "w")
    f = open("./tmp/data.ttl", "w")
    f.write(strg)
    f.close()
    
    os.system("/usr/bin/python3 ./services/visualization_service/ontology_visualization/ontology_viz.py \
        -o ./services/visualization_service/ontology_visualization/test.dot \
            ./tmp/data.ttl \
                -O ./services/visualization_service/ontology_visualization/ontology.ttl")
    os.system("dot -Tsvg -o ./static/test-ontology-visualization.svg \
        ./services/visualization_service/ontology_visualization/test.dot")
    
    f = open('./static/test-ontology-visualization.svg')
    
    svg_content = f.read()
    
    f.close()
    
    os.system("rm -rf ./static/test-ontology-visualization.svg")
    
    return svg_content


@vizualization.route('/search_result/<vis_type>/', methods=['POST'])
@login_required
def search_result(vis_type):
    # main page for query big data
    svg_content = create_svg(session['result'])
    return render_template('search_result.xhtml', svg=Markup(svg_content))

