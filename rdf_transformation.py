import pandas as pd
import geocoder
from rdflib import Graph,URIRef, BNode, Literal
from rdflib.namespace import Namespace, NamespaceManager

def to_3NF_df(df):
    arr_3nf = [] 
    col_names = list(df.columns.values)
    for index, row in df.iterrows():
        res_country = row[-2]
        orig_country = row[-1]
        pop_type = row[2].replace(' ', '_') # no whitespace in URI
        if res_country != res_country or orig_country != orig_country:
            continue # missing information
        for idx in range(3,len(row)-2):
            if row[idx] == row[idx] and row[idx] != "*": # nan check
                arr_3nf.append([res_country, orig_country, pop_type, int(col_names[idx]), row[idx]])
                
    return pd.DataFrame(data = arr_3nf, columns = col_names[-2:] + [col_names[2],'Year','Count'])

	
def get_geonames_id(country_name):
    if not country_name in country_map:
        geonames_id = geocoder.geonames(country_name, key='freecraver').geonames_id
        country_map[country_name] = geonames_id
    return country_map[country_name]

	
def write_to_turtle_rdf(df, output_file):
    g = Graph()
    namespace_manager = NamespaceManager(Graph())
    n_geo = Namespace("http://sws.geonames.org/")
    n_custom_ont = Namespace("http://vocab.informatik.tuwien.ac.at/VU184.729-2018/e01429253/ontology/")
    n_custom_cls = Namespace("http://vocab.informatik.tuwien.ac.at/VU184.729-2018/e01429253/class/")
    n_time = Namespace("http://www.w3.org/2006/time/")

    namespace_manager.bind('tuwo', n_custom_ont, override=False)
    namespace_manager.bind('tuwc', n_custom_cls, override=False)
    namespace_manager.bind('gn', n_geo, override=False)
    namespace_manager.bind('time', n_time, override=False)
    g.namespace_manager = namespace_manager
    
    # define properties
    movement_property = n_custom_ont['populationMovement']
    orig_country_property = n_custom_ont['countryOfOrigin']
    pop_type_property = n_custom_ont['populationType']
    year_property = n_time['year']
    pop_amount_property = n_custom_ont['peopleAmount']
    
    # add nodes to the graph
    for index, row in df.iterrows():
        # blank node for connection
        relation_node = BNode() # a GUID is generated
        
        # base triple (residence_country, movement, blank_node)
        g.add( (n_geo[str(int(row[0]))], movement_property, relation_node) )
        
        # child properties
        g.add( (relation_node, orig_country_property, n_geo[str(int(row[1]))]) )
        g.add( (relation_node, pop_type_property, n_custom_cls[row[2]]) )
        g.add( (relation_node, year_property, Literal(int(row[3]))) )
        g.add( (relation_node, pop_amount_property, Literal(int(row[4]))) )

    # write to output file
    g.serialize(destination=output_file, format='turtle')
	
dataset_path = "dataset.csv"
output_file = "e01429253.ttl"
country_map = dict()
df = pd.read_csv(dataset_path, skiprows=5)
df['RES_ID'] = df.iloc[:,0].apply(get_geonames_id)
df['ORIG_ID'] = df.iloc[:, 1].apply(get_geonames_id)
df_3nf =to_3NF_df(df)
write_to_turtle_rdf(df_3nf, output_file)