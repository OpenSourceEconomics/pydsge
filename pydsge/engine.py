#!/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import numpy.linalg as nl
import time
from .parser import DSGE as dsge
from numba import njit

aca = np.ascontiguousarray


@njit(cache=True, nogil=True)
def preprocess_jit(PU, MU, PR, MR, gg, fq1, fp1, fq0, omg, lam, x_bar, l_max, k_max):
    """jitted preprocessing of system matrices until (l_max, k_max)
    """

    dimp, dimq = omg.shape
    l_max += 1
    k_max += 1

    # cast matrices of unconstraint sys in nice form
    Q, S = nl.qr(PU)
    T = Q.T @ aca(MU)

    S11i = nl.inv(S[:dimq,:dimq])
    T[:dimq] = S11i @ T[:dimq]
    S[:dimq] = S11i @ S[:dimq]

    T22i = nl.inv(T[dimq:,dimq:])
    T[dimq:] = T22i @ T[dimq:]
    S[dimq:] = T22i @ S[dimq:]

    S[:dimq,dimq:] -= T[:dimq,dimq:] @ S[dimq:,dimq:]
    T[:dimq,:dimq] -= T[:dimq,dimq:] @ T[dimq:,:dimq]
    T[:dimq,dimq:] = 0

    # cast matrices of constraint sys in nice form
    Q, V = nl.qr(PR)
    W = Q.T @ MR
    h = Q.T @ gg

    V11i = nl.inv(V[:dimq,:dimq])
    W[:dimq] = V11i @ W[:dimq]
    V[:dimq] = V11i @ V[:dimq]
    h[:dimq] = V11i @ h[:dimq]

    W22i = nl.inv(W[dimq:,dimq:])
    W[dimq:] = W22i @ W[dimq:]
    V[dimq:] = W22i @ V[dimq:]
    h[dimq:] = W22i @ h[dimq:]

    h[:dimq] -= W[:dimq,dimq:] @ h[dimq:]
    V[:dimq,dimq:] -= W[:dimq,dimq:] @ V[dimq:,dimq:]
    W[:dimq,:dimq] -= W[:dimq,dimq:] @ W[dimq:,:dimq]
    W[:dimq,dimq:] = 0


    def get_lam(omg, psi, l):

        A = S if l else V
        B = T if l else W
        c = np.zeros(dimq) if l else h[:dimq]

        inv = nl.inv(np.eye(dimq) + A[:dimq,dimq:] @ omg)
        lam = inv @ B[:dimq,:dimq]
        xi = inv @ (c - A[:dimq,dimq:] @ psi)

        return lam, xi


    def get_omg(omg, psi, lam, xi, l):
        
        A = S if l else V
        B = T if l else W
        c = np.zeros(dimp) if l else h[dimq:]

        psi = A[dimq:,dimq:] @ (omg @ xi + psi) - c
        omg = A[dimq:,dimq:] @ omg @ lam - B[dimq:,:dimq]

        return omg, psi


    pmat = np.empty((l_max, k_max, dimp, dimq))
    qmat = np.empty((l_max, k_max, dimq, dimq))
    pterm = np.empty((l_max, k_max, dimp))
    qterm = np.empty((l_max, k_max, dimq))

    bmat = np.empty((l_max + k_max, l_max, k_max, dimq))
    bterm = np.empty((l_max + k_max, l_max, k_max))

    pmat[0,0] = omg
    pterm[0,0] = np.zeros(dimp)
    qmat[0,0] = lam
    qterm[0,0] = np.zeros(dimq)

    lam = np.eye(dimq)
    xi = np.zeros(dimq)

    for s in range(l_max + k_max):

        y2r = fp1 @ pmat[0,0] + fq1 @ qmat[0,0] + fq0
        cr = fp1 @ pterm[0,0] + fq1 @ qterm[0,0]

        bmat[s,0,0] = y2r @ lam
        bterm[s,0,0] = cr + y2r @ xi

        lam = qmat[0,0] @ lam
        xi = qmat[0,0] @ xi + qterm[0,0]

    for k in range(1,k_max):
        qmat[0,k], qterm[0,k] = get_lam(pmat[0,k-1], pterm[0,k-1], 0)
        pmat[0,k], pterm[0,k] = get_omg(pmat[0,k-1], pterm[0,k-1], qmat[0,k], qterm[0,k], 0)

        # initialize local lam, xi to iterate upon
        lam = np.eye(dimq)
        xi = np.zeros(dimq)

        for s in range(l_max + k_max):

            k_loc = max(min(k, k-s), 0)

            y2r = fp1 @ pmat[0,k_loc] + fq1 @ qmat[0,k_loc] + fq0
            cr = fp1 @ pterm[0,k_loc] + fq1 @ qterm[0,k_loc]
            bmat[s,0,k] = y2r @ lam
            bterm[s,0,k] = cr + y2r @ xi

            lam = qmat[0,k_loc] @ lam
            xi = qmat[0,k_loc] @ xi + qterm[0,k_loc]


    for l in range(1,l_max):
        for k in range(0, k_max):
            qmat[l,k], qterm[l,k] = get_lam(pmat[l-1,k], pterm[l-1,k], l)
            pmat[l,k], pterm[l,k] = get_omg(pmat[l-1,k], pterm[l-1,k], qmat[l,k], qterm[l,k], l)

            # initialize local lam, xi to iterate upon
            lam = np.eye(dimq)
            xi = np.zeros(dimq)

            for s in range(l_max + k_max):

                l_loc = max(l-s, 0)
                k_loc = max(min(k, k+l-s), 0)

                y2r = fp1 @ pmat[l_loc,k_loc] + fq1 @ qmat[l_loc,k_loc] + fq0
                cr = fp1 @ pterm[l_loc,k_loc] + fq1 @ qterm[l_loc,k_loc]
                bmat[s,l,k] = y2r @ lam
                bterm[s,l,k] = cr + y2r @ xi

                lam = qmat[l_loc,k_loc] @ lam
                xi = qmat[l_loc,k_loc] @ xi + qterm[l_loc,k_loc]

            ## TODO: this part must be improved
                # Handeld more efficiently
                # only add the 5 necessary steps for s: 0, l-1, l, k+l-1, k+l

    return pmat, qmat, pterm, qterm, bmat, bterm


def preprocess(self, PU, MU, PR, MR, gg, fq1, fp1, fq0, verbose): 
    """dispatcher to jitted preprocessing
    """

    l_max, k_max = self.lks
    omg, lam, x_bar, zp, zq, zc = self.sys

    st = time.time()
    self.precalc_mat = preprocess_jit(PU, MU, PR, MR, gg, fq1, fp1, fq0, omg, lam, x_bar, l_max, k_max)

    if verbose:
        print('[preprocess:]'.ljust(15, ' ')+' Preprocessing finished within %ss.' % np.round((time.time() - st), 3))

    return


@njit(nogil=True, cache=True)
def find_lk(bmat, bterm, x_bar, q):
    """iteration loop to find (l,k) given state q
    """

    _, l_max, k_max = bterm.shape

    flag = 0
    l, k = 0, 0

    # check if (0,0) is a solution
    while check_cnst(bmat, bterm, l, l, 0, q) - x_bar > 0:
        l += 1
        if l == l_max:
            break

    # check if (0,0) is a solution
    if l < l_max:
        # needs to be wrapped so that both loops can be exited at once
        l, k = bruite_wrapper(bmat, bterm, x_bar, q)

        # if still no solution, use approximation
        if l == 999:
            flag = 1
            l, k = 0, 0
            while check_cnst(bmat, bterm, k, 0, k, q) - x_bar > 0:
                k += 1
                if k >= k_max:
                    # set error flag 'no solution + k_max reached'
                    flag = 2
                    break

    if not k:
        l = 1

    return l, k, flag


@njit(cache=True, nogil=True)
def t_func_jit(pmat, pterm, qmat, qterm, bmat, bterm, x_bar, zp, zq, zc, state, shocks, set_l, set_k, x_space):
    """jitted transitiona function
    """

    q = aca(state)
    q[-len(shocks):] += shocks

    if set_k == -1:
        # find (l,k) if requested
        l, k, flag = find_lk(bmat, bterm, x_bar, q)
    else:
        l, k = set_l, set_k
        flag = 0

    p = pmat[l,k] @ q + pterm[l,k]
    q = qmat[l,k] @ q + qterm[l,k]

    # instead, I should either return p or obs
    if x_space:
        p_or_obs = zp @ aca(p) + zq @ q + zc
    else:
        p_or_obs = p

    return p_or_obs, q, l, k, flag


@njit(nogil=True, cache=True)
def check_cnst(bmat, bterm, s, l, k, q0):
    """constraint value in period s given CDR-state q0 under the assumptions (l,k)
    """
    return bmat[s, l, k] @ q0 + bterm[s, l, k]


@njit(nogil=True, cache=True)
def bruite_wrapper(bmat, bterm, x_bar, q):
    """iterate over (l,k) until (l_max, k_max) and check if RE equilibrium
    """
    _, l_max, k_max = bterm.shape

    for l in range(l_max):
        for k in range(1, k_max):
            if l:
                if check_cnst(bmat, bterm, 0, l, k, q) - x_bar < 0:
                    continue
                if l > 1:
                    if check_cnst(bmat, bterm, l-1, l, k, q) - x_bar < 0:
                        continue
            if check_cnst(bmat, bterm, k+l, l, k, q) - x_bar < 0:
                continue
            if check_cnst(bmat, bterm, l, l, k, q) - x_bar > 0:
                continue
            if k > 1:
                if check_cnst(bmat, bterm, k+l-1, l, k, q) - x_bar > 0:
                    continue
            return l, k

    return 999, 999
