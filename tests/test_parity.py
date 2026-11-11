from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from pymusic_deconv import music_basis,music_prop
DATA=Path(__file__).parents[1]/'data'
def load():
    return (pd.read_csv(DATA/'reference.csv',index_col=0),pd.read_csv(DATA/'bulk.csv',index_col=0),
            pd.read_csv(DATA/'metadata.csv',index_col=0))
def test_basis():
    x,bulk,meta=load();out=music_basis(x,meta.ct,meta.donor)
    for key in ['design','variance','library_size']:
        expected=pd.read_csv(DATA/f'{key}.csv',index_col=0)
        np.testing.assert_allclose(out[key],expected,atol=1e-8,rtol=1e-8)
@pytest.mark.parametrize('mode',['default','markers'])
def test_proportions(mode):
    x,bulk,meta=load();before=x.copy(deep=True)
    out=music_prop(bulk,x,meta.ct,meta.donor,markers=x.index[:80] if mode=='markers' else None)
    mapping={'proportions':'Est.prop.weighted','nnls_proportions':'Est.prop.allgene',
             'weights':'Weight.gene','proportion_variance':'Var.prop','r_squared':'r.squared.full'}
    for key,rkey in mapping.items():
        expected=pd.read_csv(DATA/f'{mode}_{rkey}.csv',index_col=0)
        actual=np.asarray(out[key])
        np.testing.assert_allclose(actual.ravel(),expected.to_numpy().ravel(),atol=1e-8,rtol=1e-8,equal_nan=True)
    np.testing.assert_allclose(out['proportions'].sum(axis=1),1)
    assert out['diagnostics'].converged.all()
    pd.testing.assert_frame_equal(x,before)
def test_invalid_labels_and_identifiability():
    x,bulk,meta=load()
    with pytest.raises(ValueError,match='cell order'): music_basis(x,meta.ct.iloc[::-1],meta.donor)
    with pytest.raises(ValueError,match='two donors'): music_basis(x,meta.ct,pd.Series('one',index=x.columns))
