#!/usr/bin/env python
#===================================================================================
#description     : Methods for training graph exploration                          =
#author          : Shashi Narayan, shashi.narayan(at){ed.ac.uk,loria.fr,gmail.com})=                                    
#date            : Created in 2014, Later revised in April 2016.                   =
#version         : 0.1                                                             =
#===================================================================================

from nltk.metrics.distance import edit_distance

# Compare edit distance
def compare_edit_distance(operator,edit_dist_after_drop,  edit_dist_before_drop):
    if operator == "lt":
        if edit_dist_after_drop < edit_dist_before_drop:
            return True
        else:
            return False
    
    if operator == "lteq":
        if edit_dist_after_drop <= edit_dist_before_drop:
            return True
        else:
            return False

# Split Candidate: Common for all clsses
def process_split_candidate_for_split_common(split_candidate, simple_sentences, main_sent_dict, boxer_graph):
    if len(split_candidate) != len(simple_sentences):
        # Number of events is less than number of simple sentences
        return False, []

    else:
        # Calculate all parent and following subtrees
        parent_subgraph_nodeset_dict = boxer_graph.extract_parent_subgraph_nodeset_dict()
        #print "parent_subgraph_nodeset_dict : "+str(parent_subgraph_nodeset_dict)
            
        node_overlap_dict = {}
        for nodename in split_candidate:
            split_nodeset = parent_subgraph_nodeset_dict[nodename]
            subsentence = boxer_graph.extract_main_sentence(split_nodeset, main_sent_dict, [])
            subsentence_words_set = set(subsentence.split())
            
            overlap_data = []
            for index in range(len(simple_sentences)):
                simple_sent_words_set = set(simple_sentences[index].split())
                overlap_words_set = subsentence_words_set & simple_sent_words_set
                overlap_data.append((len(overlap_words_set), index))
            overlap_data.sort(reverse=True)

            node_overlap_dict[nodename] = overlap_data[0]
                
        # Check that every node has some overlap in their maximum overlap else fail
        overlap_maxvalues = [node_overlap_dict[node][0] for node in node_overlap_dict]
        if 0 in overlap_maxvalues:
            return False, []
        else:
            # check the mapping covers all simple sentences
            overlap_max_simple_indixes = [node_overlap_dict[node][1] for node in node_overlap_dict]
            if len(set(overlap_max_simple_indixes)) == len(simple_sentences):
                # Thats a valid split, attach unprocessed graph components
                node_subgraph_nodeset_dict, node_span_dict = boxer_graph.partition_drs_for_successful_candidate(split_candidate, parent_subgraph_nodeset_dict)

                results = []
                for nodename in split_candidate:
                    span = node_span_dict[nodename]
                    nodeset = node_subgraph_nodeset_dict[nodename][:]
                    simple_sentence = simple_sentences[node_overlap_dict[nodename][1]]
                    results.append((span, nodeset, nodename, simple_sentence))
                # Sort them based on starting
                results.sort()
                return True, results
            else:
                return False, []

# functions : Drop-REL Candidate
def process_rel_candidate_for_drop_overlap(relnode_candidate, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph, overlap_percentage):
    simple_sentence = " ".join(simple_sentences)
    simple_words = simple_sentence.split()

    rel_phrase = boxer_graph.extract_relation_phrase(relnode_candidate, nodeset, main_sent_dict, filtered_mod_pos)

    #print relnode_candidate, rel_phrase

    rel_words = rel_phrase.split()
    if len(rel_words) == 0:
        return True
    else:
        found = 0
        for word in rel_words:
            if word in simple_words:
                found += 1
        percentage_found = found/float(len(rel_words))

        if percentage_found <= overlap_percentage:
            return True
        else:
            return False

def process_rel_candidate_for_drop_led(relnode_candidate, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph, opr_drop_rel):
    simple_sentence = " ".join(simple_sentences)
    
    sentence_before_drop = boxer_graph.extract_main_sentence(nodeset, main_sent_dict, filtered_mod_pos)
    edit_dist_before_drop = edit_distance(sentence_before_drop.split(), simple_sentence.split())        
    
    temp_nodeset, temp_filtered_mod_pos = boxer_graph.drop_relation(nodeset, relnode_candidate, filtered_mod_pos)
    sentence_after_drop = boxer_graph.extract_main_sentence(temp_nodeset, main_sent_dict, temp_filtered_mod_pos)
    edit_dist_after_drop = edit_distance(sentence_after_drop.split(), simple_sentence.split())
    
    isDrop = compare_edit_distance(opr_drop_rel, edit_dist_after_drop, edit_dist_before_drop)
    return isDrop

# functions : Drop-MOD Candidate
def process_mod_candidate_for_drop_led(modcand_to_process, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph, opr_drop_mod):
    simple_sentence = " ".join(simple_sentences)
    
    sentence_before_drop = boxer_graph.extract_main_sentence(nodeset, main_sent_dict, filtered_mod_pos)
    edit_dist_before_drop = edit_distance(sentence_before_drop.split(), simple_sentence.split())
    
    modcand_position_to_process = modcand_to_process[0]
    temp_filtered_mod_pos = filtered_mod_pos[:]+[modcand_position_to_process]
    sentence_after_drop = boxer_graph.extract_main_sentence(nodeset, main_sent_dict, temp_filtered_mod_pos)
    edit_dist_after_drop = edit_distance(sentence_after_drop.split(), simple_sentence.split())
    
    isDrop = compare_edit_distance(opr_drop_mod, edit_dist_after_drop, edit_dist_before_drop)
    return isDrop

# functions : Drop-OOD Candidate
def process_ood_candidate_for_drop_led(oodnode_candidate, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph, opr_drop_ood):
    simple_sentence = " ".join(simple_sentences)
    
    sentence_before_drop = boxer_graph.extract_main_sentence(nodeset, main_sent_dict, filtered_mod_pos)
    edit_dist_before_drop = edit_distance(sentence_before_drop.split(), simple_sentence.split())
    
    temp_nodeset = nodeset[:]
    temp_nodeset.remove(oodnode_candidate)
    sentence_after_drop = boxer_graph.extract_main_sentence(temp_nodeset, main_sent_dict, filtered_mod_pos)
    edit_dist_after_drop = edit_distance(sentence_after_drop.split(), simple_sentence.split())

    isDrop = compare_edit_distance(opr_drop_ood, edit_dist_after_drop, edit_dist_before_drop)
    return isDrop

class Method_OVERLAP_LED:
    def __init__(self, overlap_percentage, opr_drop_mod, opr_drop_ood):
        self.overlap_percentage = overlap_percentage
        self.opr_drop_mod = opr_drop_mod
        self.opr_drop_ood = opr_drop_ood

    # Split candidate
    def process_split_candidate_for_split(self, split_candidate, simple_sentences, main_sent_dict, boxer_graph):
        isSplit, results = process_split_candidate_for_split_common(split_candidate, simple_sentences, main_sent_dict, boxer_graph)
        return isSplit, results    

    # Drop-REL Candidate
    def process_rel_candidate_for_drop(self, relnode_candidate, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph):
        isDrop = process_rel_candidate_for_drop_overlap(relnode_candidate, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph, self.overlap_percentage)
        return isDrop

    # Drop-MOD Candidate
    def process_mod_candidate_for_drop(self, modcand_to_process, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph):
        isDrop = process_mod_candidate_for_drop_led(modcand_to_process, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph, self.opr_drop_mod)
        return isDrop

    # Drop-OOD Candidate
    def process_ood_candidate_for_drop(self, oodnode_candidate, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph):
        isDrop = process_ood_candidate_for_drop_led(oodnode_candidate, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph, self.opr_drop_ood)
        return isDrop

class Method_LED:
    def __init__(self, opr_drop_rel, opr_drop_mod, opr_drop_ood):
        self.opr_drop_rel = opr_drop_rel
        self.opr_drop_mod = opr_drop_mod
        self.opr_drop_ood = opr_drop_ood

    # Split candidate
    def process_split_candidate_for_split(self, split_candidate, simple_sentences, main_sent_dict, boxer_graph):
        isSplit, results = process_split_candidate_for_split_common(split_candidate, simple_sentences, main_sent_dict, boxer_graph)
        return isSplit, results

    # Drop-REL Candidate
    def process_rel_candidate_for_drop(self, relnode_candidate, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph):
        isDrop = process_rel_candidate_for_drop_led(relnode_candidate, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph, self.opr_drop_rel)
        return isDrop

    # Drop-MOD Candidate
    def process_mod_candidate_for_drop(self, modcand_to_process, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph):
        isDrop = process_mod_candidate_for_drop_led(modcand_to_process, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph, self.opr_drop_mod)
        return isDrop

    # Drop-OOD Candidate
    def process_ood_candidate_for_drop(self, oodnode_candidate, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph):
        isDrop = process_ood_candidate_for_drop_led(oodnode_candidate, filtered_mod_pos, nodeset, simple_sentences, main_sent_dict, boxer_graph, self.opr_drop_ood)
        return isDrop
