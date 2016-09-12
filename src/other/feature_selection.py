import os

bool_features = open("boolean_features.txt").readlines()
log = open("log_features.txt", "w")
good_features = open("good_features.txt", "w")

bool_feat_dic = {}

for feat in bool_features:
	bool_feat_dic[feat.strip()] = False


best_precision = 0
for feat in bool_feat_dic:
	base_prop = open("base.prop", "w")
	base_prop.write("""trainFile = models/hpo_train2.bilou
serializeTo = models/hpo_train2.ser.gz
map = word=0,answer=1

useClassFeature=true
useWord=true
maxNGramLeng=14
entitySubclassification = SBIEO
wordShape=chris2useLC""")
	bool_feat_dic[feat] = True
	for feat in bool_feat_dic:
		base_prop.write(feat + "=" + str(bool_feat_dic[feat]) + "\n")
	os.system("feature_selection.sh")
	res = open("/home/mlobo/IBEnt/data/...report.txt").readlines()[:6]
		precision = int(res[4].split("=")[1])
	if precision > best_precision:
		best_precision = precision
		good_features.write(feat)
	else:
		bool_feat_dic[feat] = False
	log.write(feat + " | " + str(precision))
	base_prop.close()

log.close()
good_features.close()