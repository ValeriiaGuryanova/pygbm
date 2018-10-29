from sklearn.model_selection import train_test_split
import numpy as np
import pytest

from pygbm import GradientBoostingMachine
from pygbm.binning import BinMapper


@pytest.mark.parametrize('seed', [1, 3, 4, 5])
@pytest.mark.parametrize('n_samples', [255, 3000])
def test_same_predictions_easy_target(seed, n_samples):
    # Make sure pygbm has the same predictions as LGBM for very easy targets.
    #
    # Notes:
    # - As some splits maye have equal gains (and because of float errors) when
    #   the number of samples in a node is low, it makes more sense to compare
    #   the predictions rather than the trees which may be split in different
    #   features just out of luck.
    # - To avoid discrepancies in the binning strategy, data is pre-binned if
    #   n_samples > 255.

    lb = pytest.importorskip("lightgbm")

    rng = np.random.RandomState(seed=seed)
    n_samples = n_samples
    min_sample_leaf = 1
    max_leaf_nodes = 6
    max_iter = 1

    # data = linear target, 5 features, 3 irrelevant.
    X = rng.normal(size=(n_samples, 5))
    y = X[:, 0] - X[:, 1]
    if n_samples > 255:
        X = BinMapper().fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=rng)

    est_lightgbm = lb.LGBMRegressor(n_estimators=max_iter,
                                    min_data=1, min_data_in_bin=1,
                                    learning_rate=1,
                                    min_child_samples=min_sample_leaf,
                                    num_leaves=max_leaf_nodes)
    est_pygbm = GradientBoostingMachine(max_iter=max_iter,
                                        validation_split=None, scoring=None,
                                        min_samples_leaf=min_sample_leaf,
                                        max_leaf_nodes=max_leaf_nodes)
    est_lightgbm.fit(X_train, y_train)
    est_pygbm.fit(X_train, y_train)

    for data in (X_test, X_train):
        pred_lgbm = est_lightgbm.predict(data)
        pred_pygbm = est_pygbm.predict(data)
        np.testing.assert_array_almost_equal(pred_lgbm, pred_pygbm, decimal=5)
