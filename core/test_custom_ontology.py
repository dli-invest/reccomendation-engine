import holmes_extractor as holmes
import unittest

# ontology = holmes.Ontology("core/holmes.owl")
# ontology = holmes.Ontology("company_headlines.owl")
manager = holmes.Manager("en_core_web_trf", ontology=ontology, number_of_workers=1)

# Register search phrase
manager.register_search_phrase("An ENTITYORG takes over an ENTITYORG")

# Parse documents
manager.parse_and_register_document("Royal Bank of Scotland announces it intends to acquire Brewin Dolphin", "1")
manager.parse_and_register_document("Chipmaker MaxLinear Inc announced on Thursday it will buy Silicon Motion Technology Corp for nearly $4 billion.", "2")
manager.parse_and_register_document("Last month, cybersecurity company Mandiant was purchased by Alphabet", "3")
manager.parse_and_register_document("The Datto takeover by Kaseya", "4")

# Perform matching
matches = manager.match()

# Check all documents matched
print(len(matches))
# -> 4

# Extract companies doing the taking over
print([match['word_matches'][0]['document_phrase'] for match in matches])
# -> ['Royal Bank', 'Chipmaker MaxLinear Inc', 'Alphabet', 'Kaseya']

# Extract companies being taken over
print([match['word_matches'][2]['document_phrase'] for match in matches])
