#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow
label: Task1-Multi-contrast
doc: >
  For CMRx4DFlow 2026 validation

requirements:
  - class: StepInputExpressionRequirement

inputs:
  submissionId:
    label: Submission ID
    type: int
  submitterUploadSynId:
    label: Synapse Folder ID accessible by the submitter
    type: string
  synapseConfig:
    label: filepath to .synapseConfig file
    type: File

outputs: {}

steps:

  set_submitter_folder_permissions:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.1/cwl/set_permissions.cwl
    in:
      - id: entityid
        source: "#submitterUploadSynId"
      # TODO: replace `valueFrom` with the admin user ID or admin team ID
      - id: principalid
        valueFrom: "3466681" 
      - id: permissions
        valueFrom: "download"
      - id: synapse_config
        source: "#synapseConfig"
    out: []

  download_submission:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.1/cwl/get_submission.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: synapse_config
        source: "#synapseConfig"
    out:
      - id: filepath
      - id: docker_repository
      - id: docker_digest
      - id: entity_id
      - id: entity_type
      - id: results

  score:
    run: steps/score-task1.cwl
    in:
      - id: input_file
        source: "#download_submission/filepath"
      # - id: goldstandard
      #   source: "#download_goldstandard/filepath"
      #- id: check_validation_finished 
      #  source: "#check_status/finished"
    out:
      - id: results
      - id: log_file

  upload_log_file:
    run: steps/upload_log_file.cwl
    in: 
      - id: synapse_config
        source: "#synapseConfig"
      - id: log_file
        source: "#score/log_file"
      # TODO synapse id of the detail log_file store folder
      - id: upload_folder_id
        valueFrom: "syn74297844"
      - id: file_name
        source: "#submissionId"
    out: []
      
  email_score:
    #run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.1/cwl/score_email.cwl
    # TODO swich to the email score
    run: steps/email_score.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: synapse_config
        source: "#synapseConfig"
      - id: results
        source: "#score/results"
      # OPTIONAL: add annotations to be withheld from participants to `[]`
      # - id: private_annotations
      #   default: []
    out: []

  annotate_submission_with_output:
    run: https://raw.githubusercontent.com/Sage-Bionetworks/ChallengeWorkflowTemplates/v3.1/cwl/annotate_submission.cwl
    in:
      - id: submissionid
        source: "#submissionId"
      - id: annotation_values
        source: "#score/results"
      - id: to_public
        default: true
      - id: force
        default: true
      - id: synapse_config
        source: "#synapseConfig"
      - id: previous_annotation_finished
        #source: "#annotate_validation_with_output/finished"
        default: true
    out: [finished]
 
