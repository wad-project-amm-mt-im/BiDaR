from flask import Blueprint, render_template, make_response, session, url_for, request, Markup
from flask_login import login_required, current_user
import json, urllib
searchModule = Blueprint('search', __name__)


@searchModule.route('/search')
@login_required
def search():
    return render_template('search.html', name=current_user.name)


@searchModule.route('/search', methods=['POST'])
@login_required
def get_query():
    if request.form.get('query'):
        querry = request.form.get('query')
        
        service_url = 'http://192.168.223.128:5003/'
        params = {
            'querry': querry,
            'limit': 10,
        }
        url = service_url + '?' + urllib.parse.urlencode(params)
        result = urllib.request.urlopen(url).read()
        
        

        service_url = 'http://192.168.223.128:5002/'
        params = {
            'rdf_content': result,
        }

        url = service_url + '?' + urllib.parse.urlencode(params)
        svg_content = urllib.request.urlopen(url).read().decode("utf-8")
        # svg_content = create_svg(result)  
        svg_path = "./static/tmp/svg_visualization.svg"
        rdf_path = "./static/tmp/rdf.ttl"
            
        session["svg_path"] = svg_path
        session["rdf_path"] = rdf_path
            
        with open(svg_path, "w") as f:
            f.write(svg_content)
        
        with open(rdf_path, "w") as f:
            from rdflib import Graph
            kg = Graph()
            kg.parse(data=result, format="json-ld")
            rdf_content = kg.serialize(format="ttl")
            f.write(rdf_content)
        
        return render_template('search_result.xhtml', svg=Markup(svg_content))
    render_template('search.html', name=current_user.name)


@searchModule.route('/download', methods=['POST'])
@login_required
def download():
    response_content = None
    download_type = request.form.get('download_format', "ttl")
    response_type = "text/plain"
    # print(f"Here: {download_type}")
    if download_type != "svg":
        from rdflib import Graph

        kg = Graph()
        kg.parse(session["rdf_path"], format="ttl")
        response_content = kg.serialize(format=download_type)
        
    elif download_type == "svg":
        with open(session["svg_path"]) as f:
            response_content = f.read()
        response_type = "text/html"

    response = make_response(response_content, 200)
    response.mimetype = response_type
    return response