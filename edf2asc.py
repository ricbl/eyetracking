import os
import subprocess

rootdir = 'input'
extensions = ('.edf',)



# data_folders = ['user3_203_20201210-101303-6691','user3_203_20201217-083511-9152', 'user2_203_20201201-092234-9617', 'user1_203_20201216-141859-3506', 'user1_203_20201216-142259-5921', 'user1_203_20201218-142722-8332', 'user1_203_20201223-140239-9152', 'user4_203_20201222-150420-9152', 'user5_203_20201113', 'user4_203_20210104-130049-9152']
# data_folders = ['phase_2/user4_204_20210303-133107-9152','phase_2/user1_204_20210301-141046-2142','phase_2/user1_204_20210301-143153-9220','phase_2/user5_204_20210302-142915-8332', 'phase_2/user5_204_20210302-145812-8332', 'phase_2/user2_204_20210308-080302-9152', 'phase_2/user3_204_20210311-101017-9152','phase_2/user3_204_20210311-121106-2142' ]
# data_folders = ['training/user3_101_20201210-083836-9220','training/user2_101_20201201-083622-3506','training/user2_101_20201201-084811-5921','training/user4_101_20201222-134634-2142', 'training/user4_101_20201222-140213-8332']
# for rootdir in data_folders:
for subdir, dirs, files in os.walk('anonymized_collected_data/phase_3/'):
    for file in files:
        ext = os.path.splitext(file)[-1].lower()
        if ext in extensions:
            bashCommand = "edf2asc -res -y " + os.path.join(subdir, file)
            process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()
            print(os.path.join(subdir, file))