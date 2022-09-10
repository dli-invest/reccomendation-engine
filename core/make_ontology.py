import types
from owlready2 import get_ontology, individual, Thing
onto = get_ontology("http://www.grandfleet.eu.org/ontologies/2022/7/stonks")
namespace = onto.get_namespace("http://www.grandfleet.eu.org/ontologies/2022/7/stonks")

with namespace:
    class buy(Thing):
        namespace = onto.get_namespace("http://www.grandfleet.eu.org/ontologies/2022/7/stonks")
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

    # another class for record earnings
    class memorandum(Thing):
        namespace = onto.get_namespace("http://www.grandfleet.eu.org/ontologies/2022/7/stonks")
        pass

    class mou(Thing):
        equivalent_to = [memorandum]
        pass

    
    class sell(Thing):
        namespace = onto.get_namespace("http://www.grandfleet.eu.org/ontologies/2022/7/stonks")
        pass

    class sell_off(Thing):
        pass

    class divest(Thing):
        pass

    class dispose(Thing):
        equivalent_to = [sell, sell_off, divest]

    # announces reports for financial results
    # attempt multiple search phrases
    # class reports(Thing):
    class q1(Thing):
        namespace = onto.get_namespace("http://www.grandfleet.eu.org/ontologies/2022/7/stonks")
        pass
    class q2(Thing):
        namespace = onto.get_namespace("http://www.grandfleet.eu.org/ontologies/2022/7/stonks")
        pass
    class q3(Thing):
        namespace = onto.get_namespace("http://www.grandfleet.eu.org/ontologies/2022/7/stonks")
        pass
    class q4(Thing):
        namespace = onto.get_namespace("http://www.grandfleet.eu.org/ontologies/2022/7/stonks")
        pass

    class first_quarter(Thing):
        equivalent_to = [q1]
        pass
    class second_quarter(Thing):
        equivalent_to = [q2]
        pass
    class third_quarter(Thing):
        equivalent_to = [q3]
        pass
    class fourth_quarter(Thing):
        equivalent_to = [q4]
        pass

onto.save(file = "company_headlines.owl", format = "rdfxml")

# honestly dont care about the thing link as long as these things work in practise