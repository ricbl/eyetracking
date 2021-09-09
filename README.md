# Code for REFLACX dataset

This code was used to collect, process, and validate the REFLACX (Reports and Eye-Tracking Data for Localization of Abnormalities in Chest X-rays) dataset. This dataset contains 3,032 cases of eye-tracking data collected while a radiologist dictated reports for images from the MIMIC-CXR dataset, paired and synchronized with timestamped transcriptions of the dictations. It also contains manual labels for each image, including bounding boxes localizing the lungs+heart and labels (image-level abnormalities, and localization of abnormalities through drawn ellipses) used to validate algorithms that find implicit localization of abnormalities from eye-tracking + transcription.

## How to use this code

The code is organized in 4 folders. `pre_processing_or_sampling_or_ibm_training`, `interface_src`, and `post_processing_and_dataset_generation` are provided to show how our dataset was collected, and their scripts might need changes to hard-coded code to adapt it to different needs of data collection.
`examples_and_paper_numbers` is provided to show how to get the numbers used to validate the publicly available dataset and a few examples of how to use it.
All scripts have to be run from inside their respective folders.

Below we provide a short description of each folder and the recommended order for running scripts that depend on the outputs of other scripts or on manually built tables. 

### pre_processing_or_sampling_or_ibm_training

Code used to generate information needed for running data-collection sessions.

To get the list of images to show to radiologists:
1. `generate_mimic_image_lists_per_user.m` 
2. `download_mimic_files_from_list.m`
3. manually find, between the sampled images, excessively rotated images, clearly flipped images, images with anonymizing rectangles intersecting the lungs, images with a large part of the lungs missing.
4. `exclude_images_from_list.m`

To train the speech-to-text model:
1. `copy_mimic_reports_for_ibm_preprocessing.py`
2. `create_ibm_model.py`

### interface_src

To start the MATLAB interface for data collection, run `interface_src/interface/xray_et.m`.

### post_processing_and_dataset_generation

Code used to generate the dataset from the collected data:
1. `check_wrong_times_in_edf.py`
2. manually create the discard_cases.csv file
3. `get_csv_to_check_transcriptions.py` and `get_list_other.py`
4. manually correct and standardize the transcriptions and "Other" labels
5. `joint_transcription_timestamp.py`
6. `analyze_interrater.py`, `analyze_interrater_phase_2.py`, and  `analyze_interrater_phase_3.py`
7. `ASC2MAT.py`
8. `create_main_table.py`


### examples_and_paper_numbers

Code used to validate the dataset's quality and provide some examples of how to use it. Before running any script, modify the file `dataset_locations.py` to reflect your local setup.

To validate the presence of localization information in the eye-tracking data:
1. `generate_heatmaps.py`
2. `get_ncc_for_localization_in_et_data.py`

To calculate the agreement between radiologists in terms of manual labeling: `interrater.py`

A list of the images from the MIMIC-CXR dataset from which displayed chest x-rays were sampled:`image_all_paths.txt`

To get the statistics for the `image_all_paths.txt` images: `get_filtered_mimic_statistics.py` and `get_sex_statistics_datasets.py`

We also provide examples of:
- how to load tables of manual labels from the dataset: `interrater.py`
- how to normalize the chest position using the chest bounding box: `get_ncc_for_localization_in_et_data.py`
- how DICOMs were loaded and modified (windowing, zooming, panning) for display: `get_brightness_each_sample.py`, `edit_video_any_id.py`
- how to calculate the shown brightness corresponding to the chest x-ray: `get_brightness_each_sample.py`
- how to generate attention heatmaps from the eye-tracking data: `generate_heatmaps.py`
- how to filter fixations by position: `filter_fixations.py`
- how to load the fixations and transcription tables: `edit_video_any_id.py`

The following scripts need additional data not provided with the public dataset:
- `create_calibration_table.py`, which depends on running `post_processing_and_dataset_generation/ASC2MAT.py` first and was used to calculate the average and maximum error values for the calibrations.
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
