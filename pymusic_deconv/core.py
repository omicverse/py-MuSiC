"""MuSiC basic deconvolution; Xuran Wang et al., GPL-3 reference in manifest."""
import numpy as np
import pandas as pd
from scipy.optimize import nnls


def _matrix(x, name):
    if not isinstance(x, pd.DataFrame) or not x.index.is_unique or not x.columns.is_unique:
        raise ValueError(f'{name} must be a DataFrame with unique gene and sample/cell names.')
    v=x.to_numpy(dtype=float)
    if not min(v.shape) or not np.isfinite(v).all() or np.any(v<0):
        raise ValueError(f'{name} must be finite, nonempty and nonnegative.')
    return v


def music_basis(counts, clusters, samples, *, nonzero=True, markers=None, select_ct=None, cell_size=None):
    """Build a genes-by-cell-types reference from genes-by-cells counts.

    clusters and samples are Series indexed exactly like counts.columns.
    Library sizes use the full selected reference, before marker restriction.
    Missing donor/type groups are ignored; every retained type needs >=2 donors.
    Only the independent cell-type variance path (ct.cov=FALSE) is implemented.
    """
    _matrix(counts,'counts')
    for key,v in [('clusters',clusters),('samples',samples)]:
        if not isinstance(v,pd.Series) or not v.index.equals(counts.columns) or v.isna().any():
            raise ValueError(f'{key} must be nonmissing and indexed in cell order.')
    types=list(pd.unique(clusters)) if select_ct is None else list(select_ct)
    if len(set(types))!=len(types) or not set(types)<=set(clusters):
        raise ValueError('select_ct must contain unique existing cell types.')
    selected=clusters.isin(types)
    x=counts.loc[:,selected]
    if nonzero:x=x.loc[x.sum(axis=1)>0]
    donors=list(pd.unique(samples[selected]))
    theta=np.full((len(x),len(donors),len(types)),np.nan)
    sizes=np.full((len(donors),len(types)),np.nan)
    for j,t in enumerate(types):
        for i,d in enumerate(donors):
            cells=(clusters==t)&(samples==d)
            if not cells.any():continue
            totals=counts.loc[x.index,cells].sum(axis=1).to_numpy(dtype=float)
            if totals.sum()<=0:continue
            theta[:,i,j]=totals/totals.sum()
            sizes[i,j]=totals.sum()/cells.sum()
        if np.isfinite(sizes[:,j]).sum()<2:
            raise ValueError(f'Cell type {t!r} needs nonempty references from at least two donors.')
    means=np.nanmean(theta,axis=1);variance=np.nanvar(theta,axis=1,ddof=1)
    mean_size=np.nanmean(sizes,axis=0)
    if cell_size is not None:
        if not isinstance(cell_size,pd.Series) or not cell_size.index.is_unique or not set(types)<=set(cell_size.index):
            raise ValueError('cell_size must be a Series indexed by each selected cell type.')
        mean_size=cell_size.loc[types].to_numpy(dtype=float)
        if not np.isfinite(mean_size).all() or np.any(mean_size<=0):raise ValueError('cell_size must be positive.')
    genes=x.index if markers is None else pd.Index(markers).drop_duplicates().intersection(x.index,sort=False)
    if not len(genes):raise ValueError('No reference markers remain.')
    positions=x.index.get_indexer(genes)
    frame=lambda a:pd.DataFrame(a[positions],index=genes,columns=types)
    return {'design':frame(means*mean_size),'mean_relative':frame(means),'variance':frame(variance),
            'library_size':pd.DataFrame(sizes,index=donors,columns=types),
            'mean_size':pd.Series(mean_size,index=types)}


def _fit(y,design,size,variance,iter_max,nu,eps):
    # Default R music.iter multiplies relative bulk abundance by 100.
    y=y*100
    initial=nnls(design,y)[0]
    if initial.sum()<=0:raise ValueError('Reference cannot explain the bulk sample.')
    residual=y-design@initial
    def weighted(coef,res):
        weight=1/(nu+res**2+variance@((coef*size)**2))
        root=np.sqrt(weight)
        d=design*root[:,None]
        coef=nnls(d,y*root)[0]
        if coef.sum()<=0:raise ValueError('Weighted fit is empty.')
        return coef,y*root-d@coef,weight,d
    coef,residual,weight,d=weighted(initial,residual)
    prop=coef/coef.sum()
    converged=False
    for iteration in range(1,iter_max+1):
        new,res_new,weight,d=weighted(coef,residual)
        new_prop=new/new.sum()
        if np.abs(new_prop-prop).sum()<eps:
            coef=new;prop=new_prop;residual=res_new;converged=True;break
        coef=new;prop=new_prop;residual=res_new
    fit=design@coef
    variance_prop=np.diag(np.linalg.inv(d.T@d))*np.mean(residual**2)/(coef.sum()**2)
    r_squared=1-np.var(y-fit,ddof=1)/np.var(y,ddof=1)
    return prop,initial/initial.sum(),weight,r_squared,variance_prop,converged,iteration


def music_prop(bulk, reference, clusters, samples, *, markers=None, select_ct=None,
               cell_size=None, iter_max=1000, nu=.0001, eps=.01):
    """MuSiC proportions using multiple reference donors (ct.cov=FALSE).

    bulk and reference are genes-by-samples/cells DataFrames. Supports the
    default uncentered, unnormalized weighted NNLS path; no MuSiC2 or recursive
    tree deconvolution. Returned convergence flags must be checked by callers.
    """
    _matrix(bulk,'bulk');_matrix(reference,'reference')
    if isinstance(iter_max,bool) or not isinstance(iter_max,int) or iter_max<1:
        raise ValueError('iter_max must be positive.')
    if not np.isfinite([nu,eps]).all() or min(nu,eps)<=0:raise ValueError('nu and eps must be positive.')
    bulk=bulk.loc[bulk.mean(axis=1)!=0]
    chosen=bulk.index if markers is None else bulk.index.intersection(pd.Index(markers),sort=False)
    basis=music_basis(reference,clusters,samples,markers=chosen,select_ct=select_ct,cell_size=cell_size)
    genes=basis['design'].index.intersection(bulk.index,sort=False)
    minimum=min(len(bulk),len(reference)) if markers is None else len(markers)
    if len(genes)<.2*minimum:raise ValueError('Too few common genes.')
    design=basis['design'].loc[genes];types=design.columns
    if len(types)<2:raise ValueError('At least two cell types are required.')
    variance=basis['variance'].loc[genes].to_numpy()
    relative=bulk.loc[genes].to_numpy(dtype=float)
    if np.any(relative.sum(axis=0)<=0):raise ValueError('Each bulk sample needs positive common-gene counts.')
    relative/=relative.sum(axis=0)
    props=[];unweighted=[];weights=np.full(relative.shape,np.nan);rs=[];vars=[];diagnostics=[]
    for i in range(relative.shape[1]):
        keep=relative[:,i]!=0
        d=design.to_numpy()[keep]
        if len(d)<=len(types) or np.linalg.matrix_rank(d)<len(types):
            raise ValueError('Reference cell types are not identifiable on expressed bulk genes.')
        result=_fit(relative[keep,i],d,basis['mean_size'].to_numpy(),variance[keep],iter_max,nu,eps)
        prop,initial,weight,r2,var,converged,iterations=result
        props.append(prop);unweighted.append(initial);weights[keep,i]=weight;rs.append(r2);vars.append(var)
        diagnostics.append((converged,iterations))
    return {'proportions':pd.DataFrame(props,index=bulk.columns,columns=types),
            'nnls_proportions':pd.DataFrame(unweighted,index=bulk.columns,columns=types),
            'weights':pd.DataFrame(weights,index=genes,columns=bulk.columns),
            'r_squared':pd.Series(rs,index=bulk.columns),
            'proportion_variance':pd.DataFrame(vars,index=bulk.columns,columns=types),
            'diagnostics':pd.DataFrame(diagnostics,index=bulk.columns,columns=['converged','iterations'])}
