import types
from owlready2 import get_ontology, Thing

onto = get_ontology("file:////workspaces/reccomendation-engine/core/holmes.owl").load()

classes =onto.classes()

for item in classes:
    print(item)

print(onto.acquire)

print(onto.acquire)

print(onto.buy)

help(onto.acquire)

onto.save(file = "test.owl", format = "rdfxml")