#!/bin/bash

#SBATCH --cpus-per-task=4                                # specify cpu

#SBATCH --mem=32G                                        # specify memory

#SBATCH --time=08:00:00                                  # set runtime

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

cp -r  $SLURM_TMPDIR/
#rm -r $SLURM_TMPDIR/caiclone/results/
#cp -r /network/scratch/j/julia.kaltenborn/data/ $SLURM_TMPDIR/

# 6. Set Flags

export GPU=0
export CUDA_VISIBLE_DEVICES=0

# 7. Change working directory to $SLURM_TMPDIR

cd $SLURM_TMPDIR/caiclone/

# 8. Run Python

echo "Running python caiclone_predictor.py ..."
python caiclone_predictor.py -m $MODEL -e $EPOCHS -b $BATCH_SIZE -l $LEARNING_RATE -i $SLURM_TMPDIR/data/precursor_vort_64x64.npy -t $SLURM_TMPDIR/data/labels_vort_64x64.npy


# 9. Copy output to scratch
cp -r $SLURM_TMPDIR/caiclone/results/* /network/scratch/j/julia.kaltenborn/caiclone/results/


# 10. Experiment is finished

echo "Experiment with $EPOCHS epochs, $BATCH_SIZE batch size, $LEARNING_RATE learning rate and $MODEL model is concluded."
