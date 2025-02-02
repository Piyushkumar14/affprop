import numpy as np
import pandas as pd
import pytest
from affprop.Afprop_vec import afprop_vec


# sample data with clusters for testing
C1 = np.random.multivariate_normal(mean=[0, 0], cov=np.eye(2), size=30)
C2 = np.random.multivariate_normal(mean=[4, 4], cov=np.eye(2), size=30)
mydata = np.r_[C1, C2]


def test_n_cluster():
    # test n_cluster equals #unique cluster labels
    clusters, exemplars, cluster_plot, num_clusters, final_iter = afprop_vec(
        mydata=mydata
    )
    assert len(set(clusters)) == num_clusters
    assert num_clusters == 2


def test_cluster_pref():
    # test valid specification of cluster preference
    with pytest.raises(ValueError):
        afprop_vec(mydata=mydata, num_cluster_pref=0)


def test_valid_damping():
    # test valid specification of cluster preference
    with pytest.raises(ValueError):
        afprop_vec(mydata=mydata, damp_c=2)
