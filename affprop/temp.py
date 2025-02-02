import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
import logging

def calc_similarity_matrix(mydata, num_cluster_pref=1):
    """
    Function to calculate the similarity matrix for affinity propagation clustering
    :param mydata: numpy array of data points
    :param num_cluster_pref: int, default 1, number of cluster preferences to use
    :return: numpy array, similarity matrix
    """
    neg_euc_dist = -cdist(mydata, mydata, "euclidean") ** 2
    pref = np.min(neg_euc_dist) if num_cluster_pref == 1 else np.median(neg_euc_dist)
    np.fill_diagonal(neg_euc_dist, pref)
    return neg_euc_dist

def init_r_array(s_matrix):
    """
    Function to compute responsibility matrix for iteration 0
    :param s_matrix: numpy array, similarity matrix
    :return: numpy array, responsibility matrix for iteration 0
    """
    r_array_0 = s_matrix - (s_matrix).max(axis=1)[:, None]
    return r_array_0

def a_array_update(num_data_pts, niter, r_array, damp_c, a_array):
    # update a(i,k) values for iteration #niter]
    for i in range(num_data_pts):
        for k in range(num_data_pts):
            if i != k:
                temp_vec = np.ones(num_data_pts)
                temp_vec[k] = 0
                temp_vec[i] = 0
                temp_vec[r_array[niter - 1, :, k] < 0] = 0
                a_ik_sum = np.dot(r_array[niter - 1, :, k], temp_vec)
                for_min = np.concatenate(
                    (r_array[niter - 1, k, k] + a_ik_sum, np.zeros(1)), axis=None
                )
                update_term = np.min(for_min)
                a_array[niter, i, k] = (
                        damp_c * update_term + (1 - damp_c) * a_array[niter - 1, i, k]
                )
            else:
                temp_vec = np.ones(num_data_pts)
                temp_vec[k] = 0
                temp_vec[r_array[niter - 1, :, k] < 0] = 0
                a_ik_sum = np.dot(r_array[niter - 1, :, k], temp_vec)
                update_term = a_ik_sum
                a_array[niter, i, k] = (
                        damp_c * update_term + (1 - damp_c) * a_array[niter - 1, i, k]
                )
    return a_array[niter]

def r_array_update(niter, a_array, s_matrix, damp_c, r_array):
    # update r(i,k) values for iteration #niter
    s_a_array_sum = a_array[niter] + s_matrix
    n = s_a_array_sum.shape[1]
    row_max = np.zeros((n, n))
    rng = np.arange(n)
    for i in rng:
        row_max[:, i] = np.amax(s_a_array_sum[:, rng != i], axis=1)
    update_term = s_matrix - row_max
    r_array[niter] = damp_c * update_term + (1 - damp_c) * r_array[niter - 1]
    return r_array[niter]

def afprop_vec2(
    mydata, num_cluster_pref=1, iterations=100, damp_c=0.5, num_stable_iters=10
):
    # if input is pandas data frame, convert to numpy array
    if isinstance(mydata, pd.DataFrame):
        mydata = mydata.values

    # data input error messages
    if num_cluster_pref != 1 and num_cluster_pref != 2:
        raise ValueError(
            "Enter valid indication (1 or 2) of cluster number preference."
        )
    if iterations < 1 or type(iterations) != int:
        raise ValueError("Enter a valid number of iterations.")
    if damp_c <= 0 or damp_c > 1:
        raise ValueError("Enter a valid damping constant.")
    if (
        num_stable_iters < 1
        or num_stable_iters > iterations
        or type(num_stable_iters) != int
    ):
        raise ValueError("Enter a valid number of iterations to check for stability.")

    # count number of data points, IE number rows in mydata
    num_data_pts = mydata.shape[0]

    # matrix of all the poitwise distances as measured by the metric s
    s_metric_matrix = create_s_metric_matrix(mydata, num_data_pts)

    # same as the above except diagonal entries (IE self-preferences) are set to special values
    # depending on num_cluster_pref
    s_matrix = create_s_matrix(mydata, num_data_pts, num_cluster_pref, s_metric_matrix)

    # initialize a_array: a(i,k) = 0 at 0th iteration
    a_array = np.zeros(num_data_pts * num_data_pts * (iterations)).reshape(
        (iterations, num_data_pts, num_data_pts)
    )

    # initialize r_array
    r_array = np.zeros(num_data_pts * num_data_pts * (iterations)).reshape(
        (iterations, num_data_pts, num_data_pts)
    )

    # fill in r_array values for 0th iteration
    r_array[0] = init_r_array(num_data_pts, s_matrix)

    ### iterative loop for iterations 1+

    # define tracker variables for checking for stability
    clusters_prev = np.zeros(num_data_pts)
    clusters_prev_2 = np.zeros(num_data_pts)
    iter_stability = np.zeros(iterations)

    for niter in range(1, iterations):

        # update a and r arrays at each iteration
        a_array[niter] = a_array_update(num_data_pts, niter, r_array, damp_c, a_array)
        r_array[niter] = r_array_update(
            num_data_pts, niter, a_array, s_matrix, damp_c, r_array
        )

        r_s_sum_array = r_array[niter] + a_array[niter]

        # results of each iteration's clustering attempt
        clusters = np.argmax(
            r_s_sum_array, axis=1
        )  # the list points grouped by their assigned center
        centers = np.where(
            np.argmax(r_s_sum_array, axis=1) == np.array(range(num_data_pts))
        )  # the points that are centers
        is_center = np.argmax(r_s_sum_array, axis=1) == np.array(
            range(num_data_pts)
        )  # true if pt is a center, false otherwise

        # record whether this iteration's clustering is the same as in previous iteration
        if np.array_equal(clusters, clusters_prev):
            iter_stability[niter] = 1

        # if you have seen enough identical clusterings in a row,
        # create a scatterplot illustrating the results
        # and break the iteration loop and return the final clustering results
        if niter > num_stable_iters and np.all(
            iter_stability[niter - num_stable_iters : niter] == 1
        ):
            exemplars = centers[0]
            num_clusters = len(np.unique(clusters))
            final_iter = niter + 1
            # if data is 2D, print scatter plot
            if mydata.shape[1] == 2:
                plt.scatter(
                    mydata[:, 0],
                    mydata[:, 1],
                    c=np.argmax(r_s_sum_array, axis=1),
                    s=200,
                )
                plt.scatter(
                    mydata[:, 0][is_center],
                    mydata[:, 1][is_center],
                    marker="+",
                    s=350,
                    c="black",
                )
                cluster_plot = plt.show()
                return cluster_plot, clusters, exemplars, num_clusters, final_iter
            else:
                return clusters, exemplars, num_clusters, final_iter
            break

        # if you have not seen enough identical clusterings in a row by the final iteration,
        # just print a message
        elif niter == iterations - 1:
            print("Stability not acheived. Consider reducing num_stable_iters.")

        # track the previous cluster, for checking stability in next iteration
        clusters_prev = clusters
