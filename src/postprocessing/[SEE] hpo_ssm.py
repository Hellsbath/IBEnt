#!/usr/bin/env python
from postprocessing.ssm import *
from postprocessing.hpo_resolution import find_hpo_term
from config.config import hpo_conn as dbhpo

hpo_measures = ["resnik_hpo", 'simui_hpo', 'simgic_hpo']

def resnik_hpo(id1, id2):
    cur = dbhpo.cursor()
    cur.execute("""SELECT MAX(i.info_content) 
        FROM graph_path p1, graph_path p2, SSM i 
        WHERE p1.term2_id = %s
        AND p2.term2_id = %s 
        AND p1.term1_id = p2.term1_id 
        AND p1.term1_id = i.term_id;""", (id1, id2))
    #r = cur.store_result()
    res = cur.fetchone()[0]
    #print id1, id2, res
    if res is None:
        res = '0'
    return float(res)

def simgic_hpo(id1, id2):
    cur = dbhpo.cursor()
    cur.execute("""SELECT ( 
            SELECT SUM(y.info_content)
            FROM  ( 
                SELECT DISTINCT f.term_id, f.info_content 
                FROM graph_path p1, graph_path p2, SSM f 
                WHERE p1.term2_id = %s
                AND p2.term2_id = %s 
                AND p1.term1_id=p2.term1_id 
                AND p1.term1_id=f.term_id)
            AS y )
         /( 
            SELECT SUM(x.info_content)   
            FROM (  
                SELECT f1.term_id, f1.info_content   
                FROM graph_path p1, SSM f1 
                WHERE p1.term2_id  = %s
                AND p1.term1_id = f1.term_id
                UNION  
                SELECT f2.term_id, f2.info_content   
                FROM graph_path p2, SSM f2
                WHERE p2.term2_id = %s
                AND p2.term1_id = f2.term_id) 
            AS x )""", (id1,id2,id1,id2))
    res = cur.fetchone()[0]
    if res is None:
        res = '0'
    return float(res)

def simui_hpo(id1, id2):
    cur = dbhpo.cursor()
    cur.execute("""SELECT ( 
            SELECT COUNT(y.info_content)
            FROM  ( 
                SELECT DISTINCT f.term_id, f.info_content 
                FROM graph_path p1, graph_path p2, SSM f 
                WHERE p1.term2_id = %s
                AND p2.term2_id = %s 
                AND p1.term1_id=p2.term1_id 
                AND p1.term1_id=f.term_id)
            AS y )
         /( 
            SELECT COUNT(x.info_content)   
            FROM (  
                SELECT f1.term_id, f1.info_content   
                FROM graph_path p1, SSM f1 
                WHERE p1.term2_id  = %s
                AND p1.term1_id = f1.term_id
                UNION  
                SELECT f2.term_id, f2.info_content   
                FROM graph_path p2, SSM f2
                WHERE p2.term2_id = %s 
                AND p2.term1_id = f2.term_id) 
            AS x )""", (id1,id2,id1,id2))
    res = cur.fetchone()[0]
    if res is None:
        res = '0'
    return float(res)

def get_ontology_id(entity, ontology):
    resid = None
    if ontology == "chebi":
        resid = entity.chebi_id
    elif ontology == "go":
        resid = entity.go_id
    elif ontology == "hpo":
        resid = entity.hpo_id   ###### HPO ########################
    return resid


def get_ssm(entities, measure, ontology="chebi", hindex=4):
    """

    :param entities: list of Entity objects relative to a sentence
    :param measure: semantic similarity measure
    :param ontology: (chebi)
    :param hindex: h-index threshold for some measures
    :return: return results with max SSM for each one
    AT LEAST 2 predictions with chebi
    """
    ssms = {} #{e1ID:{e2ID:ssm, e3ID:ssm}}

    if measure not in hpo_measures: ########### HPO ##########
        print 'measure not implement: ' + measure
        sys.exit()
    #check if chebi appears at least twice
    #nchebi = 0
    #for res in entities:
    #    if res.chebi_id != '0':
    #        nchebi += 1
    #if nchebi < 2:
    #    return entities

    #calculate SSM between each valid chebiID
    for i1, res1 in enumerate(entities):
        ssms[i1] = {}
        res1id = get_ontology_id(res1, ontology)
        if res1id != '0' and res1id is not None:
            for i2, res2 in enumerate(entities):
                res2id = get_ontology_id(res2, ontology)
                if res1id != res2id and res2id != '0' and res2id is not None: #skip entities with no mapping and same chebiID
                    if measure == "simui_hindex" or measure == "simgic_hindex":
                        ssm = eval('{0}("{1}", "{2}", h={3})'.format(measure, res1id, res2id, str(hindex)))
                    else:
                        ssm = eval('{0}("{1}", "{2}")'.format(measure, res1id, res2id))
                    ssms[i1][i2] = ssm
    #get max ssm for each chebiID
    for i1, res1 in enumerate(entities):
        res1id = get_ontology_id(res1, ontology)
        res1.ssm_score = 0
        if res1id != '0' and len(ssms[i1]) > 0:
            v = list(ssms[i1].values())
            k = list(ssms[i1].keys())
            max_ssm = (k[v.index(max(v))], max(v)) # bestEID, bestSSM
            res1.ssm_best_ID = get_ontology_id(entities[max_ssm[0]], ontology)
            if ontology == "chebi":
                res1.ssm_best_name = entities[max_ssm[0]].chebi_name
            elif ontology == "go":
                res1.ssm_best_name = entities[max_ssm[0]].go_name
            elif ontology == "hpo":
                res1.ssm_best_name = entities[max_ssm[0]].hpo_name #################3 HPO ##################
            res1.ssm_best_text = entities[max_ssm[0]].text
            #res1.ssm_score = max_ssm[1]
            res1.ssm_score = max_ssm[1]
        else:
            res1.ssm_best_ID = "0"
            res1.ssm_best_name = ""
            res1.ssm_best_text = ""
            if len(entities) == 1 and res1id != '0':
                if ontology == "chebi":
                    res1.ssm_score = 1
                elif ontology == "go":
                    res1.ssm_score = 1
                elif ontology == "hpo": #################3 HPO #################
                    res1.ssm_score = 1
        entities[i1] = res1
    return entities


def firstCommonIC(c1, c2):
    #return the IC of the first common term between two ChEBI terms
    pass


def termsInCommon(id1, id2):
    cur = dbhpo.cursor()
    cur.execute("""SELECT COUNT(i.info_content) 
		FROM graph_path p1, graph_path p2, SSM i 
		WHERE p1.term2_id = %s
		AND p2.term2_id = %s 
		AND p1.term1_id = p2.term1_id 
		AND p1.term1_id = i.term_id;""", (id1, id2))
    res = cur.fetchone()[0]
    if res is None:
        res = '0'
    return int(res)


def harmonicmeanIC(id1, id2):
    if id1 == 0 or id2 == 0:
        return 0
    cur = dbhpo.cursor()
    cur.execute("""SELECT f.info_content 
				FROM SSM f 
				WHERE f.term_id = %s""", (id1,))
    ic1 = float(cur.fetchone()[0])
    cur = dbhpo.cursor()
    cur.execute("""SELECT f.info_content 
				FROM SSM f 
				WHERE f.term_id = %s""", (id2,))
    ic2 = float(cur.fetchone()[0])
    if ic2 == 0 or ic2 == 0:
        return 0
    return (2*ic1*ic2)/(ic1+ic2)


def main():
    ''' input: measure id1 id2 OR measure term1 term2 (performs chebi resolution)'''
    parser = OptionParser(usage='measure SSM between two ChEBI entities. default is all measures between water and ethanol')
    parser.add_option("-f", "--file", dest="file",  action="store", default="ssm",
                      help="Pickle file to load/store the data")
    parser.add_option("-d", "--dir", action="store", dest="dir", type = "string", default=".",
                      help="Corpus directory with chebi mappings to measure SSM between pairs (CHEMDNER format)")
    parser.add_option("--reload", action="store_true", default=False, dest="reload",
                      help="Reload pickle data")
    parser.add_option("--log", action="store", dest="loglevel", type = "string", default = "WARNING",
                      help="Log level")
    parser.add_option("--logfile", action="store", dest="logfile", type = "string", default = "kernel.log",
                      help="Log file")
    parser.add_option("--chebi1", action="store", dest="c1", type = "string", default="15377",
                      help="ChEBI ID of the first entity")
    parser.add_option("--chebi2", action="store", dest="c2", type = "string", default="16236",
                      help="ChEBI ID of the second entity")
    parser.add_option("--ssmtype", action="store", dest="ssm", type = "string", default="all",
                      help="SSM to use, or all")
    parser.add_option("--action", action="store", dest="action", type = "string", default="measure",
                      help="measure, batch")
    (options, args) = parser.parse_args()
    numeric_level = getattr(logging, options.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % options.loglevel)

    while len(logging.root.handlers) > 0:
        logging.root.removeHandler(logging.root.handlers[-1])
    logging.basicConfig(level=numeric_level, format='%(asctime)s %(levelname)s %(message)s')

    if options.file + '_' + options.action + '.pickle' in os.listdir(os.getcwd()) and not options.reload:
        print "loading data pickle", options.file + '_' + options.action + '.pickle'
        data = pickle.load(open(options.file + '_' + options.action + '.pickle', 'rb'))
    else:
        data = {}

    measure = options.ssm


    id1 = options.c1
    id2 = options.c2
    if options.action == "measure":
        if measure == 'all':
            for m in measures:
                print m, eval(m + '("' + id1 + '", "' + id2 + '")')
        elif measure not in measures and measure not in go_measures and measure not in hpo_measures: ######### HPO ###########
            print 'measure not implement: ' + measure
            sys.exit()
        else:
            print measure, id1, id2
            expr = measure + '("' + id1 + '", "' + id2 + '")'
            print expr
            print eval(expr)

if __name__ == "__main__":
    main()
