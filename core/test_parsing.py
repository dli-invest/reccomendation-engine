import holmes_extractor as holmes
import unittest

class TestCustomOntology(unittest.TestCase):
# ontology = holmes.Ontology("core/holmes.owl")
    def test_upper(self):
        ontology = holmes.Ontology("example/ontologies/company_headlines.owl")
        manager = holmes.Manager("en_core_web_trf", ontology=ontology, number_of_workers=1)

        # Register search phrase
        manager.register_search_phrase("An ENTITYORG takes over an ENTITYORG")

        # Parse documents
        manager.parse_and_register_document("Royal Bank of Scotland announces it intends to acquire Brewin Dolphin", "1")
        manager.parse_and_register_document("Chipmaker MaxLinear Inc announced on Thursday it will buy Silicon Motion Technology Corp for nearly $4 billion.", "2")
        manager.parse_and_register_document("Last month, cybersecurity company Mandiant was purchased by Alphabet", "3")
        manager.parse_and_register_document("The Starbucks takeover by Kaseya", "4")

        # Perform matching
        matches = manager.match()

        # Check all documents matched
        assert len(matches) == 4
        # -> 4

        # Extract companies doing the taking over
        print([match['word_matches'][0]['document_phrase'] for match in matches])
        word_matches = [match['word_matches'][0]['document_phrase'] for match in matches]
        assert word_matches == ['Royal Bank', 'Chipmaker MaxLinear Inc', 'Alphabet', 'Kaseya']
        # -> ['Royal Bank', 'Chipmaker MaxLinear Inc', 'Alphabet', 'Kaseya']

        # Extract companies being taken over
        print([match['word_matches'][2]['document_phrase'] for match in matches])
        word_matches = [match['word_matches'][2]['document_phrase'] for match in matches]
        assert word_matches == ['Brewin Dolphin', 'Silicon Motion Technology Corp', 'cybersecurity company Mandiant', 'Starbucks']
        # -> ['Brewin Dolphin', 'Silicon Motion Technology Corp', 'cybersecurity company Mandiant', 'Starbucks']

    def test_purchase_agreement(self):
        ontology = holmes.Ontology("example/ontologies/company_headlines.owl")
        manager = holmes.Manager("en_core_web_trf", ontology=ontology, number_of_workers=1)

        # Register search phrase
        manager.register_search_phrase("An ENTITYORG announces agreement to purchase")

        # parse documents
        manager.parse_and_register_document("Canadian Premium Sand Inc. Announces Agreement to Purchase Land for its Solar Glass Manufacturing Facility", "1")
        matches = manager.match()

        print(matches)

    # extend spacy pipe to extract financial results.
    # def test_financial_results(self):
    #     ontology = holmes.Ontology("example/ontologies/company_headlines.owl")
    #     manager = holmes.Manager("en_core_web_trf", ontology=ontology, number_of_workers=1)

    #     # Register search phrase
    #     manager.register_search_phrase("ENTITYORG reports financial results")
    #     # entitization of first_quarter second_quarter third_quarter fourth_quarter
    #     manager.register_search_phrase("NOUN second quarter")

    #     # parse documents
    #     # manager.parse_and_register_document("ZIM Reports Financial Results for the Second Quarter of 2022", "1")
    #     # manager.parse_and_register_document("Cielo Reports 2022 Annual Financial Results", "2")
    #     manager.parse_and_register_document("Tenet Second Quarter 2022 Financial Results in Line with Company Expectations with Revenue of $32.4M", "3")
    #     matches = manager.match()

if __name__ == '__main__':
    unittest.main()
