"""
Derives the necessary metadata, given a CSVW metadata file, to enable an RDF 
data cube to successfully be uploaded to the PMD platform.
"""

from urllib.parse import urlparse
from rdflib import Dataset, Graph, Literal, URIRef
from rdflib.namespace import DCAT, DCTERMS, FOAF, Namespace, RDF, RDFS
from rdflib.plugin import register, Parser
register('json-ld', Parser, 'rdflib_jsonld.parser', 'JsonLDParser')

QB = Namespace('http://purl.org/linked-data/cube#')
PMD = Namespace('http://publishmydata.com/def/dataset#')
PMDCAT = Namespace('http://publishmydata.com/pmdcat#')
VCARD = Namespace('http://www.w3.org/2006/vcard/ns#')


class PMDMetadata():

    @staticmethod
    def from_csvw(metadata_filepath):

        pmd_metadata = Dataset()

        with open(metadata_filepath) as file:
            json_string = file.read()
            g = Graph().parse(data=json_string, format='json-ld')

        # Get all datacubes.
        datacubes = g.query(
            """
            PREFIX dcat: <http://www.w3.org/ns/dcat#>
            SELECT *
            WHERE {
                ?dataset a dcat:Dataset .
            }
            """
        )

        for datacube in datacubes:
            # Try and find a sensible id for each dcat:Dataset specifed in the
            # metadata file to derive additional URIs for PMD resources
            datacube_uri = datacube[0]
            datacube_id = urlparse(datacube_uri).path.rsplit('/', 1)[-1]

            # Create sensible URIs for PMD specific resources
            catalog_uri = "http://gss-data.org.uk/catalog/datasets"
            graph_uri = f"http://gss-data.org.uk/graph/{datacube_id}"
            metadata_graph_uri = f"http://gss-data.org.uk/graph/{datacube_id}#metadata"
            catalog_record_uri = f"http://gss-data.org.uk/catalog/{datacube_id}"
            dataset_uri = f"http://gss-data.org.uk/data/{datacube_id}"

            metadata = Graph('IOMemory', URIRef(metadata_graph_uri))
            metadata.bind('dcat', DCAT)
            metadata.bind('dct', DCTERMS)
            metadata.bind('foaf', FOAF)
            metadata.bind('qb', QB)
            metadata.bind('pmdcat', PMDCAT)
            metadata.bind('rdf', RDF)
            metadata.bind('rdfs', RDFS)
            metadata.bind('vcard', VCARD)

            graph = URIRef(graph_uri)
            metadata_graph = URIRef(metadata_graph_uri)
            catalog = URIRef(catalog_uri)
            catalog_record = URIRef(catalog_record_uri)
            dataset = URIRef(dataset_uri)
            datacube = URIRef(datacube_uri)

            triples = [
                # Metadata required by PMD: ------------------------------------
                (catalog,         RDF.type,                DCAT.Catalog),
                (catalog,         DCAT.record,             catalog_record),
                (catalog_record,  RDF.type,                DCAT.CatalogRecord),
                (catalog_record,  FOAF.primaryTopic,       dataset),
                (catalog_record,  PMDCAT.metadataGraph,    metadata_graph),
                (dataset,         RDF.type,                PMDCAT.Dataset),
                (dataset,         PMDCAT.datasetContents,  datacube),
                (dataset,         PMDCAT.graph,            graph),
                (datacube,        RDF.type,                PMDCAT.DataCube)
            ]

            # Get metadata attached to a datacube-like object and assign it
            # to the dcat:Dataset catalog entry.
            user_defined_metadata = g.query(
                """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX csvw: <http://www.w3.org/ns/csvw#>
                PREFIX qb: <http://purl.org/linked-data/cube#>
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
                SELECT ?dataset ?p ?o
                WHERE {
                    {
                        ?datacube ?p ?o .
                        FILTER (?p NOT IN (
                            rdf:type, qb:structure, csvw:tableSchema, csvw:url
                        )) .
                    }
                }
                """,
                initBindings={
                    "dataset": dataset,
                    "datacube": datacube
                }
            )

            contact_metadata = g.query("""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
                SELECT ?contact ?p ?o
                WHERE {
                    {
                        ?datacube ?p0 ?contact .
                        ?contact a vcard:Individual .
                        ?contact ?p ?o .
                    }
                }
                """,
                initBindings={
                    "datacube": datacube
                }
            )

            triples.extend(list(user_defined_metadata))
            triples.extend(list(contact_metadata))

            for triple in triples:
                if triple[2] is not None:
                    metadata.add(triple)

            pmd_metadata.add_graph(metadata)

        pmd_metadata.serialize(
            metadata_filepath.replace(".csv-metadata.json", ".trig"),
            format="trig"
        )
