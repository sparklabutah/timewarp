#!/usr/bin/env bash
# Copies SoM screenshots from TimeWarp-SoM into TimeWarpTrainingTrajectories.
#
# Source layout:  TimeWarp-SoM/som_output_versionX/<task>/*.png
# Dest layout:    TimeWarpTrainingTrajectories/version_X/<task>/SoM/*.png

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOM_ROOT="${SCRIPT_DIR}/TimeWarp-SoM"
TRAJ_ROOT="${SCRIPT_DIR}/TimeTraj-Trajectories"

if [[ ! -d "$SOM_ROOT" ]]; then
    echo "ERROR: SoM root not found: $SOM_ROOT" >&2
    exit 1
fi
if [[ ! -d "$TRAJ_ROOT" ]]; then
    echo "ERROR: Trajectory root not found: $TRAJ_ROOT" >&2
    exit 1
fi

total_copied=0
total_missing_task=0

for som_ver_dir in "$SOM_ROOT"/som_output_version*/; do
    [[ -d "$som_ver_dir" ]] || continue

    # Extract version number from "som_output_versionX"
    ver_basename="$(basename "$som_ver_dir")"          # e.g. som_output_version1
    ver_num="${ver_basename#som_output_version}"        # e.g. 1

    traj_ver_dir="${TRAJ_ROOT}/version_${ver_num}"

    if [[ ! -d "$traj_ver_dir" ]]; then
        echo "WARNING: No matching trajectory folder for $ver_basename (expected $traj_ver_dir) — skipping."
        continue
    fi

    echo "Processing version $ver_num ..."

    for task_dir in "$som_ver_dir"*/; do
        [[ -d "$task_dir" ]] || continue
        task_name="$(basename "$task_dir")"

        dest_task_dir="${traj_ver_dir}/${task_name}"
        if [[ ! -d "$dest_task_dir" ]]; then
            echo "  WARNING: Task not found in trajectories: $task_name — skipping."
            (( total_missing_task++ )) || true
            continue
        fi

        dest_som_dir="${dest_task_dir}/SoM"
        mkdir -p "$dest_som_dir"

        shopt -s nullglob
        images=("$task_dir"*.png)
        shopt -u nullglob

        if [[ ${#images[@]} -eq 0 ]]; then
            echo "  WARNING: No PNG files in $task_dir — skipping."
            continue
        fi

        for img in "${images[@]}"; do
            img_name="$(basename "$img")"
            dest_img="${dest_som_dir}/${img_name}"
            cp "$img" "$dest_img"
            (( total_copied++ )) || true
        done
    done
done

echo ""
echo "Done."
echo "  Files copied  : $total_copied"
echo "  Tasks missing in trajectories: $total_missing_task"
