#!/bin/bash
#SBATCH --job-name=blicket
#SBATCH --partition=kmarino-gpu-grn
#SBATCH --qos=kmarino-gpu-grn
#SBATCH --account=kmarino
#SBATCH --gres=gpu:h200nvl:4
#SBATCH --time=100:30:00
#SBATCH --ntasks=1
#SBATCH --mem=250G
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

# Load user environment (important for scratch paths, etc.)
source ~/.bashrc

module purge
module load cuda/12.2
nvcc --version

# Fix for Triton CUDA header path issue
export CUDA_HOME=/uufs/chpc.utah.edu/sys/installdir/r8/cuda/12.2.0
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
export CPATH=$CUDA_HOME/include:$CPATH
export LIBRARY_PATH=$CUDA_HOME/lib64:$LIBRARY_PATH

# Load conda
source ~/miniconda3/etc/profile.d/conda.sh
conda activate py311

# Debug: check Python and packages
echo "Python path: $(which python)"
echo "Python version: $(python --version)"
python -c "import omegaconf; print('Omegaconf version:', omegaconf.__version__)"

# Run your script
python /uufs/chpc.utah.edu/common/home/u1582606/LM_exploration/Blicket_deepseek/run_blicket.py