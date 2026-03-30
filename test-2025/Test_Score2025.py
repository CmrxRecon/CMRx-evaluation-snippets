"""
Created on May 5 2025

@author: Huang Mingkai

This works for the validation dataset. 
"""
import numpy as np
import os
import glob
from loadFun import loadmat
import pandas as pd
import time
from Evaluation import calmetric
import json
import argparse
import gzip
import tarfile
import zipfile
import rarfile

# List of supported modalities
modalities = [
    'BlackBlood', 'Cine', 'Flow2d', 'LGE',
    'Mapping', 'Perfusion', 'T1rho', 'T1w', 'T2w'
]

def make_key(center, vendor, patient):
    """Construct a unique key to map patient information"""
    return f"{center}|{vendor}|{patient}"

def compute_all_files_counts(gt_root: str, disease_map: dict):
    """
    Traverse the GroundTruth directory and count:
      1. TaskR1: total number of .mat files under each (Center, Vendor)
      2. TaskR2: total number of .mat files for each disease

    Args:
        gt_root: root directory for GroundTruth
        disease_map: mapping from patient_key to [disease1, disease2, ...]

    Returns:
        r1_counts: dict mapping (center, vendor) to file count
        r2_counts: dict mapping disease to file count
    """
    r1_counts = {}
    r2_counts = {}
    s1_counts = {}
    s2_counts = {}
    total_R1 = 0
    total_R2 = 0
    total_S1 = 0
    total_S2 = 0
    modalities = [
        'BlackBlood','Cine','LGE',
        'Mapping','Perfusion','T1rho','T1w','T2w','Flow2d'
    ]

    # TaskR1: count per (Center, Vendor)FullSample
    for modal in modalities:
        pattern = os.path.join(
            gt_root, 'TaskR1', 'MultiCoil', modal,
            'TestSet', 'FullSample_TaskR1',
            '*', '*', '*', '*.mat'
        )
        for fpath in glob.glob(pattern):
            total_R1 += 1
            parts = fpath.split(os.sep)
            center, vendor = parts[-4], parts[-3]
            key = (center, vendor)
            r1_counts[key] = r1_counts.get(key, 0) + 1

    # TaskR2: count per disease
    patient_counts = {}
    for modal in modalities:
        pattern = os.path.join(
            gt_root, 'TaskR2', 'MultiCoil', modal,
            'TestSet', 'FullSample_TaskR2',
            '*', '*', '*', '*.mat'
        )
        for fpath in glob.glob(pattern):
            total_R2 += 1
            parts = fpath.split(os.sep)
            center, vendor, patient = parts[-4], parts[-3], parts[-2]
            key_id = make_key(center, vendor, patient)
            patient_counts[key_id] = patient_counts.get(key_id, 0) + 1

    for key_id, count in patient_counts.items():
        for disease in disease_map.get(key_id, []):
            r2_counts[disease] = r2_counts.get(disease, 0) + count
    
    # TaskS1: count per disease
    patient_counts = {}
    for modal in modalities:
        pattern = os.path.join(
            gt_root, 'TaskS1', 'MultiCoil', modal,
            'TestSet', 'FullSample_TaskS1',
            '*', '*', '*', '*.mat'
        )
        for fpath in glob.glob(pattern):
            total_S1 += 1
            parts = fpath.split(os.sep)
            center, vendor, patient = parts[-4], parts[-3], parts[-2]
            key_id = make_key(center, vendor, patient)
            patient_counts[key_id] = patient_counts.get(key_id, 0) + 1

    for key_id, count in patient_counts.items():
        for disease in disease_map.get(key_id, []):
            s1_counts[disease] = s1_counts.get(disease, 0) + count
    
    # TaskS2: count per disease
    patient_counts = {}
    for modal in modalities:
        pattern = os.path.join(
            gt_root, 'TaskS2', 'MultiCoil', modal,
            'TestSet', 'FullSample_TaskS2',
            '*', '*', '*', '*.mat'
        )
        for fpath in glob.glob(pattern):
            total_S2 += 1
            parts = fpath.split(os.sep)
            center, vendor, patient = parts[-4], parts[-3], parts[-2]
            key_id = make_key(center, vendor, patient)
            patient_counts[key_id] = patient_counts.get(key_id, 0) + 1

    for key_id, count in patient_counts.items():
        for disease in disease_map.get(key_id, []):
            s2_counts[disease] = s2_counts.get(disease, 0) + count


    return r1_counts, r2_counts,s1_counts, s2_counts,total_R1,total_R2,total_S1,total_S2

def ungz(filename, output_dir):
    """Extract a .gz file and return the extracted file path"""
    gz = gzip.GzipFile(filename)
    out_file = os.path.join(output_dir, filename[:-3])
    with open(out_file, 'wb+') as f:
        f.write(gz.read())
    return out_file

def untar(filename, output_dir):
    """Extract a .tar or .tgz archive"""
    with tarfile.open(filename) as tar:
        tar.extractall(path=output_dir)
    return output_dir

def unzip(filename, output_dir):
    """Extract a .zip archive"""
    with zipfile.ZipFile(filename, 'r') as z:
        z.extractall(output_dir)
    return output_dir

def unrar(filename, output_dir):
    """Extract a .rar archive"""
    with rarfile.RarFile(filename) as r:
        r.extractall(output_dir)
    return output_dir

def unzipfile(fpth, output_dir):
    """Automatically extract gz/tar/zip/rar files and return the extraction root directory."""
    if '.' not in fpth:
        try:
            unzip(fpth, output_dir)
            return output_dir
        except:
            raise Exception('Failed to extract file, Unsupported format')
    suffix = fpth.split('.')[-1].lower()
    if suffix == 'gz':
        newf = ungz(fpth, output_dir)
        if newf.endswith('.tar'):
            untar(newf, output_dir)
            os.remove(newf)
    elif suffix in ('tar', 'tgz'):
        untar(fpth, output_dir)
    elif suffix == 'zip':
        unzip(fpth, output_dir)
    elif suffix == 'rar':
        unrar(fpth, output_dir)
    else:
        raise Exception('Unsupported format')
    return output_dir

def compute_metrics(gt_file, recon_file):
    gt = loadmat(gt_file)
    gt = np.squeeze(gt)
    recon = loadmat(recon_file)
    recon = np.squeeze(recon)
    if gt.shape != recon.shape:
        return np.nan, np.nan, np.nan, f'Shape mismatch:gt:{gt.shape}/recon:{recon.shape}'
    psnr, ssim, nmse = calmetric(gt, recon)
    return np.mean(psnr), np.mean(ssim), np.mean(nmse), None

def process_task(challenge_root, gt_root, result_root, task,
                 num_total_files_R1=None, num_total_files_R2=None,
                 num_total_files_S1=None, num_total_files_S2=None,
                 total_R1=None,total_R2=None,
                 total_S1=None,total_S2=None,
                 center_map=None, manufacturer_map=None, disease_map=None):
    SetType = 'TestSet'
    undersample_task = f'{task}' #
    gt_task = f'FullSample_{task}'

    records = []
    start = time.time()

    # Iterate over reconstruction files
    for modal in modalities:
        base_dir = os.path.join(
            gt_root,
            task, 'MultiCoil',
            modal, SetType, gt_task
        )

        pattern = os.path.join(base_dir, '*', '*', '*', '*.mat')#
        
        for gt_path in glob.glob(pattern):
            parts = gt_path.split(os.sep)
            center, vendor, patient = parts[-4], parts[-3], parts[-2]
            key_id = make_key(center, vendor, patient)
            fname = os.path.basename(gt_path)

            recon_path = glob.glob(os.path.join(
                challenge_root, task, 'MultiCoil', modal, SetType,
                undersample_task, center, vendor, patient,
                f'{fname[:-4]}_kus_*.mat'
            ))


            if not recon_path:
                # Build the alternative path that uses "UnderSample_{task}"
                alt_undersample_task = f'UnderSample_{task}'
                alt_base_dir = os.path.join(
                    challenge_root,
                    task, 'MultiCoil',
                    modal, SetType, alt_undersample_task
                )
                recon_path = glob.glob(os.path.join(alt_base_dir, center, vendor, patient,
                f'{fname[:-4]}_kus_*.mat'))


            if not recon_path:
                psnr = ssim = nmse = np.nan
                comment = 'Recon data missing'
            else:
                recon_path = recon_path[0]
                psnr, ssim, nmse, comment = compute_metrics(gt_path, recon_path)

            rec = {
                'Modality': modal,
                'Center': center,
                'Vendor': vendor,
                'Patient': patient,
                'File': fname,
                'PSNR': psnr,
                'SSIM': ssim,
                'NMSE': nmse,
                'Comments': comment
            }
            # Add mapping information
            if task == 'TaskR1' and center_map and manufacturer_map:
                rec['SheetCenter'] = center_map.get(key_id, 'Unknown')
                rec['SheetManufacturer'] = manufacturer_map.get(key_id, 'Unknown')
            if (task == 'TaskR2'or task == 'TaskS1'or task == 'TaskS2') and disease_map is not None:
                rec['Diseases'] = disease_map.get(key_id, [])
            records.append(rec)

    df = pd.DataFrame(records)
    # Ensure the Comments column exists
    if 'Comments' not in df.columns:
        df['Comments'] = np.nan

    # Keep only records without errors
    valid = df[df['Comments'].isna()].copy()

    # Summary statistics
    if task == 'TaskR1':
        summary = {'Num_Files': f"{len(valid)}/{total_R1}"}
    elif task == 'TaskR2':
        summary = {'Num_Files': f"{len(valid)}/{total_R2}"}
    elif task == 'TaskS1':
        summary = {'Num_Files': f"{len(valid)}/{total_S1}"}
    elif task == 'TaskS2':
        summary = {'Num_Files': f"{len(valid)}/{total_S2}"}

    # Task1: aggregate by SheetCenter + SheetManufacturer
    if task == 'TaskR1' and 'SheetCenter' in df.columns and 'SheetManufacturer' in df.columns:

        psnr_means = []
        ssim_means = []
        nmse_means = []

        for (center, vendor), group in valid.groupby(['SheetCenter', 'SheetManufacturer']):
            key = f"{center}_{vendor}"
            num_total_files = num_total_files_R1.get((center, vendor), 0)
            submitted = len(group)
            summary[f'{key}_Num'] = f"{submitted}/{num_total_files}"
            #summary[f'{key}_PSNR'] = round(group['PSNR'].mean(), 4)
            #summary[f'{key}_SSIM'] = round(group['SSIM'].mean(), 4)
            #summary[f'{key}_NMSE'] = round(group['NMSE'].mean(), 4)

            # Adjusted mean: sum / expected count
            if num_total_files:
                mean_psnr = group['PSNR'].sum() / num_total_files
                mean_ssim = group['SSIM'].sum() / num_total_files
                mean_nmse = group['NMSE'].mean() * (2 - len(group) / num_total_files)
                summary[f'{key}_PSNR_adj'] = round(mean_psnr, 4)
                summary[f'{key}_SSIM_adj'] = round(mean_ssim, 4)
                summary[f'{key}_NMSE_adj'] = round(mean_nmse, 4)
                psnr_means.append(mean_psnr)
                ssim_means.append(mean_ssim)
                nmse_means.append(mean_nmse)
        summary['Mean_of_all_centers_PSNR_adj'] = round(sum(psnr_means) / len(psnr_means), 4)
        summary['Mean_of_all_centers_SSIM_adj'] = round(sum(ssim_means) / len(ssim_means), 4)
        summary['Mean_of_all_centers_NMSE_adj'] = round(sum(nmse_means) / len(nmse_means), 4)

    # Task2: aggregate by disease list
    if (task == 'TaskR2' or task == 'TaskS1' or task == 'TaskS2') and 'Diseases' in df.columns:
        all_diseases = set(d for lst in valid['Diseases'] for d in lst)

        psnr_means = []
        ssim_means = []
        nmse_means = []

        for disease in sorted(all_diseases):
            group = valid[valid['Diseases'].apply(lambda lst: disease in lst)]
            if task == 'TaskR2':
                num_total_files = num_total_files_R2.get(disease, 0)
            elif task == 'TaskS1':
                num_total_files = num_total_files_S1.get(disease, 0)
            elif task == 'TaskS2':
                num_total_files = num_total_files_S2.get(disease, 0)
            
            submitted = len(group)
            summary[f'{disease}_Num'] = f"{submitted}/{num_total_files}"
            #summary[f'{disease}_PSNR'] = round(group['PSNR'].mean(), 4)
            #summary[f'{disease}_SSIM'] = round(group['SSIM'].mean(), 4)
            #summary[f'{disease}_NMSE'] = round(group['NMSE'].mean(), 4)
            # Adjusted mean: sum / expected count
            if num_total_files:
                mean_psnr = group['PSNR'].sum() / num_total_files
                mean_ssim = group['SSIM'].sum() / num_total_files
                mean_nmse = group['NMSE'].mean() * (2 - len(group) / num_total_files)
                summary[f'{disease}_PSNR_adj'] = round(mean_psnr, 4)
                summary[f'{disease}_SSIM_adj'] = round(mean_ssim, 4)
                summary[f'{disease}_NMSE_adj'] = round(mean_nmse, 4)
                psnr_means.append(mean_psnr)
                ssim_means.append(mean_ssim)
                nmse_means.append(mean_nmse)
        
        summary['Mean_of_all_diseases_PSNR_adj'] = round(sum(psnr_means) / len(psnr_means), 4)
        summary['Mean_of_all_diseases_SSIM_adj'] = round(sum(ssim_means) / len(ssim_means), 4)
        summary['Mean_of_all_diseases_NMSE_adj'] = round(sum(nmse_means) / len(nmse_means), 4)

    # Output results, with filenames separated by task
    result_dir = os.path.join(result_root, 'Result')
    os.makedirs(result_dir, exist_ok=True)

    # Summary JSON
    json_name = f"results.json"
    json_content = {'submission_status': 'SCORED', **summary}
    with open(os.path.join(result_dir, json_name), 'w') as f:
        json.dump(json_content, f, indent=4)
    # Excel, two sheets
    excel_name = f"result_{task}.xlsx"
    excel_path = os.path.join(result_dir, excel_name)
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='results', index=False)
        summary_df = pd.DataFrame(
            [{'Category': k, 'Value': v} for k, v in summary.items()]
        )
        summary_df.to_excel(writer, sheet_name='summary', index=False)

    print(f"{task} completed in {time.time() - start:.2f}s")

    # Participant Excel: two-column summary
    participant_excel_name = f"result_{task}_for_participant.xlsx"
    participant_excel_path = os.path.join(result_dir, participant_excel_name)
    # Build a list of {Category, Value} dicts from the JSON content
    participant_records = [
        {'Category': k, 'Value': v}
        for k, v in json_content.items()
    ]
    participant_df = pd.DataFrame(participant_records)
    participant_df.to_excel(participant_excel_path, index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='Submission.zip or folder')
    parser.add_argument('-t', '--task', required=True, help='Specify task category (TaskR1 or TaskR2)')
    parser.add_argument('-g', '--groundtruth', required=True, help='Root directory of GroundTruth')
    parser.add_argument('-o', '--output', default='./', help='Extraction and output directory')
    parser.add_argument('-e', '--excel', required=True,
                        help='Excel file. TaskR1 sheet needs columns Center/Manufacturer/AnonPatientID, '
                             'TaskR2 sheet needs columns Center/Manufacturer/AnonPatientID/Disease1~4')
    args = parser.parse_args()

    root = args.input
    
    gt_root = args.groundtruth

    xls = pd.ExcelFile(args.excel)
    center_map = {}
    manufacturer_map = {}
    disease_map = {}
    tasks = []
    for task in ('TaskR1', 'TaskR2','TaskS1','TaskS2'):
        if os.path.isdir(os.path.join(root, task)):
            tasks.append(task)
            df_sheet = pd.read_excel(xls, sheet_name=task, dtype=str)
            # Build composite key
            for _, row in df_sheet.iterrows():
                key_id = make_key(row['Center'], row['Manufacturer'], row['AnonPatientID'])
                if task == 'TaskR1':
                    center_map[key_id] = row['Center']
                    manufacturer_map[key_id] = row['Manufacturer']
                elif task == 'TaskR2'or task == 'TaskS1'or task == 'TaskS2' :
                    diseases = [row.get(f'Disease{i}') for i in range(1, 6)]
                    #diseases = [d for d in diseases if pd.notna(d) and d != '']
                    diseases =  [
                                d.strip().replace(',', '').replace(' ', '_')
                                for d in diseases
                                if pd.notna(d) and d.strip() != ''
                                ]
                    # Remove duplicates and sort
                    disease_map[key_id] = diseases

    num_total_files_R1, num_total_files_R2,num_total_files_S1,num_total_files_S2,total_R1,total_R2,total_S1,total_S2 = compute_all_files_counts(gt_root, disease_map)

    if  args.task in tasks:
        print(f"=== Processing {args.task} ===")
        process_task(
            root, gt_root, args.output, args.task,
            num_total_files_R1,
            num_total_files_R2,
            num_total_files_S1,
            num_total_files_S2,
            total_R1,total_R2,
            total_S1,total_S2,
            center_map=center_map,
            manufacturer_map=manufacturer_map,
            disease_map=disease_map
        )
    os.system(f'zip -r better_log.zip {args.output}/Result/*')

'''
python Test_Score2025.py \
  -i /mnt/nas/nas4/privateData/tmp-CMRxRecon2025-debug/test-output/15/infer \
  -t TaskR1 \
  -g /mnt/nas/nas3/openData/share/ChallengeData_TestSet_GroundTruth \
  -o /mnt/nas/nas3/openData/share/Evaluation_Result \
  -e /SSDHome/home/huangmk/evaluation_platform/evaluation-2025/CMRxRecon2025_TestData_Disease_Info_English.xlsx
'''
