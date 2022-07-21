import holmes_extractor as holmes
manager = holmes.Manager("en_core_web_trf", number_of_workers=1)
manager.register_search_phrase("An ENTITYPERSON visits an ENTITYGPE")
manager.parse_and_register_document("Richard Hudson visited Berlin")
print(manager.match())
# python3 -m spacy download en_core_web_trf
# python3 -m spacy download en_core_web_lg
# python3 -m coreferee install en