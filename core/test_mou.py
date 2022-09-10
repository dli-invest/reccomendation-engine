import holmes_extractor as holmes
import unittest

ontology = holmes.Ontology("example/ontologies/company_headlines.owl")
class TestCustomOntology(unittest.TestCase):
# ontology = holmes.Ontology("core/holmes.owl")
    def test_upper(self):

        manager = holmes.Manager("en_core_web_trf", ontology=ontology, number_of_workers=1)

        # Register search phrase
        manager.register_search_phrase("mou with ENTITYORG")
        manager.register_search_phrase("sign mou")

        # Parse documents
        manager.parse_and_register_document("Canadian Premium Sand Inc. Executes a Memorandum of Understanding with Hanwha Solutions", "1")
        manager.parse_and_register_document("ImagineAR and Loop Insights Sign MOU To Integrate Augmented Reality and Artificial Intelligence, Creating Real-Time Actionable Data For Brands To Hyper Target Consumers and Sports Fans", "2")
        # Perform matching
        matches = manager.match()
        print(matches)
        # -> ['Brewin Dolphin', 'Silicon Motion Technology Corp', 'cybersecurity company Mandiant', 'Starbucks']

if __name__ == '__main__':
    unittest.main()
