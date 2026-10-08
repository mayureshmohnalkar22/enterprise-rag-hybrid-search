"""V4 regressions derived from observed NIST RMF testing."""
import json
from pathlib import Path
from rag.list_checks import audit_list
from rag.verification import verify


def test_nist_complete_seven():
    data=json.loads(Path('data/eval/nist_regressions.json').read_text())
    assert audit_list(data['cases'][0]['answer'], data['reference_items'])['complete']


def test_nist_split_and_omission_detected():
    data=json.loads(Path('data/eval/nist_regressions.json').read_text())
    result=audit_list(data['cases'][1]['answer'], data['reference_items'])
    assert not result['complete']
    assert 'Secure and Resilient' in result['missing']
    assert 'Privacy-Enhanced' in result['missing']


def test_cited_complete_list_overlap_not_zero():
    text='The seven traits are Valid and Reliable; Safe; Secure and Resilient; Accountable and Transparent; Explainable and Interpretable; Privacy-Enhanced; Fair with Harmful Bias Managed.'
    answer='According to [1] the seven traits are:\n1. Valid and Reliable\n2. Safe\n3. Secure and Resilient\n4. Accountable and Transparent\n5. Explainable and Interpretable\n6. Privacy-Enhanced\n7. Fair with Harmful Bias Managed'
    result=verify(answer,[{'citation':'[1]','text':text}])
    assert result['citation_coverage']==1
    assert result['mean_lexical_overlap'] >= .8
    assert result['lexical_support_rate']==1


def test_citation_coverage_can_be_high_while_list_incomplete():
    data=json.loads(Path('data/eval/nist_regressions.json').read_text())
    answer='The list is [1]:\n'+'\n'.join(f'{i}. {line}' for i,line in enumerate(data['cases'][1]['answer'].splitlines(),1))
    ver=verify(answer,[{'citation':'[1]','text':data['cases'][0]['answer']}])
    assert ver['citation_coverage']==1
    assert not audit_list(answer,data['reference_items'])['complete']


def test_contradictory_abstention_warning():
    answer="I don't have the information to list seven characteristics.\nValid and Reliable\nSafe\nSecure and Resilient\nPrivacy-Enhanced"
    result=verify(answer,[{'citation':'[1]','text':'Safe and reliable AI'}])
    assert result['warnings']


def test_numeric_mismatch_remains_flagged():
    result=verify('Retention is 60 days [1].',[{'citation':'[1]','text':'Retention is 30 days.'}])
    assert result['claims'][0]['number_mismatch']


def test_invalid_id_not_counted_as_covered():
    result=verify('Valid and reliable [99].',[{'citation':'[1]','text':'Valid and reliable'}])
    assert result['citation_coverage']==0
    assert result['invalid_citations']==['[99]']
