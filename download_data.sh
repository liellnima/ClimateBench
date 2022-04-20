#!/bin/bash

#SBATCH --cpus-per-task=4                                # specify cpu

#SBATCH --mem=32G                                        # specify memory

#SBATCH --time=10:00:00                                  # set runtime

#SBATCH -o /home/mila/c/charlotte.lange/slurm-%j.out        # set log dir to home


# 1. Load Python

module load python/3.7


# 3. Create or Set Up Environment

if [ -a env/bin/activate ]; then

    source env/bin/activate

else

    python -m venv env
    source env/bin/activate
    pip install -U pip wheel setuptools

fi


# 4. Install requirements.txt if it exists

if [ -a requirements_prep_data.txt ]; then

    pip install -r requirements_prep_data.txt

fi


# 5. Copy data and code from scratch to $SLURM_TMPDIR/

cp -r /network/scratch/c/charlotte.lange/ClimateBench/  $SLURM_TMPDIR/
#rm -r $SLURM_TMPDIR/caiclone/results/
#cp -r /network/scratch/j/julia.kaltenborn/data/ $SLURM_TMPDIR/

# 6. Set Flags

export GPU=0
export CUDA_VISIBLE_DEVICES=0

# 7. Change working directory to $SLURM_TMPDIR

cd $SLURM_TMPDIR/ClimateBench/

# 8. Run Python

echo "Running python prepare_data.py ..."
python prepare_data.py


# 9. Copy output to scratch
cp -r $SLURM_TMPDIR/ClimateBench/data/* /network/scratch/c/charlotte.lange/ClimateBench/data/

# 10. Experiment is finished

echo "Done."
