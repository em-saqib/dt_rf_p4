# -*- coding: utf-8 -*-
# **Generate Table entries from RFC for P4**
# Note: change the range as per number of ports. First change the ports range of: for qsfp_cage in [1, 2] if there is two ports named 1 and 2. Then define this rnages for voting tables as:     for i in range(1,3): for j in range(1,3): for k in range(1,3):
# Also change the features aocrding to input names.
# Also change the object of model name

import os
import sys
import pickle as pickle
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
from sklearn import tree
import re
from statistics import mode
import random

np.random.seed(42)

clf = pd.read_pickle('rfc.pkl') #replace with trained model.sav from notebooks

## list the feature names
feature_names = clf.feature_names_in_
print(feature_names)

## gets all splits and conditions
def get_splits(forest, feature_names):
    data = []
    #generate dataframe with all thresholds and features
    for t in range(len(forest.estimators_)):
        clf = forest[t]
        n_nodes = clf.tree_.node_count
        features  = [feature_names[i] for i in clf.tree_.feature]
        for i in range(0, n_nodes):
            node_id = i
            left_child_id = clf.tree_.children_left[i]
            right_child_id = clf.tree_.children_right[i]
            threshold = clf.tree_.threshold[i]
            feature = features[i]
            if threshold != -2.0:
                data.append([t, node_id, left_child_id,
                             right_child_id, threshold, feature])
    data = pd.DataFrame(data)
    data.columns = ["Tree","NodeID","LeftID","RightID","Threshold","Feature"]
    return data

## gets the feature table of each feature from the splits
def get_feature_table(splits_data, feature_name):
    feature_data = splits_data[splits_data["Feature"]==feature_name]
    feature_data = feature_data.sort_values(by="Threshold")
    feature_data = feature_data.reset_index(drop=True)
    ##
    # feature_data["Threshold"] = (feature_data["Threshold"]).astype(int)
    feature_data["Threshold"] = feature_data["Threshold"].astype(int)
    ##
    code_table = pd.DataFrame()
    code_table["Threshold"] = feature_data["Threshold"]
    #print(feature_data)
    #create a column for each split in each tree
    for tree_id, node in zip(list(feature_data["Tree"]), list(feature_data["NodeID"])):
        colname = "s"+str(tree_id)+"_"+str(node)
        code_table[colname] = np.where((code_table["Threshold"] <=
                                        feature_data[(feature_data["NodeID"]== node) &
                                                     (feature_data["Tree"]==tree_id)]["Threshold"].values[0]), 0, 1)
    #add a row to represent the values above the largest threshold
    temp = [max(code_table["Threshold"])+1]
    temp.extend(list([1]*(len(code_table.columns)-1)))
    code_table.loc[len(code_table)] = temp
    code_table = code_table.drop_duplicates(subset=['Threshold'])
    code_table = code_table.reset_index(drop=True)
    return code_table

## get feature tables with ranges and codes only
def get_feature_codes_with_ranges(feature_table, num_of_trees):
    Codes = pd.DataFrame()
    for tree_id in range(num_of_trees):
        colname = "code"+str(tree_id)
        Codes[colname] = feature_table[feature_table[[col for col in feature_table.columns if ('s'+str(tree_id)+'_') in col]].columns[0:]].apply(lambda x: ''.join(x.dropna().astype(str)),axis=1)
        Codes[colname] = ["0b" + x for x in Codes[colname]]
    feature_table["Range"] = [0]*len(feature_table)
    feature_table["Range"].loc[0] = "0,"+str(feature_table["Threshold"].loc[0])
    for i in range(1, len(feature_table)):
        if (i==(len(feature_table))-1):
            feature_table["Range"].loc[i] = str(feature_table["Threshold"].loc[i])+","+str(feature_table["Threshold"].loc[i])
        else:
            feature_table["Range"].loc[i] = str(feature_table["Threshold"].loc[i-1]+1) + ","+str(feature_table["Threshold"].loc[i])
    Ranges = feature_table["Range"]
    return Ranges, Codes

## get list of splits crossed to get to leaves
def retrieve_branches(estimator):
    number_nodes = estimator.tree_.node_count
    children_left_list = estimator.tree_.children_left
    children_right_list = estimator.tree_.children_right
    feature = estimator.tree_.feature
    threshold = estimator.tree_.threshold
    # Calculate if a node is a leaf
    is_leaves_list = [(False if cl != cr else True) for cl, cr in zip(children_left_list, children_right_list)]
    # Store the branches paths
    paths = []
    for i in range(number_nodes):
        if is_leaves_list[i]:
            # Search leaf node in previous paths
            end_node = [path[-1] for path in paths]
            # If it is a leave node yield the path
            if i in end_node:
                output = paths.pop(np.argwhere(i == np.array(end_node))[0][0])
                yield output
        else:
            # Origin and end nodes
            origin, end_l, end_r = i, children_left_list[i], children_right_list[i]
            # Iterate over previous paths to add nodes
            for index, path in enumerate(paths):
                if origin == path[-1]:
                    paths[index] = path + [end_l]
                    paths.append(path + [end_r])
            # Initialize path in first iteration
            if i == 0:
                paths.append([i, children_left_list[i]])
                paths.append([i, children_right_list[i]])

## get classes and certainties
def get_classes(clf):
    leaves = []
    classes = []
    certainties = []
    for branch in list(retrieve_branches(clf)):
        leaves.append(branch[-1])
    for leaf in leaves:
        if clf.tree_.n_outputs == 1:
            value = clf.tree_.value[leaf][0]
        else:
            value = clf.tree_.value[leaf].T[0]
        class_name = np.argmax(value)
        certainty = int(round(max(value)/sum(value),2)*100)
        classes.append(class_name)
        certainties.append(certainty)
    return classes, certainties

## get the codes corresponging to the branches followed
def get_leaf_paths(clf):
    depth = clf.max_depth
    branch_codes = []
    for branch in list(retrieve_branches(clf)):
        code = [0]*len(branch)
        for i in range(1, len(branch)):
            if (branch[i]==clf.tree_.children_left[branch[i-1]]):
                code[i] = 0
            elif (branch[i]==clf.tree_.children_right[branch[i-1]]):
                code[i] = 1
        branch_codes.append(list(code[1:]))
    return branch_codes

## get the order of the splits to enable code generation
def get_order_of_splits(data, feature_names):
    splits_order = []
    for feature_name in feature_names:
        feature_data = data[data.iloc[:,4]==feature_name]
        feature_data = feature_data.sort_values(by="Threshold")
        for node in list(feature_data.iloc[:,0]):
            splits_order.append(node)
    return splits_order

def get_splits_per_tree(clf, feature_names):
    data = []
    n_nodes = clf.tree_.node_count
    #set feature names
    features  = [feature_names[i] for i in clf.tree_.feature]
    #generate dataframe with all thresholds and features
    for i in range(0,n_nodes):
        node_id = i
        left_child_id = clf.tree_.children_left[i]
        right_child_id = clf.tree_.children_right[i]
        threshold = clf.tree_.threshold[i]
        feature = features[i]
        if threshold != -2.0:
            data.append([node_id, left_child_id,
                         right_child_id, threshold, feature])
    data = pd.DataFrame(data)
    data.columns = ["NodeID","LeftID","RightID","Threshold","Feature"]
    return data

## Get codes and masks
def get_codes_and_masks(clf, feature_names):
    splits = get_order_of_splits(get_splits_per_tree(clf, feature_names), feature_names)
    depth = clf.max_depth
    codes = []
    masks = []
    for branch, coded in zip(list(retrieve_branches(clf)), get_leaf_paths(clf)):
        code = [0]*len(splits)
        mask = [0]*len(splits)
        for index, split in enumerate(splits):
            if split in branch:
                mask[index] = 1
        masks.append(mask)
        codes.append(code)
    masks = pd.DataFrame(masks)
    masks['Mask'] = masks[masks.columns[0:]].apply(lambda x: ''.join(x.dropna().astype(str)),axis=1)
    masks = ["0b" + x for x in masks['Mask']]
    indices = range(0,len(splits))
    temp = pd.DataFrame(columns=["split", "index"],dtype=object)
    temp["split"] = splits
    temp["index"] = indices
    final_codes = []
    for branch, code, coded in zip(list(retrieve_branches(clf)), codes, get_leaf_paths(clf)):
        indices_to_use = temp[temp["split"].isin(branch)].sort_values(by="split")["index"]
        for i, j in zip(range(0,len(coded)), list(indices_to_use)):
            code[j] = coded[i]
        final_codes.append(code)
    final_codes = pd.DataFrame(final_codes)
    final_codes["Code"] = final_codes[final_codes.columns[0:]].apply(lambda x: ''.join(x.dropna().astype(str)),axis=1)
    final_codes = ["0b" + x for x in final_codes["Code"]]
    return final_codes, masks
## End of model manipulation ##


# Get table entries and generate file with table entries
with open("rules.cmd", "w") as entries_file: # file to save entries in

    print("table_clear tbl_f0", file=entries_file)
    print("table_clear tbl_f1", file=entries_file)
    print("table_clear tbl_cw0", file=entries_file)
    print("table_clear tbl_cw1", file=entries_file)
    print("table_clear tbl_cw2", file=entries_file)
    print("table_clear voting_table", file=entries_file)

    # Get entries for feature tables
    tree_code0 = []
    tree_code1 = []
    tree_code2 = []

    for fea in range(0,len(feature_names)):
        Ranges, Codes = get_feature_codes_with_ranges(get_feature_table(get_splits(clf, feature_names), feature_names[fea]), len(clf.estimators_))
        for ran, cods0, cods1, cods2 in zip(Ranges, Codes.iloc[:,0], Codes.iloc[:,1], Codes.iloc[:,2]):
            pref = 'table_add'
            tbl_name = "tbl_f" + str(fea)
            acc_name = "SetCode_f"+ str(fea)
            if(ran == Ranges[len(Ranges)-1]):
                print(pref + " " + tbl_name + " " + acc_name + " " + str(ran.split(",")[0]) + "->" + str(65535) + " => " + cods0 + " " + cods1 + " " + cods2 + " 1", file=entries_file)
            else:
                print(pref + " " + tbl_name + " " + acc_name + " " + str(ran.split(",")[0]) + "->" + str(ran.split(",")[1]) + " => " + cods0 + " " + cods1 + " " + cods2 + " 1", file=entries_file)

        tree_code0.append(len(cods0)-2)
        tree_code1.append(len(cods1)-2)
        tree_code2.append(len(cods2)-2)

        #print('', file=entries_file)
    tree_code_sizes = [tree_code0, tree_code1, tree_code2]
    print(tree_code_sizes)

    # Generate code tables
    for tree_id in range(0, len(clf.estimators_)):
        Final_Codes, Final_Masks = get_codes_and_masks(clf.estimators_[tree_id], feature_names)
        Classe, Certain = get_classes(clf.estimators_[tree_id])
        pref = 'table_add'
        code_tbl_name = "tbl_cw"+str(tree_id)
        acc_name = "SetClass_t"+str(tree_id)
        for cod, mas, cla, cer in zip(Final_Codes, Final_Masks, Classe, Certain):
            print(pref + " " + code_tbl_name + " " + acc_name + " " + cod + "&&&" + mas + " => " + str(cla+2) + " " + str(cer) + " " + str(1), file=entries_file)

    # Get voting table entries
    for i in range(2,4):
        for j in range(2,4):
            for k in range(2,4):
                if ((i!=j) & (j!=k) & (i!=k)):

                    print("table_add voting_table set_final_class" + " " + str(i)  + " " + str(j)  + " " + str(k) + " => " +str(np.random.choice([i, j, k])), file=entries_file)
                else:
                    print("table_add voting_table set_final_class" + " " + str(i)  + " " + str(j)  + " " + str(k) + " => " +str(mode([i, j, k])), file=entries_file)