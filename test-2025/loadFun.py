#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed April 10 00:23:25 2023
Load .mat data using python

@author: c.y.wang
"""

import scipy.io as scio
import numpy as np
import h5py

def loadmat(filename):
    # read .mat file
    # mat_file = scio.loadmat(filename)
    # #acquire dataset
    # dataset = mat_file['img4ranking']
    try:
        mat_file = scio.loadmat(filename)
        dataset = mat_file['img4ranking']
        print("MAT file opened successfully using scipy.io.loadmat.")
    except NotImplementedError:
        try:
            
            with h5py.File(filename, 'r') as f:
                # read MAT file dataset
                dataset = f['img4ranking'][:]
                dataset = np.transpose(dataset, np.arange(dataset.ndim)[::-1])
            print("MAT file opened successfully using h5py.")
        except Exception as e:
            print("Failed to open MAT file:", str(e))

    return dataset


def ifft2c(x):
    S = np.shape(x)

    # calculate rescale factor
    fctr = S[0] * S[1]

    x = np.reshape(x, (S[0], S[1], np.prod(S[2:])))

    res = np.zeros(np.shape(x), dtype=complex)

    # apply inverse fft to each channel
    for n in range(np.shape(x)[2]):
        res[:,:,n] = np.sqrt(fctr) * np.fft.ifftshift(np.fft.ifft2(np.fft.fftshift(x[:,:,n])))

    res = np.reshape(res, S)

    return res

def multicoilkdata2img(dataset):
    k_space =np.transpose(dataset,[4,3,2,1,0])
    # transfer k-space to complex
    k_space = k_space['real'] + 1j * k_space['imag']
    recon = ifft2c(k_space)
    # apply fft to k-space
    recon = abs(rss_complex(recon, 2))
    return recon

def kdata2img(dataset):
    k_space = np.transpose(dataset, [3, 2, 1, 0])
    # transfer k-space to complex
    k_space = k_space['real'] + 1j * k_space['imag']
    # apply fft to k-space 
    recon = abs(ifft2c(k_space))
    return recon

def loadmat_group(group):
    """
    Load a group in Matlab v7.3 format .mat file using h5py.
    """
    data = {}
    for k, v in group.items():
        if isinstance(v, h5py.Dataset):
            data[k] = v[()]
        elif isinstance(v, h5py.Group):
            data[k] = loadmat_group(v)
    return data

    import numpy as np

def rss(data: np.ndarray, dim: int = 0) -> np.ndarray:
    """
    Compute the Root Sum of Squares (RSS).

    RSS is computed assuming that dim is the coil dimension.

    Args:
        data: The input array
        dim: The dimensions along which to apply the RSS transform

    Returns:
        The RSS value.
    """
    return np.sqrt((data**2).sum(dim))


def rss_complex(data: np.ndarray, dim: int = 0) -> np.ndarray:
    """
    Compute the Root Sum of Squares (RSS) for complex inputs.

    RSS is computed assuming that dim is the coil dimension.

    Args:
        data: The input array
        dim: The dimensions along which to apply the RSS transform

    Returns:
        The RSS value.
    """
    return np.sqrt(np.sum(np.abs(data)**2, axis=dim))