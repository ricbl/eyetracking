import os
import subprocess

def main():
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--file_name', type=str, nargs='?',
                        help='name of the edf file, without the .EDF extension.')
    args = parser.parse_args()
    bashCommand = "edf2asc -res -y " + args.file_name
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

if __name__ == "__main__":
    main()
