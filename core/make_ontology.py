import types
from owlready2 import get_ontology, individual, Thing
onto = get_ontology("http://www.grandfleet.eu.org/ontologies/2022/7/company_headlines")
namespace = onto.get_namespace("http://www.grandfleet.eu.org/ontologies/2022/7/company_headlines")

with namespace:
    class buy(Thing):
        namespace = onto.get_namespace("http://www.grandfleet.eu.org/ontologies/2022/7/company_headlines")
        pass

    class takeover(Thing):
        pass 
    
    class take_over(Thing):
        pass

    class purchase(Thing):
        pass

    class acquire(Thing):
        pass
        equivalent_to = [buy, takeover, take_over, purchase]

onto.save(file = "company_headlines.owl", format = "rdfxml")

# honestly dont care about the thing link as long as these things work in practise