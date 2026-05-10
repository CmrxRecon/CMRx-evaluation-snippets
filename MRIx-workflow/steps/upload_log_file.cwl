#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
label: Upload log file

requirements:
  - class: InlineJavascriptRequirement

inputs:
  - id: synapse_config
    label: filepath to .synapseConfig file
    type: File
  - id: log_file
    label: filepath to the log file, which will be upload
    type: File
  - id: upload_folder_id
    label: the Synapse folder id to upload the log file
    type: string
  - id: file_name
    label: the name display on the synapse website
    type: int

outputs: []
#  - id: item_id
#    label: 
#    type: string
#    outputBinding:
#      glob: results.json
#      outputEval: $(JSON.parse(self[0].contents)['item_id'])
#      loadContents: true

# synapse -c ./synapse_config store --parentid syn51756002 better_log.zip  --name 1.zip
baseCommand: ["synapse"]
arguments:
  - prefix: -c
    valueFrom: $(inputs.synapse_config.path)

  - valueFrom: store

  - prefix: --parentid
    valueFrom: $(inputs.upload_folder_id)

  - valueFrom: $(inputs.log_file.path)

  - prefix: --name
    valueFrom: $(inputs.file_name).zip

hints:
  DockerRequirement:
    dockerPull: sagebionetworks/synapsepythonclient:v2.3.0