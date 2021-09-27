# Code for REFLACX dataset

This code was used to collect, process, and validate the REFLACX (Reports and Eye-Tracking Data for Localization of Abnormalities in Chest X-rays) dataset. This dataset contains 3,032 cases of eye-tracking data collected while a radiologist dictated reports for images from the MIMIC-CXR dataset, paired and synchronized with timestamped transcriptions of the dictations. It also contains manual labels for each image, including bounding boxes localizing the lungs+heart and labels (image-level abnormalities and localization of abnormalities through drawn ellipses) used to validate algorithms that find implicit localization of abnormalities from eye-tracking + transcription. The dataset is available at [https://physionet.org/content/reflacx-xray-localization/1.0.0/](https://physionet.org/content/reflacx-xray-localization/1.0.0/)

## How to use this code

The code is organized in 4 folders. `pre_processing_or_sampling_or_ibm_training`, `interface_src`, and `post_processing_and_dataset_generation` are provided to show how our dataset was collected, and their scripts might need changes to hard-coded code to adapt it to different needs of data collection.
`examples_and_paper_numbers` is provided to show how to get the numbers used to validate the publicly available dataset and a few examples of how to use it.
All scripts have to be run from inside their respective folders.

Below we provide a short description of each folder and the recommended order for running scripts. The provided paths are relative to each of the folders.

### pre_processing_or_sampling_or_ibm_training

Code used to generate information needed for running data-collection sessions.

To get the list of images to show to radiologists:
1. Place tables from the MIMIC-CXR and MIMIC-CXR-JPG dataset in `../datasets/mimic/tables/`
2. Run `generate_mimic_image_lists_per_user.m` 
3. Run `download_mimic_files_from_list.m`
4. Run `copy_list_to_folder_for_checking.m`
5. Manually find, between the sampled images listed in the `images_check_rectangle/` folder, excessively rotated images, clearly flipped images, images with anonymizing rectangles intersecting the lungs, images with a large part of the lungs missing.
6. Run `exclude_images_from_list.m`

To train the speech-to-text model:
1. Place reports  from the MIMIC-CXR dataset (`file`s folder) in `../datasets/mimic/reports/`
2. Run `copy_mimic_reports_for_ibm_preprocessing.py`
3. Put the credentials of the IBM Watson account in `credentials/ibm_credentials_sci.json` (check the `get_credentials` function in`create_ibm_model.py` for the needed keywords)
4. Run `create_ibm_model.py`

For a list of expressions used as a sign that a sentence in a report referred to another study, check the `list_of_unwanted_expressions` variable in `copy_mimic_reports_for_ibm_preprocessing.py`. Sentences with any of these expressions were not used in the training of the IBM Watson Speech to Text models. Sentences with characters that were not whitespaces, comma, letters or hyphens were also excluded.

For a list of transcription errors automatically corrected before the editing by the radiologists, check the `replace_dict` variable in `../interface_src/scripts/convert_audio_to_text_ibm.py`.

### interface_src

To start the MATLAB interface for data collection, initialize MATLAB with the`ptb3-matlab` command line command and run `interface/xray_et.m`.

#### Quick instructions for the use of the interface

##### General
- The meaning of each argument from the interface configuration window is commented at the beginning of the `interface/xray_et.m` script.
- Instructions for what to do on each screen are displayed by the interface.
- Use the "Save And Exit" button to exit the interface properly. Alt + E exits the interface when in the middle of a case, but, when used, data is not fully saved for that case. Avoid clicking Ctrl + C because it may make the interface unresponsive.
- Cases with red warnings on the last screen should be discarded.

##### Chest x-rays
- The right mouse button controls windowing. Dragging the mouse up and down controls window width, while left and right controls window level.
- The middle mouse wheel or up/down arrow control zooming.
- Drag with the middle mouse button for panning.
- Drag with the left mouse button to draw ellipses and bounding boxes, when available.

##### Dictation screen
- Punctuations have to be dictated: comma, period, and slash.
- Audio recording is automatic.

##### Text editing
- Drag with the left mouse button to select.
- Click the left mouse button to change the cursor position.
- Double click the left mouse button to select a word.
- Use Ctrl + z to undo.
- Use Ctrl + a to redo.
- Use Ctrl + q to cut.
- Use select + deselect to copy.
- Use the right mouse button to paste.
- Use arrows to navigate the cursor.

##### Drawing ellipses
- Ellipses are not mandatory for "Support Devices" and "Other" labels.
- The certainty of previous bounding boxes is shown in the upper left corner of the screen with the following code:
  - 1 for "Unlikely"
  - 3 for "Less Likely"
  - 5 for "Possibly"
  - 7 for for "Suspicious for/Probably"
  - 9 for "Consistent with".
- Click out of the ellipse you are currently drawing to reset it.
- The next screen button is disabled if an ellipse is being edited but is not saved.
 
### post_processing_and_dataset_generation

Code used to generate the dataset from the collected data:
1. Place the folders of the experiments to be transformed into the dataset inside the folders `../anonymized_collected_data/phase_1`, `../anonymized_collected_data/phase_2`, and `../anonymized_collected_data/phase_3`
2. Run `check_wrong_times_in_edf.py`
3. Manually create the `discard_cases.csv` file, listing the cases to discard for all reasons, with columns `trial` (int), `user` (string), and `phase` (int)
4. Run `get_csv_to_check_transcriptions.py` and `get_list_other.py`
5. Editing the generated tables, manually correct and standardize the transcriptions and "Other" labels, placing the corresponding tables in `../anonymized_collected_data/phase_<phase>/`
6. Run `joint_transcription_timestamp.py`
7. Run `analyze_interrater.py`, `analyze_interrater_phase_2.py`, and  `analyze_interrater_phase_3.py`
8. Run `ASC2MAT.py`
9. Run `create_main_table.py`


### examples_and_paper_numbers

Code used to validate the dataset's quality and provide some examples of how to use it. Before running any script, modify the file `dataset_locations.py` to reflect your local setup.

To validate the presence of localization information in the eye-tracking data:
1. Run `generate_heatmaps.py`
2. Run `get_ncc_for_localization_in_et_data.py`

To calculate the agreement between radiologists in terms of manual labeling, run `interrater.py`

`image_all_paths.txt` is a list of the images from the MIMIC-CXR dataset from which displayed chest x-rays were sampled.

To get the statistics for the `image_all_paths.txt` images, run `get_filtered_mimic_statistics.py` and `get_sex_statistics_datasets.py`

The tables used to calculate some of the numbers shown in the paper are in `tables_calculations/`. These tables were modified from the csv files generated by other scripts.

We also provide examples of:
- how to load tables of manual labels from the dataset: `interrater.py`
- how to normalize the chest position using the chest bounding box: `get_ncc_for_localization_in_et_data.py`
- how DICOMs were loaded and modified (windowing, zooming, panning) for display: `get_brightness_each_sample.py`, `edit_video_any_id.py`
- how to calculate the shown brightness corresponding to the chest x-ray: `get_brightness_each_sample.py`
- how to generate attention heatmaps from the eye-tracking data: `generate_heatmaps.py`
- how to filter fixations by position: `filter_fixations.py`
- how to load the fixations and transcription tables: `edit_video_any_id.py`

The following scripts need additional data not provided with the public dataset:
- `create_calibration_table.py`, which depends on the output from `../post_processing_and_dataset_generation/ASC2MAT.py` and was used to calculate the average and maximum error values for the calibrations.
- `edit_video.py`, used to generate a video showing interface use through all screens of a case, with all portions recorded by the MATLAB interface.


## Requirements

### Python
* Python 3.7.7
* numpy 1.19.1
* pandas 1.1.1
* librosa 0.8.0
* statsmodels 0.12.2
* shapely 1.7.1
* scikit-image 0.17.2
* pyrubberband 0.3.0
* pydicom 2.1.2
* pydub 0.24.1
* soundfile 0.10.3.post1
* pyttsx3 2.90
* pillow 8.0.1
* scikit-learn 0.23.2
* nltk 3.5
* syllables 1.0.0
* moviepy 1.0.3
* opencv 3.4.2

### EyeLink
* edfapi 3.1
* EYELINK II CL v5.15
* Eyelink GL Version 1.2 Sensor=AC7
* EDF2ASC 3.1

### Other 
* MATLAB R2019a
* Psychtoolbox 3.0.17
* Ubuntu 18.04.5 LTS
* espeak 1.48.04
* ffmpeg 3.4.8
* rubberband-cli 1.8.1

## Citing this repository

If you use the dataset, please follow the citation instructions available at [https://doi.org/10.13026/e0dj-8498](https://doi.org/10.13026/e0dj-8498).


If you use this software, please cite a Zenodo release:
[![DOI](https://zenodo.org/badge/386056923.svg)](https://zenodo.org/badge/latestdoi/386056923)


