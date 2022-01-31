from rdflib import Graph
from rdflib.parser import Parser
from rdflib import *
from SPARQLWrapper import SPARQLWrapper
from rdflib.plugin import register, Serializer, Parser
# from rdflib_jsonld import

g = Graph()

g.parse("../google_response.json", format="json-ld")


strg = g.serialize(format="ttl")

f = open("data.ttl", "w")

f.write(strg)

f.close()
