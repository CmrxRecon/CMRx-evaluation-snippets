"""
Copyright (c) Facebook, Inc. and its affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""
import os
from typing import Optional
import csv
import pandas as pd

import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def mse(gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """Compute Mean Squared Error (MSE)"""
    return np.mean((gt - pred) ** 2)


def nmse(gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """Compute Normalized Mean Squared Error (NMSE)"""
    return np.array(np.linalg.norm(gt - pred) ** 2 / np.linalg.norm(gt) ** 2)


def psnr(
    gt: np.ndarray, pred: np.ndarray, maxval: Optional[float] = None
) -> np.ndarray:
    """Compute Peak Signal to Noise Ratio metric (PSNR)"""
    if maxval is None:
        maxval = gt.max()
    return peak_signal_noise_ratio(gt, pred, data_range=maxval)


def ssim(
    gt: np.ndarray, pred: np.ndarray, maxval: Optional[float] = None
) -> np.ndarray:
    """Compute Structural Similarity Index Metric (SSIM)"""
    if maxval is None:
        maxval = gt.max()
    return structural_similarity(gt, pred, data_range=maxval)

def normalize_std(array):
    """Normalize an array using mean and standard deviation."""
    mean = np.mean(array)
    std = np.std(array) + 1e-8
    return (array - mean) / std


def normalize_percentile(array):
    # get magnitude
    data = np.abs(array)
    # calculate 99% percentile
    percentile99 = np.percentile(data, 99.5)
    # avoid dividing 0
    if percentile99 == 0:
        return data
    # normalization
    #data_normalize = np.clip(data / percentile99, 0, 1)
    data_normalize = data / percentile99

    return data_normalize


def calmetric(pred_recon, gt_recon):

    if gt_recon.ndim == 5:
        D, H, W = gt_recon.shape[-3], gt_recon.shape[-2], gt_recon.shape[-1]
        psnr_array = np.zeros((D, H, W), dtype=np.float64)
        ssim_array = np.zeros((D, H, W), dtype=np.float64)
        nmse_array = np.zeros((D, H, W), dtype=np.float64)

        for k in range(D):
            for i in range(H):
                for j in range(W):
                    # Take a 2D slice over the first two dims, fixing the last three indices
                    # pred/gt will be 2D arrays shaped like pred_recon[:, :, k, i, j]
                    pred = pred_recon[:, :, k, i, j]
                    gt   = gt_recon[:, :, k, i, j]

                    # Robust normalization
                    pred_normalized = normalize_percentile(pred)
                    gt_normalized   = normalize_percentile(gt)

                    # Metrics for this (k, i, j)
                    psnr_array[k, i, j] = psnr(gt_normalized, pred_normalized)
                    ssim_array[k, i, j] = ssim(gt_normalized, pred_normalized)
                    nmse_array[k, i, j] = nmse(gt_normalized, pred_normalized)
    
    elif gt_recon.ndim == 4:
        psnr_array = np.zeros((gt_recon.shape[-2], gt_recon.shape[-1]))
        ssim_array = np.zeros((gt_recon.shape[-2], gt_recon.shape[-1]))
        nmse_array = np.zeros((gt_recon.shape[-2], gt_recon.shape[-1]))

        for i in range(gt_recon.shape[-2]):
            for j in range(gt_recon.shape[-1]):
                pred, gt = pred_recon[:, :, i, j], gt_recon[:, :, i, j]
                # revise the normlization to a more stable way
                pred_normalized = normalize_percentile(pred)
                gt_normalized = normalize_percentile(gt)

                psnr_array[i, j] = psnr(gt_normalized, pred_normalized)
                ssim_array[i, j] = ssim(gt_normalized, pred_normalized)
                nmse_array[i, j] = nmse(gt_normalized, pred_normalized)
    elif gt_recon.ndim == 3:
        psnr_array = np.zeros((1, gt_recon.shape[-1]))
        ssim_array = np.zeros((1, gt_recon.shape[-1]))
        nmse_array = np.zeros((1, gt_recon.shape[-1]))

        for j in range(gt_recon.shape[-1]):
            pred, gt = pred_recon[:, :, j], gt_recon[:, :, j]

            # revise the normlization to a more stable way
            pred_normalized = normalize_percentile(pred)
            gt_normalized = normalize_percentile(gt)

            psnr_array[0,j] = psnr(pred_normalized, gt_normalized)
            ssim_array[0,j] = ssim(pred_normalized, gt_normalized)
            nmse_array[0,j] = nmse(pred_normalized, gt_normalized)
    
    elif gt_recon.ndim == 2:
        psnr_array = np.zeros((1))
        ssim_array = np.zeros((1))
        nmse_array = np.zeros((1))


        pred, gt = pred_recon, gt_recon

        # revise the normlization to a more stable way
        pred_normalized = normalize_percentile(pred)
        gt_normalized = normalize_percentile(gt)

        psnr_array = psnr(pred_normalized, gt_normalized)
        ssim_array  = ssim(pred_normalized, gt_normalized)
        nmse_array = nmse(pred_normalized, gt_normalized)

    return psnr_array, ssim_array, nmse_array


def save_metric(psnr_array, ssim_array, nmse_array, folder, Sub_Task, Coil_Type):
    Results_folder_name = Coil_Type+'_'+Sub_Task+'_Results'
    if not os.path.exists(Results_folder_name):
        os.makedirs(Results_folder_name)

    filename  = Results_folder_name + '/' + Sub_Task + '_psnr_results.csv'
    if not os.path.isfile(filename):
        with open(filename, mode='a') as psnr_file:
            writer = csv.writer(psnr_file)
            writer.writerow(['folder', 'Sub_Task', 'PSNR'])
    with open(filename, mode='a') as psnr_file:
        writer = csv.writer(psnr_file)
        writer.writerow([folder, Sub_Task, psnr_array])

    filename = Results_folder_name + '/' + Sub_Task + '_ssim_results.csv'
    if not os.path.isfile(filename):
        with open(filename, mode='a') as ssim_file:
            writer = csv.writer(ssim_file)
            writer.writerow(['folder', 'Sub_Task', 'SSIM'])
    with open(filename, mode='a') as ssim_file:
        writer = csv.writer(ssim_file)
        writer.writerow([folder, Sub_Task, ssim_array])

    filename = Results_folder_name + '/' + Sub_Task + '_nmse_results.csv'
    if not os.path.isfile(filename):
        with open(filename, mode='a') as nmse_file:
            writer = csv.writer(nmse_file)
            writer.writerow(['folder', 'Sub_Task', 'NMSE'])
    with open(filename, mode='a') as nmse_file:
        writer = csv.writer(nmse_file)
        writer.writerow([folder, Sub_Task, nmse_array])

def memo_metric0(gt_recon):
    psnr_array = np.zeros((gt_recon.shape[2], gt_recon.shape[3]))
    ssim_array = np.zeros((gt_recon.shape[2], gt_recon.shape[3]))
    nmse_array = np.zeros((gt_recon.shape[2], gt_recon.shape[3]))
    return psnr_array, ssim_array, nmse_array


def save_df(user_input,table,processed_list, Sub_Task,Coil_Type):
    # Save wall thickness for all the subjects
    Results_folder_name = Coil_Type + '_' + Sub_Task + '_Results'
    filename = Results_folder_name + '/' + Sub_Task + '_ROI_results.csv'
    columns_list = ['Mapping_AHA_1', 'Mapping_AHA_2', 'Mapping_AHA_3',
                    'Mapping_AHA_4', 'Mapping_AHA_5', 'Mapping_AHA_6',
                    'Mapping_AHA_7', 'Mapping_AHA_8', 'Mapping_AHA_9',
                    'Mapping_AHA_10', 'Mapping_AHA_11', 'Mapping_AHA_12',
                    'Mapping_AHA_13', 'Mapping_AHA_14', 'Mapping_AHA_15', 'Mapping_AHA_16',
                    'Mapping_Global']
    columns_list = [user_input + '_' + s for s in columns_list]

    df = pd.DataFrame(table, index=processed_list,
                      columns=columns_list
                      )
    df.to_csv(filename)