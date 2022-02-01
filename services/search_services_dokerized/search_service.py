from flask import Flask, make_response, request

from googleSearchMservice.micro_google_search import searchOnGoogle
import os

app = Flask(__name__)


@app.route('/', methods=['GET'])
def search():
    try:
        querry = request.args.get('querry')
        limit = int(request.args.get('limit', 1))

        print(f"querry: {querry}, limit: {limit}")
        response =  make_response(searchOnGoogle(querry, limit), 200) # search micro service call
        response.mimetype = "text/plain"
        
        return response

    except Exception as e:
        print(e)
        return make_response({"result": "Bad Request"}, 400)

'''
@app.route('/search', methods=['POST'])
def get_query():
    if request.form.get('query'):
        querry = request.form.get('query')
        result = searchOnGoogle(querry) # search micro service call
        
        svg_content = create_svg(result)
        
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

'''

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)